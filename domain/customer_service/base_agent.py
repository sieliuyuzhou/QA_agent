import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from tools.base import ToolResult


class BaseReActAgent(ABC):
    """共享 ReAct 循环基类。子类只需覆盖 _get_system_prompt() 和 _handle_terminal_action()。"""

    def __init__(self, llm, tools: list, max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self._tools_map = {tool.name: tool for tool in tools}

    def _find_tool(self, name: str):
        return self._tools_map.get(name)

    def _build_tools_description(self) -> str:
        return "\n".join(tool.to_prompt_desc() for tool in self.tools)

    def _format_context(self, messages: list) -> str:
        if not messages:
            return "（无历史对话）"
        return "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}"
            for m in messages
        )

    def _format_step_history(self, step_history: List[Dict[str, str]]) -> str:
        if not step_history:
            return ""
        lines = []
        for step in step_history:
            for key in ("thought", "action", "observation"):
                if step.get(key):
                    lines.append(f"{key.capitalize()}: {step[key]}")
            lines.append("")
        return "\n".join(lines)

    def _parse_output(self, output: str) -> Dict[str, str]:
        result = {"thought": "", "action": "", "action_name": "", "action_input": ""}

        thought_match = re.search(
            r"Thought:\s*(.+?)(?=Action:|$)", output, re.DOTALL | re.IGNORECASE
        )
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        action_match = re.search(
            r"Action:\s*(.+?)(?=$)", output, re.DOTALL | re.IGNORECASE
        )
        if action_match:
            result["action"] = action_match.group(1).strip()

        if result["action"]:
            m = re.match(r"(\w+)\s*\[(.+)\]", result["action"], re.DOTALL)
            if m:
                result["action_name"] = m.group(1).strip()
                result["action_input"] = m.group(2).strip()

        return result

    def _map_action_input(self, action_input: str, tool) -> dict:
        if not action_input:
            return {}
        try:
            params = json.loads(action_input)
            if isinstance(params, dict):
                return params
        except json.JSONDecodeError:
            pass
        required_params = [p for p in tool.parameters if p.required]
        if len(required_params) == 1:
            return {required_params[0].name: action_input}
        return {}

    def _dispatch_tool(self, action_name: str, action_input: str) -> Any:
        tool = self._find_tool(action_name)
        if not tool:
            return f"错误：未找到名为 '{action_name}' 的工具"
        params = self._map_action_input(action_input, tool)
        try:
            return tool.run(params)
        except ValueError as e:
            return f"错误：{e}"
        except Exception as e:
            return f"工具执行错误：{e}"

    @abstractmethod
    def _get_system_prompt(self) -> str:
        ...

    @abstractmethod
    def _handle_terminal_action(
        self, action_name: str, action_input: str, citations: list, step: int
    ) -> Any:
        ...

    def run_react_loop(
        self,
        user_input: str,
        context_messages: list,
        current_user=None,
        conversation_id: str = "",
    ) -> Any:
        context = self._format_context(context_messages)
        tools_desc = self._build_tools_description()
        step_history = []
        citations = []
        knowledge_lookup_without_sources = False

        system_prompt = self._get_system_prompt()

        for step in range(self.max_steps):
            history_str = self._format_step_history(step_history)

            from domain.customer_service.prompts import build_user_prompt
            prompt = build_user_prompt(
                context=context, user_input=user_input, history=history_str
            )

            try:
                output = self.llm.chat(prompt, system_prompt=system_prompt)
            except Exception as e:
                step_history.append({
                    "thought": f"LLM 调用失败: {e}",
                    "action": "",
                    "observation": f"错误：{e}",
                })
                continue

            parsed = self._parse_output(output)

            if not parsed["action_name"]:
                step_history.append({
                    "thought": parsed["thought"],
                    "action": parsed["action"],
                    "observation": "无法解析 Action，请使用正确的格式：Action: tool_name[input]",
                })
                continue

            action_name = parsed["action_name"]
            action_input = parsed["action_input"]

            terminal_actions = {"Finish", "AskUser", "Handoff"}
            if action_name in terminal_actions:
                if (
                    action_name == "Finish"
                    and knowledge_lookup_without_sources
                    and not citations
                ):
                    action_name = "Handoff"
                    action_input = "当前没有找到可靠知识依据，已为您转接人工进一步确认。"
                return self._handle_terminal_action(
                    action_name, action_input, citations, step
                )

            tool_result = self._dispatch_tool(action_name, action_input)
            if isinstance(tool_result, ToolResult):
                observation = tool_result.content
                citations.extend(tool_result.citations)
                if not tool_result.citations:
                    knowledge_lookup_without_sources = True
            else:
                observation = str(tool_result)

            step_history.append({
                "thought": parsed["thought"],
                "action": parsed["action"],
                "observation": observation,
            })

        return self._handle_terminal_action(
            "Finish",
            "抱歉，我无法在有限的步骤内解决您的问题，请尝试更具体地描述您的需求。",
            citations,
            self.max_steps,
        )
