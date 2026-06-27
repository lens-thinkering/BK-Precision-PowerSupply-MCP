"""Load and query the BK Precision model capability registry."""

from __future__ import annotations

import json
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent / "models" / "registry.json"
_registry: dict | None = None


def _load() -> dict:
    global _registry
    if _registry is None:
        with open(_REGISTRY_PATH, encoding="utf-8") as f:
            _registry = json.load(f)
    return _registry


def get_model_profile(model_id: str) -> dict:
    """Return the capability profile for *model_id*.

    Raises KeyError with a helpful message listing known models if not found.
    """
    models = _load()["models"]
    if model_id not in models:
        known = ", ".join(sorted(models))
        raise KeyError(
            f"Unknown model '{model_id}'. Supported models: {known}. "
            "Call bk_get_supported_models() for a full capability table."
        )
    profile = dict(models[model_id])
    profile["model_id"] = model_id
    return profile


def list_models() -> list[dict]:
    """Return a list of all model profiles, each with 'model_id' added."""
    models = _load()["models"]
    return [{"model_id": mid, **profile} for mid, profile in models.items()]


def find_model_by_idn(idn_response: str) -> str | None:
    """Attempt to match a *IDN? response to a known model ID.

    Returns the model_id string if found, None otherwise.
    BK Precision IDN format: 'B&K Precision,<model>,<serial>,<fw>'
    """
    idn_upper = idn_response.upper()
    for model_id in _load()["models"]:
        if model_id.upper() in idn_upper:
            return model_id
    return None
