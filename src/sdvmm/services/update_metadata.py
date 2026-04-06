from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
import json
import os
import re
import time
from html import unescape
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sdvmm.domain.models import (
    InstalledMod,
    ModUpdateReport,
    ModUpdateStatus,
    ModsInventory,
    NexusIntegrationStatus,
    RemoteModLink,
    RemoteMetadataCacheEntry,
    RemoteMetadataPayloadCache,
    UpdateCheckDiagnostics,
    UpdateSourceIntentOverlay,
    UpdateSourceIntentRecord,
)
from sdvmm.domain.unique_id import canonicalize_unique_id
from sdvmm.domain.nexus_codes import (
    NEXUS_CONFIGURED,
    NEXUS_INVALID_AUTH_FAILURE,
    NEXUS_NOT_CONFIGURED,
    NEXUS_WORKING_VALIDATED,
)
from sdvmm.domain.remote_requirement_codes import (
    NO_REMOTE_LINK_FOR_REQUIREMENTS,
    REQUIREMENTS_ABSENT,
    REQUIREMENTS_PRESENT,
    REQUIREMENTS_UNAVAILABLE,
)
from sdvmm.domain.update_codes import (
    GITHUB_PROVIDER,
    JSON_PROVIDER,
    LOCAL_PRIVATE_MOD,
    METADATA_UNAVAILABLE,
    METADATA_SOURCE_ISSUE,
    MISSING_UPDATE_KEY,
    NEXUS_PROVIDER,
    NO_REMOTE_LINK,
    NO_PROVIDER_MAPPING,
    REMOTE_METADATA_LOOKUP_FAILED,
    UNSUPPORTED_UPDATE_KEY_FORMAT,
    UPDATE_AVAILABLE,
    UP_TO_DATE,
)

NEXUS_API_KEY_ENV = "SDVMM_NEXUS_API_KEY"
NEXUS_VALIDATE_URL = "https://api.nexusmods.com/v1/users/validate.json"

MALFORMED_UPDATE_KEY = "malformed_update_key"
MISSING_API_KEY = "missing_api_key"
AUTH_FAILURE = "auth_failure"
REQUEST_FAILURE = "request_failure"
RESPONSE_MISSING_VERSION = "response_missing_version"
UNEXPECTED_PROVIDER_RESPONSE = "unexpected_provider_response"
UNSUPPORTED_PROVIDER = "unsupported_provider"
INCOMPLETE_MANUAL_SOURCE_ASSOCIATION = "incomplete_manual_source_association"
DEFAULT_REMOTE_METADATA_CACHE_FRESHNESS_SECONDS = 900.0
DEFAULT_REMOTE_METADATA_PREFETCH_WORKERS = 6


class MetadataFetchError(ValueError):
    """Raised when remote metadata cannot be retrieved or parsed."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


class JsonMetadataFetcher(Protocol):
    def fetch_json(
        self,
        url: str,
        timeout_seconds: float,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Fetch JSON from a remote URL."""


class UrllibJsonMetadataFetcher:
    def fetch_json(
        self,
        url: str,
        timeout_seconds: float,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        request_headers: dict[str, str] = {
            "User-Agent": "sdvmm/0.1 (+local metadata check)",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update({str(key): str(value) for key, value in headers.items()})

        request = Request(url, headers=request_headers)

        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            body_message = _extract_http_error_message(exc)
            reason = AUTH_FAILURE if exc.code in {401, 403} else REQUEST_FAILURE
            message = f"HTTP {exc.code}: {body_message or exc.reason or 'request failed'}"
            raise MetadataFetchError(reason, message) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise MetadataFetchError(REQUEST_FAILURE, str(exc)) from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise MetadataFetchError(
                UNEXPECTED_PROVIDER_RESPONSE,
                f"Invalid metadata JSON: {exc}",
            ) from exc

        if not isinstance(data, dict):
            raise MetadataFetchError(
                UNEXPECTED_PROVIDER_RESPONSE,
                "Metadata payload must be a JSON object",
            )

        return data


class MetadataProviderAdapter(Protocol):
    provider: str

    def build_link(self, raw_value: str) -> RemoteModLink | None:
        """Build a provider-specific remote link from UpdateKeys value."""

    def fetch_payload(
        self,
        link: RemoteModLink,
        *,
        fetcher: JsonMetadataFetcher,
        timeout_seconds: float,
        nexus_api_key: str | None = None,
    ) -> dict[str, Any]:
        """Load provider metadata payload for a resolved link."""

    def extract_version(self, payload: Mapping[str, Any]) -> str | None:
        """Extract a comparable remote version from provider payload."""

    def extract_page_url(self, payload: Mapping[str, Any]) -> str | None:
        """Extract a user-facing remote page URL from provider payload, if present."""

    def extract_requirements(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        """Extract source-declared remote requirements, if available."""


class JsonProviderAdapter:
    provider = JSON_PROVIDER

    def build_link(self, raw_value: str) -> RemoteModLink | None:
        url = raw_value.strip()
        if not _looks_like_url(url):
            return None

        return RemoteModLink(
            provider=JSON_PROVIDER,
            key=url,
            page_url=url,
            metadata_url=url,
        )

    def fetch_payload(
        self,
        link: RemoteModLink,
        *,
        fetcher: JsonMetadataFetcher,
        timeout_seconds: float,
        nexus_api_key: str | None = None,
    ) -> dict[str, Any]:
        _ = nexus_api_key
        if not link.metadata_url:
            raise MetadataFetchError(UNEXPECTED_PROVIDER_RESPONSE, "JSON provider has no metadata URL")
        return fetcher.fetch_json(link.metadata_url, timeout_seconds)

    def extract_version(self, payload: Mapping[str, Any]) -> str | None:
        return _extract_generic_version(payload)

    def extract_page_url(self, payload: Mapping[str, Any]) -> str | None:
        return _extract_generic_page_url(payload)

    def extract_requirements(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        return _extract_generic_requirements(payload)


class GithubProviderAdapter:
    provider = GITHUB_PROVIDER

    def build_link(self, raw_value: str) -> RemoteModLink | None:
        repo = raw_value.strip()
        if not _looks_like_repo_slug(repo):
            return None

        return RemoteModLink(
            provider=GITHUB_PROVIDER,
            key=repo,
            page_url=f"https://github.com/{repo}",
            metadata_url=f"https://api.github.com/repos/{repo}/releases/latest",
        )

    def fetch_payload(
        self,
        link: RemoteModLink,
        *,
        fetcher: JsonMetadataFetcher,
        timeout_seconds: float,
        nexus_api_key: str | None = None,
    ) -> dict[str, Any]:
        _ = nexus_api_key
        if not link.metadata_url:
            raise MetadataFetchError(UNEXPECTED_PROVIDER_RESPONSE, "GitHub provider has no metadata URL")
        return fetcher.fetch_json(link.metadata_url, timeout_seconds)

    def extract_version(self, payload: Mapping[str, Any]) -> str | None:
        tag_name = payload.get("tag_name")
        if isinstance(tag_name, str) and tag_name.strip():
            stripped = tag_name.strip()
            if stripped.startswith(("v", "V")) and len(stripped) > 1 and stripped[1].isdigit():
                return stripped[1:]
            return stripped

        return _extract_generic_version(payload)

    def extract_page_url(self, payload: Mapping[str, Any]) -> str | None:
        return _extract_generic_page_url(payload)

    def extract_requirements(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        return _extract_generic_requirements(payload)


class NexusProviderAdapter:
    provider = NEXUS_PROVIDER

    def build_link(self, raw_value: str) -> RemoteModLink | None:
        parsed = _parse_nexus_key(raw_value)
        if parsed is None:
            return None

        game_domain, mod_id = parsed
        return RemoteModLink(
            provider=NEXUS_PROVIDER,
            key=f"{game_domain}:{mod_id}",
            page_url=f"https://www.nexusmods.com/{game_domain}/mods/{mod_id}",
            metadata_url=f"https://api.nexusmods.com/v1/games/{game_domain}/mods/{mod_id}.json",
        )

    def fetch_payload(
        self,
        link: RemoteModLink,
        *,
        fetcher: JsonMetadataFetcher,
        timeout_seconds: float,
        nexus_api_key: str | None = None,
    ) -> dict[str, Any]:
        if not link.metadata_url:
            raise MetadataFetchError(UNEXPECTED_PROVIDER_RESPONSE, "Nexus provider has no metadata URL")

        api_key = normalize_nexus_api_key(nexus_api_key)
        if not api_key:
            api_key = normalize_nexus_api_key(os.getenv(NEXUS_API_KEY_ENV, ""))
        if not api_key:
            raise MetadataFetchError(
                MISSING_API_KEY,
                (
                    f"Nexus metadata requires a configured API key (saved key preferred; env fallback: {NEXUS_API_KEY_ENV})."
                ),
            )

        return fetcher.fetch_json(
            link.metadata_url,
            timeout_seconds,
            headers={
                "apikey": api_key,
            },
        )

    def extract_version(self, payload: Mapping[str, Any]) -> str | None:
        for key in ("version", "mod_version"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return _extract_generic_version(payload)

    def extract_page_url(self, payload: Mapping[str, Any]) -> str | None:
        value = payload.get("url")
        if isinstance(value, str) and _looks_like_url(value) and "nexusmods.com" in value.casefold():
            return value.strip()
        return None

    def extract_requirements(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        # Nexus payloads vary by endpoint/version; parse common requirement shapes conservatively.
        for key in ("requirements", "mod_requirements", "dependencies", "requires"):
            extracted = _extract_requirement_items(payload.get(key))
            if extracted:
                return extracted
        return tuple()


@dataclass(frozen=True, slots=True)
class LinkResolutionIssue:
    provider: str
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    provider: str
    reason: str
    message: str


_PROVIDER_PRIORITY = (JSON_PROVIDER, GITHUB_PROVIDER, NEXUS_PROVIDER)
_PROVIDER_ADAPTERS: tuple[MetadataProviderAdapter, ...] = (
    JsonProviderAdapter(),
    GithubProviderAdapter(),
    NexusProviderAdapter(),
)
_PROVIDERS_BY_NAME = {adapter.provider: adapter for adapter in _PROVIDER_ADAPTERS}
_RemotePayloadCacheKey = tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class _CachedRemotePayload:
    payload: dict[str, Any]
    fetched_at_epoch_seconds: float
    source: str


@dataclass(slots=True)
class _UpdateCheckDiagnosticsAccumulator:
    mod_count: int = 0
    remote_links_resolved: int = 0
    unique_remote_targets: int = 0
    live_fetches: int = 0
    in_run_cache_hits: int = 0
    persisted_cache_hits: int = 0
    cached_failure_hits: int = 0
    seen_remote_targets: set[_RemotePayloadCacheKey] = field(default_factory=set)

    def note_remote_target(self, cache_key: _RemotePayloadCacheKey) -> None:
        if cache_key in self.seen_remote_targets:
            return
        self.seen_remote_targets.add(cache_key)
        self.unique_remote_targets += 1


_RemotePayloadCacheValue = _CachedRemotePayload | MetadataFetchError


@dataclass(frozen=True, slots=True)
class _ResolvedModUpdateCheck:
    mod: InstalledMod
    links: tuple[RemoteModLink, ...]
    resolution_issues: tuple[LinkResolutionIssue, ...]


def check_updates_for_inventory(
    inventory: ModsInventory,
    *,
    fetcher: JsonMetadataFetcher | None = None,
    timeout_seconds: float = 8.0,
    nexus_api_key: str | None = None,
    update_source_intent_overlay: UpdateSourceIntentOverlay | None = None,
) -> ModUpdateReport:
    report, _ = check_updates_for_inventory_with_cache(
        inventory,
        fetcher=fetcher,
        timeout_seconds=timeout_seconds,
        nexus_api_key=nexus_api_key,
        update_source_intent_overlay=update_source_intent_overlay,
    )
    return report


def check_updates_for_inventory_with_cache(
    inventory: ModsInventory,
    *,
    fetcher: JsonMetadataFetcher | None = None,
    timeout_seconds: float = 8.0,
    nexus_api_key: str | None = None,
    update_source_intent_overlay: UpdateSourceIntentOverlay | None = None,
    persisted_remote_metadata_cache: RemoteMetadataPayloadCache | None = None,
    freshness_window_seconds: float = DEFAULT_REMOTE_METADATA_CACHE_FRESHNESS_SECONDS,
    now_epoch_seconds: float | None = None,
) -> tuple[ModUpdateReport, RemoteMetadataPayloadCache]:
    started_at = time.perf_counter()
    active_fetcher = fetcher or UrllibJsonMetadataFetcher()
    overlay_by_unique_id = _overlay_records_by_unique_id(update_source_intent_overlay)
    resolved_now = time.time() if now_epoch_seconds is None else now_epoch_seconds
    remote_payload_cache = _seed_remote_payload_cache(
        persisted_remote_metadata_cache=persisted_remote_metadata_cache,
        freshness_window_seconds=freshness_window_seconds,
        now_epoch_seconds=resolved_now,
    )
    diagnostics = _UpdateCheckDiagnosticsAccumulator(mod_count=len(inventory.mods))
    resolved_checks = tuple(
        _resolve_mod_update_check(
            mod,
            overlay_by_unique_id.get(canonicalize_unique_id(mod.unique_id)),
        )
        for mod in inventory.mods
    )
    prefetched_remote_payloads = _prefetch_primary_remote_payloads(
        resolved_checks=resolved_checks,
        fetcher=active_fetcher,
        timeout_seconds=timeout_seconds,
        nexus_api_key=nexus_api_key,
        cache_write_epoch_seconds=resolved_now,
        remote_payload_cache=remote_payload_cache,
        diagnostics=diagnostics,
    )

    statuses: list[ModUpdateStatus] = []
    for resolved_check in resolved_checks:
        statuses.append(
            _check_single_mod(
                mod=resolved_check.mod,
                links=resolved_check.links,
                resolution_issues=resolved_check.resolution_issues,
                fetcher=active_fetcher,
                timeout_seconds=timeout_seconds,
                nexus_api_key=nexus_api_key,
                cache_write_epoch_seconds=resolved_now,
                remote_payload_cache=remote_payload_cache,
                prefetched_remote_payloads=prefetched_remote_payloads,
                diagnostics=diagnostics,
            )
        )

    statuses.sort(key=lambda status: (status.name.casefold(), status.folder_path.name.casefold()))
    diagnostics_report = UpdateCheckDiagnostics(
        mod_count=diagnostics.mod_count,
        remote_links_resolved=diagnostics.remote_links_resolved,
        unique_remote_targets=diagnostics.unique_remote_targets,
        live_fetches=diagnostics.live_fetches,
        in_run_cache_hits=diagnostics.in_run_cache_hits,
        persisted_cache_hits=diagnostics.persisted_cache_hits,
        cached_failure_hits=diagnostics.cached_failure_hits,
        duration_ms=(time.perf_counter() - started_at) * 1000.0,
    )
    return (
        ModUpdateReport(statuses=tuple(statuses), diagnostics=diagnostics_report),
        _build_persisted_remote_metadata_cache(remote_payload_cache),
    )


def check_nexus_connection(
    *,
    nexus_api_key: str | None,
    fetcher: JsonMetadataFetcher | None = None,
    timeout_seconds: float = 8.0,
) -> NexusIntegrationStatus:
    normalized = normalize_nexus_api_key(nexus_api_key)
    if not normalized:
        return NexusIntegrationStatus(
            state=NEXUS_NOT_CONFIGURED,
            source="none",
            masked_key=None,
            message="Nexus API key is not configured.",
        )

    active_fetcher = fetcher or UrllibJsonMetadataFetcher()
    try:
        payload = active_fetcher.fetch_json(
            NEXUS_VALIDATE_URL,
            timeout_seconds,
            headers={"apikey": normalized},
        )
    except MetadataFetchError as exc:
        if exc.reason == AUTH_FAILURE:
            return NexusIntegrationStatus(
                state=NEXUS_INVALID_AUTH_FAILURE,
                source="entered",
                masked_key=mask_api_key(normalized),
                message=f"[{AUTH_FAILURE}] {exc.message}",
            )
        return NexusIntegrationStatus(
            state=NEXUS_CONFIGURED,
            source="entered",
            masked_key=mask_api_key(normalized),
            message=f"[{exc.reason}] Could not validate Nexus key right now: {exc.message}",
        )

    user_name = payload.get("name")
    user_suffix = f" (user: {user_name})" if isinstance(user_name, str) and user_name.strip() else ""
    return NexusIntegrationStatus(
        state=NEXUS_WORKING_VALIDATED,
        source="entered",
        masked_key=mask_api_key(normalized),
        message=f"Nexus key validated successfully{user_suffix}.",
    )


def compare_versions(installed_version: str, remote_version: str) -> int | None:
    left = _tokenize_version(installed_version)
    right = _tokenize_version(remote_version)

    if not left or not right:
        return None

    max_len = max(len(left), len(right))
    for idx in range(max_len):
        left_token = left[idx] if idx < len(left) else 0
        right_token = right[idx] if idx < len(right) else 0

        if left_token == right_token:
            continue

        left_key = _token_key(left_token)
        right_key = _token_key(right_token)
        if left_key < right_key:
            return -1
        return 1

    return 0


def resolve_remote_link(update_keys: tuple[str, ...]) -> RemoteModLink | None:
    candidates, _ = resolve_remote_link_candidates(update_keys)
    if not candidates:
        return None
    return candidates[0]


def resolve_remote_link_candidates(
    update_keys: tuple[str, ...],
) -> tuple[tuple[RemoteModLink, ...], tuple[LinkResolutionIssue, ...]]:
    candidates: list[RemoteModLink] = []
    issues: list[LinkResolutionIssue] = []

    for raw_key in update_keys:
        provider, value = _parse_update_key(raw_key)
        if provider is None:
            continue

        adapter = _PROVIDERS_BY_NAME.get(provider)
        if adapter is None:
            issues.append(
                LinkResolutionIssue(
                    provider=provider,
                    reason=UNSUPPORTED_PROVIDER,
                    message=f"UpdateKey provider '{provider}' is not mapped to a supported metadata adapter.",
                )
            )
            continue

        link = adapter.build_link(value)
        if link is not None:
            candidates.append(link)
            continue

        issues.append(
            LinkResolutionIssue(
                provider=provider,
                reason=MALFORMED_UPDATE_KEY,
                message=f"Unsupported {provider} UpdateKey format: {raw_key}",
            )
        )

    ordered: list[RemoteModLink] = []
    for provider_name in _PROVIDER_PRIORITY:
        ordered.extend(link for link in candidates if link.provider == provider_name)

    return tuple(ordered), tuple(issues)


def _check_single_mod(
    mod: InstalledMod,
    *,
    links: tuple[RemoteModLink, ...],
    resolution_issues: tuple[LinkResolutionIssue, ...],
    fetcher: JsonMetadataFetcher,
    timeout_seconds: float,
    nexus_api_key: str | None,
    cache_write_epoch_seconds: float,
    remote_payload_cache: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
    prefetched_remote_payloads: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
    diagnostics: _UpdateCheckDiagnosticsAccumulator,
) -> ModUpdateStatus:
    base_status = ModUpdateStatus(
        unique_id=mod.unique_id,
        name=mod.name,
        folder_path=mod.folder_path,
        installed_version=mod.version,
        remote_version=None,
        state=NO_REMOTE_LINK,
        remote_link=links[0] if links else None,
        update_source_diagnostic=None,
        message=None,
        remote_requirements_state=NO_REMOTE_LINK_FOR_REQUIREMENTS,
        remote_requirements=tuple(),
        remote_requirements_message="No remote link is available for requirement guidance.",
    )

    if not links:
        if resolution_issues:
            issue = resolution_issues[0]
            diagnostic_code = _diagnostic_code_for_resolution_issue(issue)
            message = _message_for_resolution_issue(issue)
            if diagnostic_code == LOCAL_PRIVATE_MOD:
                return replace(
                    base_status,
                    update_source_diagnostic=diagnostic_code,
                    message=message,
                    remote_requirements_message=message,
                )
            return replace(
                base_status,
                state=METADATA_UNAVAILABLE,
                update_source_diagnostic=diagnostic_code,
                message=message,
                remote_requirements_state=REQUIREMENTS_UNAVAILABLE,
                remote_requirements_message=message,
            )
        return replace(base_status, update_source_diagnostic=MISSING_UPDATE_KEY)

    diagnostics.remote_links_resolved += len(links)
    failures: list[ProviderFailure] = []
    best_requirements_state = REQUIREMENTS_UNAVAILABLE
    best_requirements: tuple[str, ...] = tuple()
    best_requirements_message: str | None = None
    best_link = links[0]

    for link in links:
        provider = _PROVIDERS_BY_NAME.get(link.provider)
        if provider is None:
            failures.append(
                ProviderFailure(
                    provider=link.provider,
                    reason=UNSUPPORTED_PROVIDER,
                    message=f"Provider '{link.provider}' is not supported.",
                )
            )
            continue

        try:
            payload = _fetch_payload_with_cache(
                provider=provider,
                link=link,
                fetcher=fetcher,
                timeout_seconds=timeout_seconds,
                nexus_api_key=nexus_api_key,
                cache_write_epoch_seconds=cache_write_epoch_seconds,
                remote_payload_cache=remote_payload_cache,
                prefetched_remote_payloads=prefetched_remote_payloads,
                diagnostics=diagnostics,
            )
        except MetadataFetchError as exc:
            failures.append(
                ProviderFailure(
                    provider=link.provider,
                    reason=exc.reason,
                    message=exc.message,
                )
            )
            continue

        page_url = provider.extract_page_url(payload)
        if page_url:
            link = replace(link, page_url=page_url)

        remote_requirements = provider.extract_requirements(payload)
        if remote_requirements:
            remote_requirements_state = REQUIREMENTS_PRESENT
            remote_requirements_message = "Remote source declares additional requirements."
        else:
            remote_requirements_state = REQUIREMENTS_ABSENT
            remote_requirements_message = "Remote source does not declare explicit requirements."
        best_requirements_state = remote_requirements_state
        best_requirements = remote_requirements
        best_requirements_message = remote_requirements_message
        best_link = link

        remote_version = provider.extract_version(payload)
        if remote_version is None:
            failures.append(
                ProviderFailure(
                    provider=link.provider,
                    reason=RESPONSE_MISSING_VERSION,
                    message="Remote metadata does not provide a usable version field.",
                )
            )
            continue

        comparison = compare_versions(mod.version, remote_version)
        if comparison is None:
            failures.append(
                ProviderFailure(
                    provider=link.provider,
                    reason=UNEXPECTED_PROVIDER_RESPONSE,
                    message="Installed or remote version format is not comparable.",
                )
            )
            continue

        if comparison < 0:
            return replace(
                base_status,
                state=UPDATE_AVAILABLE,
                remote_link=link,
                remote_version=remote_version,
                message="Remote version is newer than installed version.",
                remote_requirements_state=remote_requirements_state,
                remote_requirements=remote_requirements,
                remote_requirements_message=remote_requirements_message,
            )

        return replace(
            base_status,
            state=UP_TO_DATE,
            remote_link=link,
            remote_version=remote_version,
            message="Installed version is up to date.",
            remote_requirements_state=remote_requirements_state,
            remote_requirements=remote_requirements,
            remote_requirements_message=remote_requirements_message,
        )

    fallback_link = links[0]
    message = _summarize_failures(failures)
    return replace(
        base_status,
        state=METADATA_UNAVAILABLE,
        remote_link=best_link or fallback_link,
        update_source_diagnostic=_diagnostic_code_for_failures(failures),
        message=message,
        remote_requirements_state=best_requirements_state,
        remote_requirements=best_requirements,
        remote_requirements_message=best_requirements_message or message,
    )


def _fetch_payload_with_cache(
    *,
    provider: MetadataProviderAdapter,
    link: RemoteModLink,
    fetcher: JsonMetadataFetcher,
    timeout_seconds: float,
    nexus_api_key: str | None,
    cache_write_epoch_seconds: float,
    remote_payload_cache: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
    prefetched_remote_payloads: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
    diagnostics: _UpdateCheckDiagnosticsAccumulator,
) -> dict[str, Any]:
    cache_key = _remote_payload_cache_key(link, nexus_api_key)
    diagnostics.note_remote_target(cache_key)
    prefetched = prefetched_remote_payloads.pop(cache_key, None)
    if prefetched is not None:
        remote_payload_cache[cache_key] = prefetched
        if isinstance(prefetched, MetadataFetchError):
            raise MetadataFetchError(prefetched.reason, prefetched.message)
        return prefetched.payload
    cached = remote_payload_cache.get(cache_key)
    if cached is not None:
        if isinstance(cached, MetadataFetchError):
            diagnostics.cached_failure_hits += 1
            raise MetadataFetchError(cached.reason, cached.message)
        if cached.source == "persisted":
            diagnostics.persisted_cache_hits += 1
        else:
            diagnostics.in_run_cache_hits += 1
        return cached.payload

    diagnostics.live_fetches += 1
    try:
        payload = provider.fetch_payload(
            link,
            fetcher=fetcher,
            timeout_seconds=timeout_seconds,
            nexus_api_key=nexus_api_key,
        )
    except MetadataFetchError as exc:
        remote_payload_cache[cache_key] = MetadataFetchError(exc.reason, exc.message)
        raise

    remote_payload_cache[cache_key] = _CachedRemotePayload(
        payload=payload,
        fetched_at_epoch_seconds=cache_write_epoch_seconds,
        source="live",
    )
    return payload


def _remote_payload_cache_key(
    link: RemoteModLink,
    nexus_api_key: str | None,
) -> _RemotePayloadCacheKey:
    metadata_target = (link.metadata_url or link.page_url or link.key).strip()
    auth_marker = ""
    if link.provider == NEXUS_PROVIDER:
        auth_marker = normalize_nexus_api_key(nexus_api_key) or normalize_nexus_api_key(
            os.getenv(NEXUS_API_KEY_ENV, "")
        )
    return (link.provider, metadata_target, "authenticated" if auth_marker else "")


def _seed_remote_payload_cache(
    *,
    persisted_remote_metadata_cache: RemoteMetadataPayloadCache | None,
    freshness_window_seconds: float,
    now_epoch_seconds: float,
) -> dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue]:
    seeded: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue] = {}
    if persisted_remote_metadata_cache is None:
        return seeded

    for entry in persisted_remote_metadata_cache.entries:
        age_seconds = now_epoch_seconds - entry.fetched_at_epoch_seconds
        if age_seconds < 0:
            age_seconds = 0
        if age_seconds > freshness_window_seconds:
            continue
        seeded[(entry.provider, entry.metadata_target, entry.auth_scope)] = _CachedRemotePayload(
            payload=dict(entry.payload),
            fetched_at_epoch_seconds=entry.fetched_at_epoch_seconds,
            source="persisted",
        )
    return seeded


def _resolve_mod_update_check(
    mod: InstalledMod,
    update_source_intent: UpdateSourceIntentRecord | None,
) -> _ResolvedModUpdateCheck:
    manual_resolution = _resolve_manual_source_override(update_source_intent)
    if manual_resolution is None:
        links, resolution_issues = resolve_remote_link_candidates(mod.update_keys)
    else:
        links = manual_resolution.links
        resolution_issues = manual_resolution.issues
    return _ResolvedModUpdateCheck(
        mod=mod,
        links=links,
        resolution_issues=resolution_issues,
    )


def _prefetch_primary_remote_payloads(
    *,
    resolved_checks: tuple[_ResolvedModUpdateCheck, ...],
    fetcher: JsonMetadataFetcher,
    timeout_seconds: float,
    nexus_api_key: str | None,
    cache_write_epoch_seconds: float,
    remote_payload_cache: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
    diagnostics: _UpdateCheckDiagnosticsAccumulator,
) -> dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue]:
    requests: dict[_RemotePayloadCacheKey, tuple[MetadataProviderAdapter, RemoteModLink]] = {}
    for resolved_check in resolved_checks:
        if not resolved_check.links:
            continue
        link = resolved_check.links[0]
        cache_key = _remote_payload_cache_key(link, nexus_api_key)
        diagnostics.note_remote_target(cache_key)
        if cache_key in remote_payload_cache or cache_key in requests:
            continue
        provider = _PROVIDERS_BY_NAME.get(link.provider)
        if provider is None:
            continue
        requests[cache_key] = (provider, link)

    if len(requests) < 2:
        return {}

    max_workers = min(DEFAULT_REMOTE_METADATA_PREFETCH_WORKERS, len(requests))
    prefetched: dict[_RemotePayloadCacheKey, _RemotePayloadCacheValue] = {}
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sdvmm-update") as executor:
        future_to_cache_key = {}
        for cache_key, (provider, link) in requests.items():
            diagnostics.live_fetches += 1
            future_to_cache_key[
                executor.submit(
                    _fetch_remote_payload_for_prefetch,
                    provider=provider,
                    link=link,
                    fetcher=fetcher,
                    timeout_seconds=timeout_seconds,
                    nexus_api_key=nexus_api_key,
                    cache_write_epoch_seconds=cache_write_epoch_seconds,
                )
            ] = cache_key

        for future in as_completed(future_to_cache_key):
            cache_key = future_to_cache_key[future]
            try:
                prefetched[cache_key] = future.result()
            except MetadataFetchError as exc:
                prefetched[cache_key] = MetadataFetchError(exc.reason, exc.message)

    return prefetched


def _fetch_remote_payload_for_prefetch(
    *,
    provider: MetadataProviderAdapter,
    link: RemoteModLink,
    fetcher: JsonMetadataFetcher,
    timeout_seconds: float,
    nexus_api_key: str | None,
    cache_write_epoch_seconds: float,
) -> _CachedRemotePayload:
    payload = provider.fetch_payload(
        link,
        fetcher=fetcher,
        timeout_seconds=timeout_seconds,
        nexus_api_key=nexus_api_key,
    )
    return _CachedRemotePayload(
        payload=payload,
        fetched_at_epoch_seconds=cache_write_epoch_seconds,
        source="live",
    )


def _build_persisted_remote_metadata_cache(
    remote_payload_cache: Mapping[_RemotePayloadCacheKey, _RemotePayloadCacheValue],
) -> RemoteMetadataPayloadCache:
    entries: list[RemoteMetadataCacheEntry] = []
    for (provider, metadata_target, auth_scope), cached in remote_payload_cache.items():
        if isinstance(cached, MetadataFetchError):
            continue
        entries.append(
            RemoteMetadataCacheEntry(
                provider=provider,
                metadata_target=metadata_target,
                auth_scope=auth_scope,
                fetched_at_epoch_seconds=cached.fetched_at_epoch_seconds,
                payload=dict(cached.payload),
            )
        )
    entries.sort(key=lambda entry: (entry.provider, entry.metadata_target, entry.auth_scope))
    return RemoteMetadataPayloadCache(entries=tuple(entries))


def _parse_update_key(raw_key: str) -> tuple[str | None, str]:
    if ":" not in raw_key:
        return None, ""

    prefix, value = raw_key.split(":", 1)
    provider = prefix.strip().casefold()
    return provider, value.strip()


def _parse_nexus_key(raw_value: str) -> tuple[str, str] | None:
    value = raw_value.strip()
    if not value:
        return None

    if "@" in value:
        value = value.split("@", 1)[0].strip()
        if not value:
            return None

    if value.isdigit():
        return "stardewvalley", value

    match = re.fullmatch(r"([a-z0-9][a-z0-9_-]*):(\d+)", value.casefold())
    if match is not None:
        game_domain, mod_id = match.groups()
        return game_domain, mod_id

    url_match = re.fullmatch(
        r"https?://(?:www\.)?nexusmods\.com/([a-z0-9][a-z0-9_-]*)/mods/(\d+)(?:[/?#].*)?",
        value.casefold(),
    )
    if url_match is not None:
        game_domain, mod_id = url_match.groups()
        return game_domain, mod_id

    return None


def _looks_like_repo_slug(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value.strip()) is not None


def _tokenize_version(version: str) -> list[int | str]:
    chunks = [chunk for chunk in re.split(r"[^0-9A-Za-z]+", version.strip()) if chunk]
    tokens: list[int | str] = []
    for chunk in chunks:
        if chunk.isdigit():
            tokens.append(int(chunk))
        else:
            tokens.append(chunk.casefold())

    return tokens


def _token_key(value: int | str) -> tuple[int, int | str]:
    if isinstance(value, int):
        return (0, value)
    return (1, value)


def _extract_generic_version(payload: Mapping[str, Any]) -> str | None:
    for key in ("version", "Version", "latest_version", "latestVersion"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _extract_generic_requirements(payload: Mapping[str, Any]) -> tuple[str, ...]:
    for key in ("requirements", "Dependencies", "dependencies", "requires"):
        extracted = _extract_requirement_items(payload.get(key))
        if extracted:
            return extracted
    return tuple()


def _extract_requirement_items(value: object) -> tuple[str, ...]:
    if value is None:
        return tuple()

    if isinstance(value, str):
        return _split_requirement_text(value)

    if isinstance(value, Mapping):
        items: list[str] = []
        for nested_key in ("name", "display_name", "description", "requirement", "value"):
            nested = value.get(nested_key)
            if isinstance(nested, str):
                items.extend(_split_requirement_text(nested))
        if not items:
            for nested_value in value.values():
                items.extend(_extract_requirement_items(nested_value))
        return _dedupe_requirement_items(items)

    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_extract_requirement_items(item))
        return _dedupe_requirement_items(items)

    return tuple()


def _split_requirement_text(raw_text: str) -> tuple[str, ...]:
    text = unescape(raw_text.strip())
    if not text:
        return tuple()

    text = re.sub(r"<[^>]+>", " ", text)
    chunks = re.split(r"[\n\r;,]+", text)
    items = [chunk.strip(" -*\t") for chunk in chunks if chunk.strip(" -*\t")]
    return _dedupe_requirement_items(items)


def _dedupe_requirement_items(items: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    deduped: dict[str, str] = {}
    for raw_item in items:
        item = str(raw_item).strip()
        if not item:
            continue
        key = item.casefold()
        if key not in deduped:
            deduped[key] = item

    return tuple(sorted(deduped.values(), key=str.casefold))


def _extract_generic_page_url(payload: Mapping[str, Any]) -> str | None:
    for key in ("html_url", "page_url", "url"):
        value = payload.get(key)
        if isinstance(value, str) and _looks_like_url(value):
            return value.strip()
    return None


def _looks_like_url(value: str) -> bool:
    lowered = value.strip().casefold()
    return lowered.startswith("https://") or lowered.startswith("http://")


def _extract_http_error_message(exc: HTTPError) -> str | None:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    if not body.strip():
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()[:240]

    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    return body.strip()[:240]


def normalize_nexus_api_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def mask_api_key(value: str | None) -> str | None:
    normalized = normalize_nexus_api_key(value)
    if not normalized:
        return None
    if len(normalized) <= 8:
        return "*" * len(normalized)
    return f"{normalized[:4]}...{normalized[-4:]}"


def _summarize_failures(failures: list[ProviderFailure]) -> str:
    if not failures:
        return "[metadata_unavailable] Metadata provider could not resolve a usable version."

    shown = failures[:2]
    fragments = [
        f"[{failure.reason}] {failure.provider}: {failure.message}"
        for failure in shown
    ]
    if len(failures) > len(shown):
        fragments.append(f"... {len(failures) - len(shown)} more provider failure(s)")
    return "; ".join(fragments)


def _diagnostic_code_for_resolution_issue(issue: LinkResolutionIssue):
    if issue.reason == MALFORMED_UPDATE_KEY:
        return UNSUPPORTED_UPDATE_KEY_FORMAT
    if issue.reason == UNSUPPORTED_PROVIDER:
        if issue.provider in {"local", "private"}:
            return LOCAL_PRIVATE_MOD
        return NO_PROVIDER_MAPPING
    if issue.reason == INCOMPLETE_MANUAL_SOURCE_ASSOCIATION:
        return METADATA_SOURCE_ISSUE
    return METADATA_SOURCE_ISSUE


def _message_for_resolution_issue(issue: LinkResolutionIssue) -> str:
    if issue.reason == UNSUPPORTED_PROVIDER and issue.provider in {"local", "private"}:
        return "[local_private_mod] Mod declares a local/private update source; no public remote page is available."
    if issue.reason == UNSUPPORTED_PROVIDER:
        return f"[{UNSUPPORTED_PROVIDER}] No provider mapping for UpdateKey provider '{issue.provider}'."
    if issue.reason == INCOMPLETE_MANUAL_SOURCE_ASSOCIATION:
        return (
            f"[{INCOMPLETE_MANUAL_SOURCE_ASSOCIATION}] "
            "Saved manual source association is incomplete; provider and source key are required."
        )
    return f"[{issue.reason}] {issue.message}"


def _diagnostic_code_for_failures(failures: list[ProviderFailure]):
    if any(
        failure.reason in {AUTH_FAILURE, REQUEST_FAILURE, MISSING_API_KEY}
        for failure in failures
    ):
        return REMOTE_METADATA_LOOKUP_FAILED
    return METADATA_SOURCE_ISSUE


@dataclass(frozen=True, slots=True)
class ManualSourceOverrideResolution:
    links: tuple[RemoteModLink, ...]
    issues: tuple[LinkResolutionIssue, ...]


def _overlay_records_by_unique_id(
    overlay: UpdateSourceIntentOverlay | None,
) -> dict[str, UpdateSourceIntentRecord]:
    if overlay is None:
        return {}
    return {
        record.normalized_unique_id: record
        for record in overlay.records
    }


def _resolve_manual_source_override(
    update_source_intent: UpdateSourceIntentRecord | None,
) -> ManualSourceOverrideResolution | None:
    if update_source_intent is None or update_source_intent.intent_state != "manual_source_association":
        return None

    provider_name = (update_source_intent.manual_provider or "").strip().casefold()
    source_key = (update_source_intent.manual_source_key or "").strip()
    page_url = (update_source_intent.manual_source_page_url or "").strip()
    if not provider_name or not source_key:
        return ManualSourceOverrideResolution(
            links=tuple(),
            issues=(
                LinkResolutionIssue(
                    provider=provider_name or "<missing>",
                    reason=INCOMPLETE_MANUAL_SOURCE_ASSOCIATION,
                    message="Saved manual source association must include provider and source key.",
                ),
            ),
        )

    adapter = _PROVIDERS_BY_NAME.get(provider_name)
    if adapter is None:
        return ManualSourceOverrideResolution(
            links=tuple(),
            issues=(
                LinkResolutionIssue(
                    provider=provider_name,
                    reason=UNSUPPORTED_PROVIDER,
                    message=(
                        f"Saved manual source association provider '{provider_name}' "
                        "is not mapped to a supported metadata adapter."
                    ),
                ),
            ),
        )

    link = adapter.build_link(source_key)
    if link is None:
        return ManualSourceOverrideResolution(
            links=tuple(),
            issues=(
                LinkResolutionIssue(
                    provider=provider_name,
                    reason=MALFORMED_UPDATE_KEY,
                    message=(
                        f"Saved manual source association has unsupported {provider_name} "
                        f"source key format: {source_key}"
                    ),
                ),
            ),
        )

    if page_url and _looks_like_url(page_url):
        link = replace(link, page_url=page_url)
    return ManualSourceOverrideResolution(links=(link,), issues=tuple())
