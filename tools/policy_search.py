from infrastructure.rag import get_store

from .base import Citation, Tool, ToolParameter, ToolResult


POLICY_SOURCE_ID = "Doc5-售后与保修政策"


def retrieve_policy(query: str, top_k: int = 5) -> ToolResult:
    results = get_store().search(query, top_k=top_k, source_id=POLICY_SOURCE_ID)
    policy_results = [
        result
        for result in results
        if result.get("metadata", {}).get("source_id") == POLICY_SOURCE_ID
    ]
    if not policy_results:
        return ToolResult(content="未找到有效的售后政策依据，请补充信息或联系人工客服。")

    content = []
    citations = []
    for result in policy_results:
        metadata = result.get("metadata", {})
        section = metadata.get("question", "售后政策")
        answer = metadata.get("answer", "")
        content.append(f"政策章节：{section}\n内容：{answer}")
        citations.append(
            Citation(
                source_id=POLICY_SOURCE_ID,
                title=metadata.get("title", POLICY_SOURCE_ID),
                section=section,
                excerpt=answer[:160],
            )
        )
    return ToolResult(content="\n\n".join(content), citations=citations)


policy_search_tool = Tool(
    name="search_after_sales_policy",
    description="仅检索售后与保修政策，返回政策来源依据。",
    func=retrieve_policy,
    parameters=[
        ToolParameter("query", "string", "需要核对的售后政策问题"),
        ToolParameter("top_k", "integer", "返回结果数量", required=False, default=5),
    ],
)
