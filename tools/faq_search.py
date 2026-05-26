from typing import Optional

from infrastructure.rag import get_store
from .base import Tool, ToolParameter


def search_faq(query: str, top_k: int = 5) -> str:
    store = get_store()
    results = store.search(query, top_k=top_k)
    
    if not results:
        return "未找到相关的FAQ内容，请尝试其他关键词。"
    
    output_lines = [f"找到 {len(results)} 条相关FAQ：\n"]
    
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        question = metadata.get("question", "未知问题")
        answer = metadata.get("answer", "未知答案")
        distance = result.get("distance", 0)
        
        output_lines.append(f"【{i}】{question}")
        output_lines.append(f"    答案：{answer}")
        output_lines.append(f"    相关度：{1 - distance:.4f}\n")
    
    return "\n".join(output_lines)


search_faq_tool = Tool(
    name="search_faq",
    description="检索FAQ知识库，根据用户问题查找相关的问答内容。输入应为用户的问题或关键词。",
    func=search_faq,
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="用户的查询问题或关键词",
            required=True,
        ),
        ToolParameter(
            name="top_k",
            type="integer",
            description="返回结果数量",
            required=False,
            default=5,
        ),
    ],
)
