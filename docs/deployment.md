# Deployment

Run vikunja-mcp with Docker behind Caddy (automatic HTTPS).

Replace `mcp.example.com`, `vikunja-demo.example.com`, `your-name.authkit.app`, `user@server.example.com` and `~/vikunja-mcp` with your own values.

## Overview

- `compose.yml`: the MCP server plus Caddy (`Caddyfile`, serves only `/mcp` and the `/.well-known/oauth-protected-resource` paths). Works with any Vikunja set in `VIKUNJA_URL`.
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

Log in at `https://vikunja-demo.example.com` and create an API token (Settings, API tokens) with access to projects and tasks. Then put it in the `.env` without echoing it or saving it to shell history:

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

With OAuth on (see below), also check the metadata. The first command returns JSON with `resource` and `authorization_servers`. The second shows a `www-authenticate` header that contains `resource_metadata`:

```bash
curl -s https://mcp.example.com/.well-known/oauth-protected-resource/mcp
curl -si -X POST https://mcp.example.com/mcp | grep -i www-authenticate
```

Connect Claude Code using `MCP_AUTH_TOKEN`, not the Vikunja API token:

```bash
claude mcp add --transport http vikunja https://mcp.example.com/mcp --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```

### OAuth with WorkOS AuthKit

OAuth lets the Claude website connect with a login instead of a fixed token. The static token keeps working next to it.

#### Identity provider setup

In the WorkOS dashboard, create a staging environment and note its AuthKit domain, for example `https://your-name.authkit.app`. Under Connect configuration, enable Client ID Metadata Document and Dynamic Client Registration. Add the MCP URL, for example `https://mcp.example.com/mcp`, as a Resource Indicator and set it as the default.

#### Server settings

Add the three variables to the `.env` on the server and recreate the containers:

```bash
cat >> .env <<'EOF'
OAUTH_ISSUER=https://your-name.authkit.app
PUBLIC_URL=https://mcp.example.com/mcp
OAUTH_ALLOWED_SUBJECTS='[]'
EOF
docker compose up -d
```

`PUBLIC_URL` must match the Resource Indicator exactly, because it is the audience checked in every token.

#### First login

On the Claude website, add the connector with the MCP URL and log in. The first attempt is rejected with 403, because the allowlist is still empty. The server log shows your user id:

```bash
docker compose logs vikunja-mcp | grep "Rejected a valid token from a subject that is not allowed"
```

Put that id into `OAUTH_ALLOWED_SUBJECTS` in the `.env` as a JSON list, for example `OAUTH_ALLOWED_SUBJECTS='["user_01EXAMPLE"]'`, run `docker compose up -d`, and reconnect the connector.

#### Keeping the secrets out

No WorkOS API keys or client secrets go on the server. It only needs the public issuer address and the MCP URL, and it fetches the public signing keys from the issuer on its own.

## Update and restart

Run the same rsync again, then on the server:

```bash
docker compose up --build -d
```

If the `Caddyfile` changed, also run `docker compose restart caddy` (see Troubleshooting).

Data is kept across restarts and rebuilds: the demo database is in `data/vikunja`, and Caddy's certificates are in the `caddy_data` and `caddy_config` volumes. To back up the demo data:

```bash
tar czf vikunja-backup-$(date +%F).tar.gz data/vikunja
```

## Troubleshooting

**401 from a client.** Wrong token: usually the Vikunja token instead of `MCP_AUTH_TOKEN`, or a stale value. Check with `grep MCP_AUTH_TOKEN .env` and add the client again.

**401 with a `www-authenticate` header on a curl test without a token.** This is normal. It tells OAuth clients where to find the metadata.

**403 from the Claude website.** The token is valid, but the user id is not in `OAUTH_ALLOWED_SUBJECTS`.

**"Audience doesn't match" in the log.** The Resource Indicator is missing in the identity provider or differs from `PUBLIC_URL`. Fix it in the dashboard, then remove the connector and add it again.

**421 Invalid Host header.** `ALLOWED_HOSTS` must be the exact domain without a port. Run `docker compose up -d` after changing it.

**No certificate.** The DNS record is wrong or proxied, or ports 80/443 are blocked. Check `docker compose logs caddy`.

**TLS "internal error" for a domain.** Caddy has no site block for that domain. Check the Caddyfile in use for it.

**Caddy still uses the old Caddyfile.** rsync replaces the file, and a single-file mount keeps showing the old one to the container. Run `docker compose restart caddy`.

**Works on a phone but not on one computer.** That computer resolves the name differently, for example through Tailscale split DNS. Compare:

```bash
dig +short mcp.example.com @1.1.1.1
getent hosts mcp.example.com
```

**Container restarts in a loop.** Check `docker compose logs <service>`. A missing or invalid variable stops the server, and a wrong owner on `data/vikunja` stops the demo Vikunja.
