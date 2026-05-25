import os
from typing import Generator, Optional, Dict, Any, List
from openai import OpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

from .exceptions import (
    ModelException,
    ModelTimeoutError,
    ModelRateLimitError,
    ModelAuthenticationError,
    ModelConnectionError,
)

load_dotenv()


class ChatService:
    api_key: str
    base_url: str
    model_name: str
    timeout: int
    max_retries: int
    _client: Optional[OpenAI] = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))
        self.max_retries = max_retries or int(os.getenv("LLM_MAX_RETRIES", "3"))

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _handle_error(self, error: Exception) -> None:
        if isinstance(error, APITimeoutError):
            raise ModelTimeoutError(f"请求超时: {error}")
        elif isinstance(error, RateLimitError):
            raise ModelRateLimitError(f"请求限流: {error}")
        elif isinstance(error, AuthenticationError):
            raise ModelAuthenticationError(f"认证失败: {error}")
        elif isinstance(error, APIError):
            raise ModelConnectionError(f"API 错误: {error}")
        else:
            raise ModelException(f"未知错误: {error}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ModelTimeoutError),
        reraise=True,
    )
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        messages = self._build_messages(prompt, system_prompt, history)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            self._handle_error(e)
            return ""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ModelTimeoutError),
        reraise=True,
    )
    def chat_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        messages = self._build_messages(prompt, system_prompt, history)
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self._handle_error(e)

    def render_template(self, template: str, **kwargs: Any) -> str:
        return template.format(**kwargs)

    def chat_with_template(
        self,
        template: str,
        template_vars: Dict[str, Any],
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        prompt = self.render_template(template, **template_vars)
        return self.chat(prompt, system_prompt, history, temperature, max_tokens)
