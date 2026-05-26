import re
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .prompts import build_prompt


@dataclass
class AgentResponse:
    type: str
    content: str
    conversation_id: str
    metadata: Optional[dict] = None


class CustomerServiceAgent:
    def __init__(
        self,
        llm,
        conversation_manager,
        tools: list,
        system_prompt: Optional[str] = None,
        max_steps: int = 5,
    ):
        self.llm = llm
        self.conversation_manager = conversation_manager
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self._tools_map = {tool.name: tool for tool in tools}

    def _find_tool(self, name: str):
        return self._tools_map.get(name)

    def _build_tools_description(self) -> str:
        lines = []
        for tool in self.tools:
            lines.append(tool.to_prompt_desc())
        return "\n".join(lines)

    def _format_context(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return "（无历史对话）"
        
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines)

    def _format_step_history(self, step_history: List[Dict[str, str]]) -> str:
        if not step_history:
            return ""
        
        lines = []
        for step in step_history:
            thought = step.get("thought", "")
            action = step.get("action", "")
            observation = step.get("observation", "")
            
            if thought:
                lines.append(f"Thought: {thought}")
            if action:
                lines.append(f"Action: {action}")
            if observation:
                lines.append(f"Observation: {observation}")
            lines.append("")
        
        return "\n".join(lines)

    def _parse_output(self, output: str) -> Dict[str, str]:
        result = {
            "thought": "",
            "action": "",
            "action_name": "",
            "action_input": "",
        }
        
        thought_match = re.search(r"\*\*Thought\*\*:\s*(.+?)(?=\*\*Action\*\*|$)", output, re.DOTALL | re.IGNORECASE)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        else:
            thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", output, re.DOTALL | re.IGNORECASE)
            if thought_match:
                result["thought"] = thought_match.group(1).strip()
        
        action_match = re.search(r"\*\*Action\*\*:\s*(.+?)(?=\*\*Observation\*\*|$)", output, re.DOTALL | re.IGNORECASE)
        if action_match:
            result["action"] = action_match.group(1).strip()
        else:
            action_match = re.search(r"Action:\s*(.+?)(?=Observation:|$)", output, re.DOTALL | re.IGNORECASE)
            if action_match:
                result["action"] = action_match.group(1).strip()
        
        if result["action"]:
            action_pattern = r"(\w+)\s*\[(.+?)\]"
            action_match = re.match(action_pattern, result["action"])
            if action_match:
                result["action_name"] = action_match.group(1).strip()
                result["action_input"] = action_match.group(2).strip()
        
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

    def _dispatch_tool(self, action_name: str, action_input: str) -> str:
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

    def run(self, user_input: str, conversation_id: str, verbose: bool = False) -> AgentResponse:
        self.conversation_manager.add_message(
            conversation_id, "user", user_input
        )
        
        context_messages = self.conversation_manager.get_context(conversation_id)
        context = self._format_context(context_messages)
        
        tools_desc = self._build_tools_description()
        
        step_history = []
        
        for step in range(self.max_steps):
            history_str = self._format_step_history(step_history)
            
            prompt = build_prompt(
                tools_desc=tools_desc,
                context=context,
                user_input=user_input,
                history=history_str,
            )
            
            if verbose:
                print(f"\n{'='*50}")
                print(f"[Step {step + 1}] 构建 Prompt...")
                print(f"{'='*50}")
            
            try:
                output = self.llm.chat(prompt)
                if verbose:
                    print(f"\n[LLM 原始输出]:\n{output}")
            except Exception as e:
                step_history.append({
                    "thought": f"LLM 调用失败: {e}",
                    "action": "",
                    "observation": f"错误：{e}",
                })
                if verbose:
                    print(f"\n[ERROR] LLM 调用失败: {e}")
                continue
            
            parsed = self._parse_output(output)
            
            if verbose:
                print(f"\n[解析结果]:")
                print(f"  Thought: {parsed['thought'][:100]}..." if len(parsed['thought']) > 100 else f"  Thought: {parsed['thought']}")
                print(f"  Action: {parsed['action']}")
                print(f"  Action Name: {parsed['action_name']}")
                print(f"  Action Input: {parsed['action_input']}")
            
            if not parsed["action_name"]:
                step_history.append({
                    "thought": parsed["thought"],
                    "action": parsed["action"],
                    "observation": "无法解析 Action，请使用正确的格式：Action: tool_name[input]",
                })
                if verbose:
                    print(f"\n[WARN] 无法解析 Action，继续重试...")
                continue
            
            action_name = parsed["action_name"]
            action_input = parsed["action_input"]
            
            if action_name == "Finish":
                final_answer = action_input
                self.conversation_manager.add_message(
                    conversation_id, "assistant", final_answer
                )
                if verbose:
                    print(f"\n[Finish] 最终答案: {final_answer[:200]}..." if len(final_answer) > 200 else f"\n[Finish] 最终答案: {final_answer}")
                return AgentResponse(
                    type="final_answer",
                    content=final_answer,
                    conversation_id=conversation_id,
                    metadata={"step_history": step_history, "total_steps": step + 1},
                )
            
            if verbose:
                print(f"\n[调用工具] {action_name}[{action_input}]")
            
            observation = self._dispatch_tool(action_name, action_input)
            
            if verbose:
                obs_preview = observation[:300] + "..." if len(observation) > 300 else observation
                print(f"\n[Observation]:\n{obs_preview}")
            
            step_history.append({
                "thought": parsed["thought"],
                "action": parsed["action"],
                "observation": observation,
            })
        
        fallback_message = "抱歉，我无法在有限的步骤内解决您的问题，请尝试更具体地描述您的需求。"
        self.conversation_manager.add_message(
            conversation_id, "assistant", fallback_message
        )
        return AgentResponse(
            type="final_answer",
            content=fallback_message,
            conversation_id=conversation_id,
            metadata={"step_history": step_history, "total_steps": self.max_steps},
        )
