from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.supervisor import Supervisor
from domain.customer_service.sub_agent import SubAgentResponse


class FakeTroubleshootingAgent:
    def __init__(self, response):
        self._response = response
    def run(self, **kwargs):
        return self._response


class FakeAfterSalesAgent:
    def __init__(self, response):
        self._response = response
    def run(self, **kwargs):
        return self._response


class FakeConsultationHandler:
    def __init__(self, response):
        self._response = response
    def run(self, **kwargs):
        return self._response


def test_diagnosis_intent_routes_to_troubleshooting():
    diag = FakeTroubleshootingAgent(SubAgentResponse(
        status="completed", recommended_response="排障步骤",
        citations=[], metadata={"agent": "TroubleshootingAgent"},
    ))
    supervisor = Supervisor(
        llm=SequenceLLM("Action: RouteTroubleshooting[X1 连不上 WiFi]"),
        manager=MemoryConversationManager(),
        troubleshooting_agent=diag,
        after_sales_agent=FakeAfterSalesAgent(SubAgentResponse(status="completed")),
        consultation_handler=FakeConsultationHandler(SubAgentResponse(status="completed")),
    )
    resp = supervisor.run("X1 连不上 WiFi", "conv-1")
    assert resp.type == "final_answer"
    assert resp.metadata.get("sub_agent") == "TroubleshootingAgent"


def test_consultation_intent_routes_to_handler():
    consult = FakeConsultationHandler(SubAgentResponse(
        status="completed", recommended_response="X2 支持 Zigbee",
        citations=[type("C", (), {"source_id": "doc2", "title": "X2 FAQ", "section": "Zigbee", "excerpt": "支持"})()],
        metadata={"agent": "ConsultationHandler"},
    ))
    supervisor = Supervisor(
        llm=SequenceLLM("Action: RouteConsultation[X2 支持 Zigbee 吗]"),
        manager=MemoryConversationManager(),
        troubleshooting_agent=FakeTroubleshootingAgent(SubAgentResponse(status="completed")),
        after_sales_agent=FakeAfterSalesAgent(SubAgentResponse(status="completed")),
        consultation_handler=consult,
    )
    resp = supervisor.run("X2 支持 Zigbee 吗", "conv-1")
    assert resp.type == "final_answer"
    assert resp.citations


def test_handoff_intent_returns_handoff():
    supervisor = Supervisor(
        llm=SequenceLLM("Action: Handoff[用户要求人工]"),
        manager=MemoryConversationManager(),
        troubleshooting_agent=FakeTroubleshootingAgent(SubAgentResponse(status="completed")),
        after_sales_agent=FakeAfterSalesAgent(SubAgentResponse(status="completed")),
        consultation_handler=FakeConsultationHandler(SubAgentResponse(status="completed")),
    )
    resp = supervisor.run("转人工", "conv-1")
    assert resp.type == "handoff"


def test_ask_user_intent_returns_ask_user():
    supervisor = Supervisor(
        llm=SequenceLLM("Action: AskUser[请问有什么可以帮您？]"),
        manager=MemoryConversationManager(),
        troubleshooting_agent=FakeTroubleshootingAgent(SubAgentResponse(status="completed")),
        after_sales_agent=FakeAfterSalesAgent(SubAgentResponse(status="completed")),
        consultation_handler=FakeConsultationHandler(SubAgentResponse(status="completed")),
    )
    resp = supervisor.run("你好", "conv-1")
    assert resp.type == "ask_user"
