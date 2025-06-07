"""Enhanced base provider class with common functionality extracted from all providers."""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp

from ..core.exceptions import (
    AuthenticationError,
    BudgetExceededError,
    GenerationError,
    RateLimitError,
)
from .provider import Provider
from .types import GenerationRequest, GenerationResponse, GenerationType


class BaseProvider(Provider):
    """Enhanced base provider with common functionality.
    
    This class extends the abstract Provider class with common patterns
    found across all provider implementations.
    """
    
    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize base provider.
        
        Args:
            name: Provider name
            api_key: Optional API key (will check env vars if not provided)
            config: Optional configuration dictionary
        """
        super().__init__(name, api_key, config)
        self._session: Optional[aiohttp.ClientSession] = None
    
    # ===== API Key Management =====
    
    def _get_api_key(self, env_var_name: str) -> str:
        """Get API key from init parameter or environment variable.
        
        Args:
            env_var_name: Name of environment variable to check
            
        Returns:
            API key string
            
        Raises:
            ValueError: If no API key found
        """
        if self.api_key:
            return self.api_key
        
        api_key = os.getenv(env_var_name)
        if not api_key:
            raise ValueError(
                f"{self.name} API key is required. "
                f"Set {env_var_name} environment variable or pass api_key parameter."
            )
        return api_key
    
    # ===== Session Management =====
    
    async def _create_session(self, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientSession:
        """Create an aiohttp session with common headers.
        
        Args:
            headers: Optional additional headers
            
        Returns:
            Configured aiohttp session
        """
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": f"AliceMultiverse/{self.name}"
        }
        if headers:
            default_headers.update(headers)
        return aiohttp.ClientSession(headers=default_headers)
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure session exists, create if needed.
        
        Returns:
            Active aiohttp session
        """
        if not self._session:
            self._session = await self._create_session(self._get_headers())
        return self._session
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get provider-specific headers.
        
        Returns:
            Dictionary of headers including authentication
        """
        pass
    
    # ===== HTTP Error Handling =====
    
    async def _handle_response_errors(
        self,
        response: aiohttp.ClientResponse,
        context: str = ""
    ) -> None:
        """Handle common HTTP error responses.
        
        Args:
            response: aiohttp response object
            context: Optional context for error messages
            
        Raises:
            Various exceptions based on status code
        """
        if response.status == 200:
            return
        
        try:
            error_text = await response.text()
        except Exception:
            error_text = f"Status {response.status}"
        
        error_prefix = f"{context}: " if context else ""
        
        if response.status == 401:
            raise AuthenticationError(self.name, f"{error_prefix}Authentication failed: {error_text}")
        elif response.status == 429:
            retry_after = response.headers.get('Retry-After', 'unknown')
            raise RateLimitError(f"{error_prefix}Rate limit exceeded. Retry after: {retry_after}")
        elif response.status == 402:
            raise BudgetExceededError(f"{error_prefix}Payment required: {error_text}")
        elif response.status >= 500:
            raise GenerationError(f"{error_prefix}Server error ({response.status}): {error_text}")
        elif response.status >= 400:
            raise GenerationError(f"{error_prefix}Client error ({response.status}): {error_text}")
    
    # ===== Parameter Handling =====
    
    def _extract_common_params(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common parameters that most providers use.
        
        Args:
            parameters: Input parameters dictionary
            
        Returns:
            Dictionary of common parameters
        """
        if not parameters:
            return {}
        
        common = {}
        
        # Common image parameters
        image_params = [
            'width', 'height', 'seed', 'num_images', 'negative_prompt',
            'guidance_scale', 'num_inference_steps', 'sampler'
        ]
        for key in image_params:
            if key in parameters:
                common[key] = parameters[key]
        
        # Common video parameters
        video_params = [
            'duration', 'fps', 'aspect_ratio', 'motion_strength',
            'camera_motion', 'video_model'
        ]
        for key in video_params:
            if key in parameters:
                common[key] = parameters[key]
        
        # Common audio parameters
        audio_params = [
            'voice', 'language', 'speed', 'pitch', 'emotion',
            'sample_rate', 'format'
        ]
        for key in audio_params:
            if key in parameters:
                common[key] = parameters[key]
        
        return common
    
    # ===== File Operations =====
    
    async def _download_result(
        self,
        url: str,
        output_dir: Path,
        filename: Optional[str] = None
    ) -> Path:
        """Download generated content from URL.
        
        Args:
            url: URL to download from
            output_dir: Directory to save to
            filename: Optional filename override
            
        Returns:
            Path to downloaded file
        """
        from ..core.file_operations import download_file
        return await download_file(url, output_dir, filename)
    
    # ===== Polling Helpers =====
    
    async def _poll_for_completion(
        self, 
        check_func: Callable[[], Awaitable[Tuple[bool, Any]]], 
        poll_interval: float = 5.0,
        max_wait: float = 300.0,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Any:
        """Poll for async job completion.
        
        Args:
            check_func: Async function that returns (is_complete, result)
            poll_interval: Seconds between polls
            max_wait: Maximum seconds to wait
            progress_callback: Optional callback for progress updates
            
        Returns:
            The result when complete
            
        Raises:
            GenerationError: If max wait time exceeded
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            is_complete, result = await check_func()
            
            if is_complete:
                return result
                
            if progress_callback:
                elapsed = time.time() - start_time
                progress = min(elapsed / max_wait, 0.95)  # Cap at 95%
                progress_callback(progress)
                
            await asyncio.sleep(poll_interval)
        
        raise GenerationError(f"Generation timed out after {max_wait} seconds")
    
    # ===== Model Validation =====
    
    def _validate_model(self, model: Optional[str], generation_type: GenerationType) -> str:
        """Validate and resolve model name.
        
        Args:
            model: Model name to validate
            generation_type: Type of generation
            
        Returns:
            Validated model name
            
        Raises:
            ValueError: If model not supported
        """
        if not model:
            return self.get_default_model(generation_type)
        
        # Check if model is supported
        if model not in self.capabilities.models:
            # Try case-insensitive match
            model_lower = model.lower()
            for supported in self.capabilities.models:
                if supported.lower() == model_lower:
                    return supported
            
            # Try removing provider prefix if present
            if model.startswith(f"{self.name.lower()}/"):
                base_model = model[len(self.name) + 1:]
                return self._validate_model(base_model, generation_type)
            
            # No match found
            raise ValueError(
                f"Model '{model}' not supported by {self.name}. "
                f"Available models: {', '.join(self.capabilities.models)}"
            )
        
        return model
    
    # ===== Model Alias Resolution =====
    
    def _resolve_model_alias(
        self,
        model: str,
        aliases: Dict[str, str]
    ) -> str:
        """Resolve model name using alias dictionary.
        
        Args:
            model: Model name or alias
            aliases: Dictionary of aliases to actual model names
            
        Returns:
            Resolved model name
        """
        # Direct match
        if model in aliases:
            return aliases[model]
        
        # Case-insensitive match
        model_lower = model.lower()
        for alias, actual in aliases.items():
            if alias.lower() == model_lower:
                return actual
        
        # Return original if no alias found
        return model
    
    # ===== Cost Calculation Helpers =====
    
    def _calculate_cost_with_modifiers(
        self,
        base_cost: float,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None,
        resolution_multiplier: float = 1.0,
        duration_multiplier: float = 1.0
    ) -> float:
        """Calculate cost with resolution/duration modifiers.
        
        Args:
            base_cost: Base cost for the model
            width: Image/video width
            height: Image/video height
            duration: Video duration in seconds
            resolution_multiplier: Multiplier per megapixel
            duration_multiplier: Multiplier per second
            
        Returns:
            Total cost
        """
        cost = base_cost
        
        # Apply resolution modifier
        if width and height:
            megapixels = (width * height) / 1_000_000
            if megapixels > 1.0:  # Only apply for > 1MP
                cost *= (1 + (megapixels - 1) * resolution_multiplier)
        
        # Apply duration modifier
        if duration and duration > 1.0:
            cost *= (1 + (duration - 1) * duration_multiplier)
        
        return cost
    
    # ===== Context Manager =====
    
    async def __aenter__(self):
        """Enter async context."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        if self._session:
            await self._session.close()
            self._session = None
    
    # ===== Request Building Helpers =====
    
    def _build_base_request(
        self,
        request: GenerationRequest,
        endpoint: str,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Build base request configuration.
        
        Args:
            request: Generation request
            endpoint: API endpoint
            method: HTTP method
            
        Returns:
            Dictionary with url, method, and base payload
        """
        return {
            "url": endpoint,
            "method": method,
            "payload": {
                "prompt": request.prompt,
                **self._extract_common_params(request.parameters)
            }
        }
    
    # ===== Response Parsing Helpers =====
    
    def _parse_error_response(self, response_data: Dict[str, Any]) -> str:
        """Parse error message from response data.
        
        Args:
            response_data: Response JSON data
            
        Returns:
            Error message string
        """
        # Common error field names
        error_fields = ['error', 'message', 'detail', 'error_message', 'errors']
        
        for field in error_fields:
            if field in response_data:
                error_value = response_data[field]
                if isinstance(error_value, str):
                    return error_value
                elif isinstance(error_value, dict):
                    # Nested error object
                    return self._parse_error_response(error_value)
                elif isinstance(error_value, list) and error_value:
                    # List of errors
                    return str(error_value[0])
        
        return "Unknown error"
    
    # ===== Retry Logic =====
    
    async def _retry_with_backoff(
        self,
        func: Callable[[], Awaitable[Any]],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ) -> Any:
        """Retry a function with exponential backoff.
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            
        Returns:
            Result from successful function call
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except (RateLimitError, aiohttp.ClientError) as e:
                last_exception = e
                
                if attempt >= max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    base_delay * (exponential_base ** attempt),
                    max_delay
                )
                
                self.logger.warning(
                    f"{self.name} request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception or GenerationError("All retry attempts failed")