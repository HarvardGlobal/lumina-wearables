"""Configuration for a separately deployed Open Wearables instance."""

from dataclasses import dataclass
import os


class OpenWearablesConfigurationError(ValueError):
    """Raised before a request when Open Wearables has not been configured."""


@dataclass(frozen=True)
class OpenWearablesSettings:
    """Non-secret connection settings for the Open Wearables external API."""

    base_url: str
    api_key: str
    timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "OpenWearablesSettings":
        base_url = os.environ.get("OPEN_WEARABLES_BASE_URL", "").strip().rstrip("/")
        api_key = os.environ.get("OPEN_WEARABLES_API_KEY", "").strip()
        if not base_url:
            raise OpenWearablesConfigurationError(
                "OPEN_WEARABLES_BASE_URL must be set to the Open Wearables API base URL"
            )
        if not api_key:
            raise OpenWearablesConfigurationError("OPEN_WEARABLES_API_KEY must be set")
        return cls(base_url=base_url, api_key=api_key)
