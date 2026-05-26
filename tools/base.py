from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: list[ToolParameter] = field(default_factory=list)

    def run(self, params: dict) -> str:
        required_params = [p for p in self.parameters if p.required]
        missing = [p.name for p in required_params if p.name not in params]
        if missing:
            raise ValueError(f"缺少必填参数: {missing}")
        return self.func(**params)

    def to_prompt_desc(self) -> str:
        params_str = ", ".join(
            f"{p.name}: {p.type}" + (" (可选)" if not p.required else "")
            for p in self.parameters
        )
        return f"- {self.name}({params_str}): {self.description}"

    def to_openai_schema(self) -> dict:
        return {}
