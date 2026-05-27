from domain.customer_service.diagnosis import DiagnosisWorkflow
from domain.customer_service.workflows import WorkflowResult
from tools.base import Citation, ToolResult


X1_FAQ_CITATION = Citation(
    source_id="doc1-x1",
    title="Doc1-X1智能门锁FAQ",
    section="连不上WiFi怎么办",
    excerpt="请按以下步骤排查WiFi连接问题。",
)

TROUBLESHOOTING_RESULT = ToolResult(
    content="X1 连不上 WiFi 排障：1. 确认路由器 2.4G 模式 2. 重启门锁 3. 重置网络",
    citations=[X1_FAQ_CITATION],
)


def _knowledge_returns(result: ToolResult):
    return lambda query: result


def test_complete_input_returns_troubleshooting_steps_with_citations():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "无法联网",
    })

    assert result.response_type == "final_answer"
    assert "X1" in result.content
    assert "无法联网" in result.content
    assert result.citations == [X1_FAQ_CITATION]
    assert result.metadata["intent"] == "diagnosis"
    assert result.metadata["workflow"] == "diagnosis"
    assert result.metadata["product_model"] == "X1"


def test_input_with_observed_state_includes_state_in_response():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "无法联网",
        "observed_state": "红灯常亮",
    })

    assert result.response_type == "final_answer"
    assert "红灯常亮" in result.content


def test_input_with_attempted_steps_acknowledges_prior_efforts():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "无法联网",
        "attempted_steps": ["重启路由器", "更换电池"],
    })

    assert result.response_type == "final_answer"
    assert "重启路由器" in result.content
    assert "更换电池" in result.content


def test_missing_product_model_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {"symptom": "无法联网"})

    assert result.response_type == "ask_user"
    assert "型号" in result.content


def test_missing_symptom_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {"product_model": "X1"})

    assert result.response_type == "ask_user"
    assert "故障" in result.content or "现象" in result.content


def test_empty_product_model_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {"product_model": "", "symptom": "无法联网"})

    assert result.response_type == "ask_user"


def test_empty_symptom_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {"product_model": "X1", "symptom": ""})

    assert result.response_type == "ask_user"


def test_non_dict_payload_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", "not a dict")

    assert result.response_type == "ask_user"


def test_no_citations_from_search_returns_handoff():
    workflow = DiagnosisWorkflow(
        _knowledge_returns(ToolResult(content="无匹配"))
    )

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "量子纠缠",
    })

    assert result.response_type == "handoff"
    assert "人工" in result.content
    assert result.citations == []


def test_search_query_includes_model_and_symptom():
    captured_queries = []

    def capture_search(query):
        captured_queries.append(query)
        return TROUBLESHOOTING_RESULT

    workflow = DiagnosisWorkflow(capture_search)
    workflow.prepare("conv-1", {
        "product_model": "X2",
        "symptom": "指纹不灵敏",
    })

    assert captured_queries == ["X2 指纹不灵敏"]


def test_invalid_observed_state_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "无法联网",
        "observed_state": "   ",
    })

    assert result.response_type == "ask_user"


def test_invalid_attempted_steps_type_returns_ask_user():
    workflow = DiagnosisWorkflow(_knowledge_returns(TROUBLESHOOTING_RESULT))

    result = workflow.prepare("conv-1", {
        "product_model": "X1",
        "symptom": "无法联网",
        "attempted_steps": "not a list",
    })

    assert result.response_type == "ask_user"
