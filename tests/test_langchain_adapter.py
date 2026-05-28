import json
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from llm.langchain_adapter import ChatServiceLLM, _convert_message, _serialize_args


class TestConvertMessage:
    def test_system_message(self):
        msg = SystemMessage(content="你是客服")
        result = _convert_message(msg)
        assert result == {"role": "system", "content": "你是客服"}

    def test_human_message(self):
        msg = HumanMessage(content="你好")
        result = _convert_message(msg)
        assert result == {"role": "user", "content": "你好"}

    def test_tool_message(self):
        msg = ToolMessage(content="FAQ 结果", tool_call_id="call_abc")
        result = _convert_message(msg)
        assert result["role"] == "tool"
        assert result["content"] == "FAQ 结果"
        assert result["tool_call_id"] == "call_abc"

    def test_ai_message_plain(self):
        msg = AIMessage(content="回答")
        result = _convert_message(msg)
        assert result == {"role": "assistant", "content": "回答"}

    def test_ai_message_with_tool_calls(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {"id": "call_1", "name": "search_faq", "args": {"query": "X1"}},
            ],
        )
        result = _convert_message(msg)
        assert result["role"] == "assistant"
        assert result["tool_calls"][0]["id"] == "call_1"
        assert result["tool_calls"][0]["function"]["name"] == "search_faq"
        assert json.loads(result["tool_calls"][0]["function"]["arguments"]) == {"query": "X1"}


class TestSerializeArgs:
    def test_dict(self):
        assert _serialize_args({"query": "X1"}) == '{"query": "X1"}'

    def test_string(self):
        assert _serialize_args("raw") == "raw"

    def test_empty(self):
        assert _serialize_args({}) == "{}"


class TestChatServiceLLM:
    def test_llm_type(self):
        mock_service = MagicMock()
        llm = ChatServiceLLM(chat_service=mock_service)
        assert llm._llm_type == "chat-service-llm"

    def test_generate_returns_ai_message(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回答"
        mock_response.choices[0].message.tool_calls = None

        mock_service = MagicMock()
        mock_service.model_name = "gpt-3.5-turbo"
        mock_service.client.chat.completions.create.return_value = mock_response

        llm = ChatServiceLLM(chat_service=mock_service)
        result = llm._generate([HumanMessage(content="你好")])
        assert result.generations[0].message.content == "回答"
        assert result.generations[0].message.tool_calls == []

    def test_generate_with_tool_calls(self):
        mock_tc = MagicMock()
        mock_tc.id = "call_1"
        mock_tc.function.name = "search_faq"
        mock_tc.function.arguments = '{"query": "X1"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_response.choices[0].message.tool_calls = [mock_tc]

        mock_service = MagicMock()
        mock_service.model_name = "gpt-3.5-turbo"
        mock_service.client.chat.completions.create.return_value = mock_response

        llm = ChatServiceLLM(chat_service=mock_service)
        result = llm._generate([HumanMessage(content="X1 怎么重置")])
        ai_msg = result.generations[0].message
        assert len(ai_msg.tool_calls) == 1
        assert ai_msg.tool_calls[0]["name"] == "search_faq"
        assert ai_msg.tool_calls[0]["args"] == {"query": "X1"}
        assert ai_msg.tool_calls[0]["id"] == "call_1"
