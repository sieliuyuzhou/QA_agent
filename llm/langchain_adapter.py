from typing import Any, Dict, List, Optional, Sequence

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_function

from llm.client import ChatService


def _convert_message(msg: BaseMessage) -> Dict[str, Any]:
    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": msg.content}
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    if isinstance(msg, ToolMessage):
        return {"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id}
    if isinstance(msg, AIMessage):
        d: Dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": _serialize_args(tc["args"]),
                    },
                }
                for tc in msg.tool_calls
            ]
        return d
    return {"role": "user", "content": msg.content}


def _serialize_args(args: Any) -> str:
    import json
    if isinstance(args, str):
        return args
    return json.dumps(args, ensure_ascii=False)


class ChatServiceLLM(BaseChatModel):
    chat_service: Any
    model_name: str = ""

    model_config = {"arbitrary_types_allowed": True}

    def bind_tools(
        self,
        tools: Sequence[BaseTool],
        **kwargs: Any,
    ) -> Any:
        openai_tools = [
            {"type": "function", "function": convert_to_openai_function(t)}
            for t in tools
        ]
        return self.bind(tools=openai_tools, **kwargs)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        openai_messages = [_convert_message(m) for m in messages]
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", None)
        tools = kwargs.get("tools", None)

        call_kwargs: Dict[str, Any] = dict(
            model=self.model_name or self.chat_service.model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
        )
        if tools:
            call_kwargs["tools"] = tools

        response = self.chat_service.client.chat.completions.create(**call_kwargs)
        choice = response.choices[0]
        msg = choice.message

        ai_msg = AIMessage(content=msg.content or "")
        if msg.tool_calls:
            import json
            tool_calls = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": args,
                    }
                )
            ai_msg = AIMessage(content=msg.content or "", tool_calls=tool_calls)

        return ChatResult(
            generations=[ChatGeneration(message=ai_msg)],
        )

    @property
    def _llm_type(self) -> str:
        return "chat-service-llm"
