import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

from .exceptions import EmbeddingError

load_dotenv()


class EmbeddingService:
    api_key: str
    base_url: str
    model_name: str
    _client: Optional[OpenAI] = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY", "")
        self.base_url = base_url or os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def embed(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingError(f"向量化失败: {e}")

    def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                raise EmbeddingError(f"批量向量化失败 (批次 {i//batch_size + 1}): {e}")
        return all_embeddings
