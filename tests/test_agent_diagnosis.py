from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent
from domain.customer_service.diagnosis import DiagnosisWorkflow
from domain.customer_service.workflows import WorkflowResult
from tools.base import Citation, ToolResult


DIAGNOSIS_ACTION = (
    'Action: PrepareDiagnosis[{"product_model":"X1",'
    '"symptom":"无法联网","observed_state":"红灯常亮",'
    '"attempted_steps":["重启"]}]'
)

X1_CITATION = Citation(
    source_id="doc1-x1",
    title="Doc1-X1智能门锁FAQ",
    section="连不上WiFi怎么办",
    excerpt="请按以下步骤排查。",
)


def _build_agent(llm_output, knowledge_result=None):
    manager = MemoryConversationManager()
    llm = SequenceLLM(llm_output)

    def knowledge_search(query):
        return knowledge_result or ToolResult(
            content="排障步骤", citations=[X1_CITATION]
        )

    workflow = DiagnosisWorkflow(knowledge_search)
    agent = CustomerServiceAgent(
        llm, manager, [], diagnosis_workflow=workflow
    )
    return agent, manager, llm


def test_prepare_diagnosis_dispatches_and_returns_troubleshooting():
    agent, manager, _ = _build_agent(DIAGNOSIS_ACTION)

    response = agent.run("X1 连不上网，红灯常亮", "conv-1")

    assert response.type == "final_answer"
    assert "X1" in response.content
    assert response.citations == [X1_CITATION]
    assert response.metadata["intent"] == "diagnosis"
    assert manager.messages[-1]["metadata"]["conversation_state"] == "active"


def test_prompt_advertises_prepare_diagnosis():
    llm = SequenceLLM("Action: AskUser[请提供型号。]")
    agent = CustomerServiceAgent(llm, MemoryConversationManager(), [])

    agent.run("门锁出问题了", "conv-1")

    assert "PrepareDiagnosis" in llm.calls[0]["system_prompt"]


def test_invalid_diagnosis_json_asks_for_clarification():
    agent, manager, _ = _build_agent("Action: PrepareDiagnosis[not json]")

    response = agent.run("X1 连不上网", "conv-1")

    assert response.type == "ask_user"
    assert "型号" in response.content or "故障" in response.content


def test_diagnosis_without_workflow_hands_off():
    manager = MemoryConversationManager()
    llm = SequenceLLM(DIAGNOSIS_ACTION)
    agent = CustomerServiceAgent(llm, manager, [])

    response = agent.run("X1 连不上网", "conv-1")

    assert response.type == "handoff"
    assert manager.messages[-1]["metadata"]["conversation_state"] == "handoff_requested"


def test_diagnosis_no_citations_hands_off():
    agent, manager, _ = _build_agent(
        DIAGNOSIS_ACTION,
        knowledge_result=ToolResult(content="无匹配"),
    )

    response = agent.run("X1 连不上网", "conv-1")

    assert response.type == "handoff"
