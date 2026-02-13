from app.core.artifacts.diff_engine import compute_diff


def test_diff_added_field() -> None:
    old = {"name": "Acme"}
    new = {"name": "Acme", "stage": "seed"}
    result = compute_diff(old, new)
    assert "dictionary_item_added" in result
    assert any("stage" in str(v) for v in result.values())


def test_diff_changed_value() -> None:
    old = {"name": "Acme", "stage": "seed"}
    new = {"name": "Acme", "stage": "series_a"}
    result = compute_diff(old, new)
    assert "values_changed" in result


def test_diff_removed_field() -> None:
    old = {"name": "Acme", "stage": "seed"}
    new = {"name": "Acme"}
    result = compute_diff(old, new)
    assert "dictionary_item_removed" in result


def test_diff_nested_change() -> None:
    old = {"company": {"name": "Acme", "employees": 10}}
    new = {"company": {"name": "Acme", "employees": 25}}
    result = compute_diff(old, new)
    assert "values_changed" in result
    assert any("employees" in str(k) for k in result.get("values_changed", {}))


def test_diff_identical() -> None:
    content = {"name": "Acme", "stage": "seed", "metrics": [1, 2, 3]}
    result = compute_diff(content, content)
    assert result == {}
