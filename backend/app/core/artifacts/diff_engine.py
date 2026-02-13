import json
from typing import Any

from deepdiff import DeepDiff


def compute_diff(
    old_content: dict[str, Any], new_content: dict[str, Any]
) -> dict[str, Any]:
    """Compute a JSON-serializable diff between two content dicts.

    Uses deepdiff to detect structural changes (added/removed/changed fields).
    Returns an empty dict if the contents are identical.
    """
    dd = DeepDiff(old_content, new_content, ignore_order=True)
    if not dd:
        return {}
    raw: dict[str, Any] = json.loads(dd.to_json())
    return raw
