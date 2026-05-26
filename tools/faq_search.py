from infrastructure.rag import get_store
from .base import Citation, Tool, ToolParameter, ToolResult


def retrieve_faq(query: str, top_k: int = 5) -> ToolResult:
    store = get_store()
    results = store.search(query, top_k=top_k)
    
    if not results:
        return ToolResult(content="未找到相关的 FAQ 内容，请补充产品型号或联系人工客服。")
    
    output_lines = [f"找到 {len(results)} 条相关 FAQ：\n"]
    citations = []
    
    for result in results:
        metadata = result.get("metadata", {})
        question = metadata.get("question", "未知问题")
        answer = metadata.get("answer", "未知答案")
        source_id = metadata.get("source_id", result.get("id", "unknown"))
        title = metadata.get("title", "FAQ 知识库")
        
        output_lines.append(f"问题：{question}\n答案：{answer}\n")
        citations.append(
            Citation(
                source_id=source_id,
                title=title,
                section=question,
                excerpt=answer[:160],
            )
        )
    
    return ToolResult(content="\n".join(output_lines), citations=citations)


def search_faq(query: str, top_k: int = 5) -> str:
    return retrieve_faq(query, top_k=top_k).content


search_faq_tool = Tool(
    name="search_faq",
    description="检索FAQ知识库，根据用户问题查找相关的问答内容。输入应为用户的问题或关键词。",
    func=retrieve_faq,
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
