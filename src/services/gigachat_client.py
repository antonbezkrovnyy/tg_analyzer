"""GigaChat API client with OAuth authentication."""

import asyncio
import logging
import time
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from pydantic import ValidationError

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from src.core.config import settings
from src.core.exceptions import (
    GigaChatAPIError,
    GigaChatAuthError,
    GigaChatRateLimitError,
    GigaChatTimeoutError,
)
from src.models.gigachat import (
    GigaChatCompletionRequest,
    GigaChatCompletionResponse,
    GigaChatMessage,
    GigaChatModelsResponse,
    GigaChatOAuthResponse,
)

logger = logging.getLogger(__name__)


class GigaChatClient:
    """Client for GigaChat API with OAuth authentication and retry logic."""

    def __init__(
        self,
        auth_key: str | None = None,
        oauth_url: str | None = None,
        base_url: str | None = None,
        scope: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        """Initialize GigaChat client.

        Args:
            auth_key: Authorization key (base64 encoded Client ID:Client Secret)
            oauth_url: OAuth endpoint URL
            base_url: API base URL
            scope: OAuth scope
            timeout: HTTP request timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (exponential backoff)
        """
        self._auth_key = auth_key or settings.gigachat_auth_key.get_secret_value()
        self._oauth_url = oauth_url or str(settings.gigachat_oauth_url)
        self._base_url = (base_url or str(settings.gigachat_base_url)).rstrip("/")
        self._scope = scope or settings.gigachat_scope
        self._timeout = timeout or settings.http_timeout
        self._max_retries = max_retries or settings.max_retries
        self._retry_delay = retry_delay or settings.retry_delay

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "GigaChatClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            verify=False,  # SSL verification disabled (GigaChat uses self-signed cert)
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _get_access_token(self) -> str:
        """Get access token, refresh if expired.

        Returns:
            Valid access token

        Raises:
            GigaChatAuthError: If authentication fails
        """
        # Check if token is still valid
        if self._access_token and self._token_expires_at:
            # Refresh if less than 5 minutes remaining
            if datetime.now() + timedelta(minutes=5) < self._token_expires_at:
                logger.debug("Using existing access token")
                return self._access_token

        logger.info("Requesting new access token from GigaChat")

        if not self._client:
            raise GigaChatAuthError("HTTP client not initialized")

        # Generate unique request ID
        rq_uid = str(uuid.uuid4())

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self._auth_key}",
        }

        data = {"scope": self._scope}

        try:
            response = await self._client.post(
                self._oauth_url,
                headers=headers,
                data=data,
            )

            if response.status_code == 401:
                raise GigaChatAuthError("Invalid authorization key")

            response.raise_for_status()

            oauth_response = GigaChatOAuthResponse.model_validate(response.json())

            self._access_token = oauth_response.access_token
            # Token expires_at is unix timestamp in milliseconds
            self._token_expires_at = datetime.fromtimestamp(
                oauth_response.expires_at / 1000
            )

            logger.info(f"Access token obtained, expires at {self._token_expires_at}")

            return self._access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth request failed: {e}")
            raise GigaChatAuthError(f"OAuth request failed: {e.response.text}")
        except ValidationError as e:
            logger.error(f"Invalid OAuth response: {e}")
            raise GigaChatAuthError(f"Invalid OAuth response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during OAuth: {e}")
            raise GigaChatAuthError(f"Unexpected error: {e}")

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            GigaChatAPIError: If request fails after all retries
            GigaChatRateLimitError: If rate limit exceeded
            GigaChatTimeoutError: If request times out
        """
        if not self._client:
            raise GigaChatAPIError("HTTP client not initialized")

        # Ensure we have valid access token
        access_token = await self._get_access_token()

        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
        )

        url = f"{self._base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self._max_retries):
            try:
                logger.debug(
                    f"Request attempt {attempt + 1}/{self._max_retries}: {method} {url}"
                )

                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limit exceeded, retry after {retry_after}s")

                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise GigaChatRateLimitError(
                            retry_after=retry_after,
                        )

                # Handle server errors (5xx) - retry
                if 500 <= response.status_code < 600:
                    logger.warning(f"Server error {response.status_code}, retrying...")

                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (
                            2**attempt
                        )  # Exponential backoff
                        await asyncio.sleep(delay)
                        continue
                    else:
                        response.raise_for_status()

                # Raise for other HTTP errors
                response.raise_for_status()

                return response

            except httpx.TimeoutException as e:
                logger.error(f"Request timeout: {e}")
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise GigaChatTimeoutError()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                raise GigaChatAPIError(
                    message=str(e),
                    status_code=e.response.status_code,
                )

        raise GigaChatAPIError("Max retries exceeded")

    async def get_models(self) -> GigaChatModelsResponse:
        """Get list of available models.

        Returns:
            List of available models

        Raises:
            GigaChatAPIError: If request fails
        """
        logger.info("Fetching available GigaChat models")

        response = await self._request_with_retry("GET", "/models")

        try:
            models_response = GigaChatModelsResponse.model_validate(response.json())
            logger.info(f"Found {len(models_response.data)} models")
            return models_response
        except ValidationError as e:
            logger.error(f"Invalid models response: {e}")
            raise GigaChatAPIError(f"Invalid response: {e}")

    async def complete(
        self,
        messages: list[GigaChatMessage] | list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> GigaChatCompletionResponse:
        """Send chat completion request to GigaChat.

        Args:
            messages: List of messages in conversation
            model: Model to use (default from settings)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Completion response from GigaChat

        Raises:
            GigaChatAPIError: If request fails
        """
        # Convert dict messages to GigaChatMessage if needed
        if messages and isinstance(messages[0], dict):
            messages = [GigaChatMessage(**msg) for msg in messages]

        request_model = GigaChatCompletionRequest(
            model=model or settings.gigachat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"Sending completion request: model={request_model.model}, "
            f"messages={len(request_model.messages)}, "
            f"temperature={temperature}"
        )

        start_time = time.time()

        response = await self._request_with_retry(
            "POST",
            "/chat/completions",
            json=request_model.model_dump(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

        latency = time.time() - start_time

        try:
            completion_response = GigaChatCompletionResponse.model_validate(
                response.json()
            )

            logger.info(
                f"Completion received: tokens={completion_response.usage.total_tokens}, "
                f"latency={latency:.2f}s"
            )

            return completion_response

        except ValidationError as e:
            logger.error(f"Invalid completion response: {e}")
            raise GigaChatAPIError(f"Invalid response: {e}")
