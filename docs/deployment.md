# Deployment

Run vikunja-mcp with Docker behind Caddy (automatic HTTPS).

Replace `mcp.example.com`, `vikunja-demo.example.com`, `user@server.example.com` and `~/vikunja-mcp` with your own values.

## Overview

- `compose.yml`: the MCP server plus Caddy (`Caddyfile`, serves only `/mcp`). Works with any Vikunja set in `VIKUNJA_URL`.
- `compose.demo.yml`: goes on top and adds a throwaway demo Vikunja with fake data. It uses `Caddyfile.demo`, which also serves the demo web UI on its own domain.

## Requirements

- Debian or Ubuntu with Docker and the Compose plugin.
- Ports 80/tcp, 443/tcp and 443/udp open.
- DNS records (DNS only, not proxied) pointing to the server: the MCP domain, plus the demo domain if you run the demo.

## Copy the files

`rsync` must be installed on both machines.

```bash
rsync -av \
  --exclude .git --exclude .venv --exclude .env \
  --exclude dev-data --exclude data \
  --exclude .pytest_cache --exclude .ruff_cache --exclude __pycache__ \
  ./ user@server.example.com:~/vikunja-mcp/
```

Everything else is copied, so check for untracked files first.

## Create the .env on the server

In `~/vikunja-mcp`:

```bash
umask 077
cat > .env <<EOF
COMPOSE_FILE=compose.yml:compose.demo.yml
MCP_DOMAIN=mcp.example.com
ALLOWED_HOSTS='["mcp.example.com"]'
MCP_AUTH_TOKEN=$(openssl rand -hex 32)
VIKUNJA_URL=http://vikunja-demo:3456
VIKUNJA_API_TOKEN=pending
DEMO_VIKUNJA_DOMAIN=vikunja-demo.example.com
DEMO_VIKUNJA_SECRET=$(openssl rand -hex 32)
EOF
```

- `COMPOSE_FILE` saves you the `-f` flags. Without the demo, drop it and the `DEMO_` lines, and point `VIKUNJA_URL` and `VIKUNJA_API_TOKEN` at your own Vikunja.
- `VIKUNJA_API_TOKEN=pending` is a placeholder so Compose starts. You create the real token once the demo is running (see below).
- `ALLOWED_HOSTS` must be the exact public domain, without a port.

## Start

The demo Vikunja runs as uid 1000 and must own its data folder.

```bash
mkdir -p data/vikunja
sudo chown 1000:1000 data/vikunja
docker compose up --build -d
docker compose ps
```

All containers should be `running` and the MCP server `healthy`. To check the certificates, look for `certificate obtained successfully` for each domain:

```bash
docker compose logs caddy | grep -i certificate
```

## Create the demo user and token

Registration is off, so create the user from the CLI. It asks for the password.

```bash
docker compose exec vikunja-demo /app/vikunja/vikunja user create --username demo --email demo@example.com
```

Log in at `https://vikunja-demo.example.com` and create an API token (Settings → API tokens) with access to projects and tasks. Then put it in the `.env` without echoing it or saving it to shell history:

```bash
read -rs TOKEN
sed -i "s|^VIKUNJA_API_TOKEN=.*|VIKUNJA_API_TOKEN=$TOKEN|" .env
unset TOKEN
docker compose up -d
```

## Verify

```bash
read -rs MCP_AUTH_TOKEN   # paste the value from .env

curl -i https://mcp.example.com/health                                          # 404, not exposed
curl -i -X POST https://mcp.example.com/mcp                                     # 401
curl -i -X POST https://mcp.example.com/mcp -H "Authorization: Bearer wrong"    # 401

# returns the projects, including Inbox
curl -s https://mcp.example.com/mcp \
  -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}'
```

Connect Claude Code using `MCP_AUTH_TOKEN`, not the Vikunja API token:

```bash
claude mcp add --transport http vikunja https://mcp.example.com/mcp --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

## Update and restart

Run the same rsync again, then on the server:

```bash
docker compose up --build -d
```

Data is kept across restarts and rebuilds: the demo database is in `data/vikunja`, and Caddy's certificates are in the `caddy_data` and `caddy_config` volumes. To back up the demo data:

```bash
tar czf vikunja-backup-$(date +%F).tar.gz data/vikunja
```

## Troubleshooting

**401 from a client.** Wrong token: usually the Vikunja token instead of `MCP_AUTH_TOKEN`, or a stale value. Check with `grep MCP_AUTH_TOKEN .env` and add the client again.

**421 Invalid Host header.** `ALLOWED_HOSTS` must be the exact domain without a port. Run `docker compose up -d` after changing it.

**No certificate.** The DNS record is wrong or proxied, or ports 80/443 are blocked. Check `docker compose logs caddy`.

**Works on a phone but not on one computer.** That computer resolves the name differently, for example through Tailscale split DNS. Compare:

```bash
dig +short mcp.example.com @1.1.1.1
getent hosts mcp.example.com
```

**Container restarts in a loop.** Check `docker compose logs <service>`. A missing or invalid variable stops the server, and a wrong owner on `data/vikunja` stops the demo Vikunja.
