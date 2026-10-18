import importlib
import pkgutil

import pytest

import vikunja_mcp.tools as tools_package


def feature_names() -> list[str]:
    return [m.name for m in pkgutil.iter_modules(tools_package.__path__) if m.ispkg]


def test_the_known_features_are_found():
    assert {"tasks", "projects"} <= set(feature_names())


@pytest.mark.parametrize("feature", feature_names())
def test_feature_exports_only_register(feature):
    package = importlib.import_module(f"vikunja_mcp.tools.{feature}")

    assert package.__all__ == ["register"]
    assert callable(package.register)


@pytest.mark.parametrize("feature", feature_names())
def test_feature_keeps_its_tools_in_a_tools_module(feature):
    module = importlib.import_module(f"vikunja_mcp.tools.{feature}.tools")

    assert callable(module.register)
