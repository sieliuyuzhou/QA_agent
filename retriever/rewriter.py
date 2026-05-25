import os
from typing import Optional
from dotenv import load_dotenv

from model import get_service
from .exceptions import RewriteError

load_dotenv()


class QueryRewriter:
    system_prompt: str
    template: str

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        template: Optional[str] = None,
    ):
        self.system_prompt = system_prompt or os.getenv(
            "RETRIEVER_SYSTEM_PROMPT",
            "",
        )
        self.template = template or os.getenv(
            "RETRIEVER_TEMPLATE",
            "请将以下问题改写为更适合检索的形式，只输出改写后的问题：\n{query}",
        )

    def rewrite(self, query: str) -> str:
        service = get_service()
        prompt = service.render_template(self.template, query=query)
        try:
            rewritten = service.chat(
                prompt=prompt,
                system_prompt=self.system_prompt if self.system_prompt else None,
                temperature=0.3,
                max_tokens=100,
            )
            return rewritten.strip()
        except Exception as e:
            raise RewriteError(f"查询改写失败: {e}")
