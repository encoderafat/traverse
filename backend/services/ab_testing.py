import hashlib
from typing import List


def select_variant(user_id: str, experiment: str, variants: List[str]) -> str:
    """
    Deterministically pick a variant based on user_id + experiment name.
    """
    if not variants:
        raise ValueError("variants must be non-empty")
    key = f"{experiment}:{user_id}".encode("utf-8")
    digest = hashlib.md5(key).hexdigest()
    bucket = int(digest[:8], 16)
    return variants[bucket % len(variants)]
