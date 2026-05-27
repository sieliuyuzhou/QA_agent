from typing import Dict, List, Optional

from tools.base import Tool


class ToolRegistry:
    def __init__(self, agent_tools: Dict[str, List[Tool]]):
        self._agent_tools = {
            agent: {t.name: t for t in tools}
            for agent, tools in agent_tools.items()
        }

    def get_tool(self, agent_name: str, tool_name: str) -> Optional[Tool]:
        return self._agent_tools.get(agent_name, {}).get(tool_name)

    def list_tools(self, agent_name: str) -> List[str]:
        return list(self._agent_tools.get(agent_name, {}).keys())
