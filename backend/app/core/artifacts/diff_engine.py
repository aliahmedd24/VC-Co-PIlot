"""Diff engine for computing and applying diffs between artifact versions."""

from typing import Any


class DiffEngine:
    """Engine for computing structured diffs between JSONB artifact content."""

    @staticmethod
    def compute_diff(
        old_content: dict[str, Any],
        new_content: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compute a structured diff between two artifact content versions.

        Returns a diff object with:
        - added: keys/values added in new_content
        - removed: keys/values removed from old_content
        - modified: keys with changed values (showing old and new)
        - unchanged: count of unchanged keys
        """
        diff: dict[str, Any] = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged_count": 0,
        }

        all_keys = set(old_content.keys()) | set(new_content.keys())

        for key in all_keys:
            old_val = old_content.get(key)
            new_val = new_content.get(key)

            if key not in old_content:
                diff["added"][key] = new_val
            elif key not in new_content:
                diff["removed"][key] = old_val
            elif old_val != new_val:
                # Recursively diff nested dicts
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    nested_diff = DiffEngine.compute_diff(old_val, new_val)
                    if DiffEngine._has_changes(nested_diff):
                        diff["modified"][key] = nested_diff
                    else:
                        diff["unchanged_count"] += 1
                else:
                    diff["modified"][key] = {"old": old_val, "new": new_val}
            else:
                diff["unchanged_count"] += 1

        return diff

    @staticmethod
    def _has_changes(diff: dict[str, Any]) -> bool:
        """Check if a diff contains any actual changes."""
        return bool(diff.get("added") or diff.get("removed") or diff.get("modified"))

    @staticmethod
    def apply_diff(
        base_content: dict[str, Any],
        diff: dict[str, Any],
        reverse: bool = False,
    ) -> dict[str, Any]:
        """
        Apply a diff to base content to reconstruct another version.

        Args:
            base_content: The content to apply the diff to
            diff: The diff object from compute_diff
            reverse: If True, reverse the diff (go from new to old)

        Returns:
            The reconstructed content
        """
        result = dict(base_content)

        if reverse:
            # Reverse: remove added, add removed, swap modified
            for key in diff.get("added", {}):
                result.pop(key, None)
            for key, val in diff.get("removed", {}).items():
                result[key] = val
            for key, change in diff.get("modified", {}).items():
                if "old" in change and "new" in change:
                    result[key] = change["old"]
                elif isinstance(change, dict) and DiffEngine._has_changes(change):
                    # Nested diff
                    if key in result and isinstance(result[key], dict):
                        result[key] = DiffEngine.apply_diff(result[key], change, reverse=True)
        else:
            # Forward: add added, remove removed, apply modified
            for key, val in diff.get("added", {}).items():
                result[key] = val
            for key in diff.get("removed", {}):
                result.pop(key, None)
            for key, change in diff.get("modified", {}).items():
                if "old" in change and "new" in change:
                    result[key] = change["new"]
                elif isinstance(change, dict) and DiffEngine._has_changes(change):
                    # Nested diff
                    if key in result and isinstance(result[key], dict):
                        result[key] = DiffEngine.apply_diff(result[key], change, reverse=False)

        return result

    @staticmethod
    def summarize_changes(diff: dict[str, Any]) -> str:
        """
        Generate a human-readable summary of changes.

        Returns a string describing what changed.
        """
        parts = []

        added_count = len(diff.get("added", {}))
        removed_count = len(diff.get("removed", {}))
        modified_count = len(diff.get("modified", {}))

        if added_count:
            keys = ", ".join(list(diff["added"].keys())[:3])
            if added_count > 3:
                keys += f" (+{added_count - 3} more)"
            parts.append(f"Added: {keys}")

        if removed_count:
            keys = ", ".join(list(diff["removed"].keys())[:3])
            if removed_count > 3:
                keys += f" (+{removed_count - 3} more)"
            parts.append(f"Removed: {keys}")

        if modified_count:
            keys = ", ".join(list(diff["modified"].keys())[:3])
            if modified_count > 3:
                keys += f" (+{modified_count - 3} more)"
            parts.append(f"Modified: {keys}")

        if not parts:
            return "No changes"

        return "; ".join(parts)
