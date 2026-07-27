from app.ai_catalog.factory import load_ai_catalog

_EXPECTED_TYPES = {"agent", "mcp_server", "api", "ai_model", "prompt_template", "skill", "connector"}


def test_ai_catalog_loads_all_asset_types():
    assets = load_ai_catalog()
    types = {a.asset_type for a in assets}
    assert types == _EXPECTED_TYPES
    assert len(assets) > 0


def test_every_asset_type_has_multiple_entries():
    assets = load_ai_catalog()
    counts: dict[str, int] = {}
    for asset in assets:
        counts[asset.asset_type] = counts.get(asset.asset_type, 0) + 1
    assert all(n >= 2 for n in counts.values())


def test_asset_ids_are_unique():
    assets = load_ai_catalog()
    ids = [a.id for a in assets]
    assert len(ids) == len(set(ids))


def test_every_asset_has_tags():
    assets = load_ai_catalog()
    assert all(len(a.tags) > 0 for a in assets)


def test_load_ai_catalog_is_cached():
    assert load_ai_catalog() is load_ai_catalog()
