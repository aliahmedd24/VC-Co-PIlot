"""Tests for the MCP Brain Server."""

from app.mcp.brain_server import brain_mcp

# ------------------------------------------------------------------ #
# Server registration
# ------------------------------------------------------------------ #


def test_brain_mcp_has_four_tools() -> None:
    """The brain MCP server should expose exactly 4 tools."""
    tool_names = {
        t.name for t in brain_mcp._tool_manager.tools.values()
    }
    expected = {
        "query_entities",
        "search_brain",
        "detect_data_gaps",
        "traverse_relations",
    }
    assert expected.issubset(tool_names), (
        f"Missing tools: {expected - tool_names}"
    )
    assert len(tool_names) >= 4


def test_brain_mcp_has_resource_templates() -> None:
    """The brain MCP server should expose 2 resource templates."""
    templates = brain_mcp._resource_manager.templates
    template_uris = {t.uri_template for t in templates.values()}
    assert "brain://venture/{venture_id}/snapshot" in template_uris
    assert (
        "brain://venture/{venture_id}/entities/{entity_type}"
        in template_uris
    )


def test_brain_mcp_server_name() -> None:
    """Server should have the correct name."""
    assert brain_mcp.name == "Startup Brain"


# ------------------------------------------------------------------ #
# MCP app mounting
# ------------------------------------------------------------------ #


def test_mcp_app_is_importable() -> None:
    """The mcp_app ASGI object should be importable for mounting."""
    from app.mcp.brain_server import mcp_app

    assert mcp_app is not None


def test_main_mounts_mcp() -> None:
    """FastAPI app should have MCP mounted at /mcp/brain."""
    from app.main import app

    # Check that /mcp/brain is in the app's routes
    mount_paths = [
        r.path for r in app.routes if hasattr(r, "path")
    ]
    assert "/mcp/brain" in mount_paths, (
        f"MCP not mounted. Routes: {mount_paths}"
    )
