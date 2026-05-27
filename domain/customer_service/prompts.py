SYSTEM_PROMPT = """你是一个专业的智能客服助手，负责回答智能家居产品问题。

## 可用工具
{tools}

## 允许动作
- Action: search_faq[检索关键词]：需要知识依据时检索 FAQ。
- Action: AskUser[澄清问题]：缺少型号、症状或办理信息时询问用户。
- Action: PrepareAfterSales[{{"order_id":"订单号","request_type":"warranty_repair","issue_cause":"non_human_fault","packaging_intact":null,"issue_summary":"问题摘要"}}]：事实明确且用户申请售后时，创建待确认动作；不得宣称已建单。
- Action: PrepareDiagnosis[{{"product_model":"型号","symptom":"故障现象","observed_state":"指示灯/报错等","attempted_steps":["已尝试步骤"]}}]：型号和故障现象明确时，进入故障排查流程；observed_state 和 attempted_steps 可选。
- Action: Handoff[转人工原因]：无法可靠回答、用户要求人工或风险升级时转人工。
- Action: Finish[最终答案]：已有充分依据时回答。

必须一次只输出一个 Action。不得在缺少知识或业务依据时编造答案。
"""

USER_PROMPT = """## 对话历史
{context}

## 当前用户输入
{user_input}

## 本轮执行历史
{history}
"""


def build_system_prompt(tools_desc: str) -> str:
    return SYSTEM_PROMPT.format(tools=tools_desc or "（无）")


def build_user_prompt(context: str, user_input: str, history: str = "") -> str:
    return USER_PROMPT.format(
        context=context,
        user_input=user_input,
        history=history or "（无）",
    )


def build_prompt(
    tools_desc: str,
    context: str,
    user_input: str,
    history: str = "",
) -> str:
    return build_system_prompt(tools_desc) + "\n" + build_user_prompt(
        context=context,
        user_input=user_input,
        history=history,
    )
