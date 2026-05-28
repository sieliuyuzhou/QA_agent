from langchain_core.messages import AIMessage

from domain.customer_service.langgraph_supervisor import LangGraphSupervisor
from domain.customer_service.sub_agent import SubAgentResponse


class FakeLLMForSupervisor:
    def __init__(self, response):
        self._response = response

    def bind_tools(self, tools, **kwargs):
        class Bound:
            def __init__(self, parent):
                self._parent = parent
            def invoke(self, messages, **kw):
                return self._parent._response
        return Bound(self)


class FakeManager:
    def __init__(self):
        self.messages = []
    def add_message(self, conv_id, role, content, metadata=None):
        self.messages.append({"role": role, "content": content, "metadata": metadata})
    def get_context(self, conv_id):
        return self.messages


class FakeTroubleshooting:
    def run(self, **kwargs):
        return SubAgentResponse(status="completed", recommended_response="排障步骤",
                                metadata={"agent": "TroubleshootingAgent"})


class FakeAfterSales:
    def run(self, **kwargs):
        return SubAgentResponse(status="completed", recommended_response="售后结果",
                                metadata={"agent": "AfterSalesAgent"})


class FakeConsultation:
    def run(self, **kwargs):
        return SubAgentResponse(
            status="completed", recommended_response="X2 支持 Zigbee",
            citations=[type("C", (), {"source_id": "doc2", "title": "FAQ", "section": "s", "excerpt": "e"})()],
            metadata={"agent": "ConsultationHandler"},
        )


def test_diagnosis_routes_to_troubleshooting():
    llm = FakeLLMForSupervisor(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "RouteTroubleshooting", "args": {"message": "X1 连不上 WiFi"}}])
    )
    sup = LangGraphSupervisor(llm=llm, manager=FakeManager(),
                               troubleshooting_agent=FakeTroubleshooting(),
                               after_sales_agent=FakeAfterSales(),
                               consultation_handler=FakeConsultation())
    resp = sup.run("X1 连不上 WiFi", "conv-1")
    assert resp.type == "final_answer"
    assert resp.metadata.get("sub_agent") == "TroubleshootingAgent"


def test_consultation_routes_to_handler():
    llm = FakeLLMForSupervisor(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "RouteConsultation", "args": {"message": "X2 支持 Zigbee 吗"}}])
    )
    sup = LangGraphSupervisor(llm=llm, manager=FakeManager(),
                               troubleshooting_agent=FakeTroubleshooting(),
                               after_sales_agent=FakeAfterSales(),
                               consultation_handler=FakeConsultation())
    resp = sup.run("X2 支持 Zigbee 吗", "conv-1")
    assert resp.type == "final_answer"
    assert resp.citations


def test_handoff_returns_handoff():
    llm = FakeLLMForSupervisor(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "Handoff", "args": {"reason": "用户要求人工"}}])
    )
    sup = LangGraphSupervisor(llm=llm, manager=FakeManager(),
                               troubleshooting_agent=FakeTroubleshooting(),
                               after_sales_agent=FakeAfterSales(),
                               consultation_handler=FakeConsultation())
    resp = sup.run("转人工", "conv-1")
    assert resp.type == "handoff"


def test_ask_user_returns_ask_user():
    llm = FakeLLMForSupervisor(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "AskUser", "args": {"question": "请问有什么可以帮您？"}}])
    )
    sup = LangGraphSupervisor(llm=llm, manager=FakeManager(),
                               troubleshooting_agent=FakeTroubleshooting(),
                               after_sales_agent=FakeAfterSales(),
                               consultation_handler=FakeConsultation())
    resp = sup.run("你好", "conv-1")
    assert resp.type == "ask_user"


def test_after_sales_routes():
    llm = FakeLLMForSupervisor(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "RouteAfterSales", "args": {"message": '{"order_id":"ORD-A-X1","request_type":"warranty_repair","issue_cause":"non_human_fault","issue_summary":"test"}'}}])
    )
    sup = LangGraphSupervisor(llm=llm, manager=FakeManager(),
                               troubleshooting_agent=FakeTroubleshooting(),
                               after_sales_agent=FakeAfterSales(),
                               consultation_handler=FakeConsultation())
    resp = sup.run("我要售后", "conv-1")
    assert resp.type == "final_answer"
    assert resp.metadata.get("sub_agent") == "AfterSalesAgent"
