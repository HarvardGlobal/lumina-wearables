"""Configuration for a separately deployed Open Wearables instance."""

from dataclasses import dataclass
import os


class OpenWearablesConfigurationError(ValueError):
    """Raised before a request when Open Wearables has not been configured."""


class WearablesExportConfigurationError(ValueError):
    """Raised when the protected PRomop export route has not been configured."""


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


@dataclass(frozen=True)
class WearablesExportSettings:
    """Configuration for the protected LUMINA Wearables -> PRomop bridge."""

    promop_base_url: str
    promop_service_token: str
    export_token: str
    timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "WearablesExportSettings":
        base_url = os.environ.get("PROMOP_BASE_URL", "").strip().rstrip("/")
        service_token = os.environ.get("PROMOP_SERVICE_AUTH_TOKEN", "").strip()
        export_token = os.environ.get("LUMINA_WEARABLES_EXPORT_TOKEN", "").strip()
        if not base_url:
            raise WearablesExportConfigurationError("PROMOP_BASE_URL must be set")
        if not service_token:
            raise WearablesExportConfigurationError("PROMOP_SERVICE_AUTH_TOKEN must be set")
        if not export_token:
            raise WearablesExportConfigurationError("LUMINA_WEARABLES_EXPORT_TOKEN must be set")
        try:
            timeout = float(os.environ.get("PROMOP_REQUEST_TIMEOUT_SECONDS", "30"))
        except ValueError as error:
            raise WearablesExportConfigurationError(
                "PROMOP_REQUEST_TIMEOUT_SECONDS must be a positive number"
            ) from error
        if timeout <= 0:
            raise WearablesExportConfigurationError("PROMOP_REQUEST_TIMEOUT_SECONDS must be positive")
        return cls(base_url, service_token, export_token, timeout)
