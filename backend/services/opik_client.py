# services/opik_client.py

import os
from typing import Any, Dict, Optional

from opik import Opik

OPIK_ENABLED = os.getenv("OPIK_ENABLED", "true").lower() == "true"


def create_opik_tracer(
    *,
    name: str,
    project_name: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Opik]:
    """
    Create a configured Opik tracer.
    Returns None if Opik is disabled.
    """
    if not OPIK_ENABLED:
        return None

    return Opik(
        project_name=project_name,
    )
