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
class Citation:
    source_id: str
    title: str
    section: str
    excerpt: str


@dataclass
class ToolResult:
    content: str
    citations: list[Citation] = field(default_factory=list)


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: list[ToolParameter] = field(default_factory=list)

    def run(self, params: dict) -> Any:
        required_params = [p for p in self.parameters if p.required]
        missing = [p.name for p in required_params if p.name not in params]
        if missing:
            raise ValueError(f"缺少必填参数: {missing}")
        
        full_params = {}
        for p in self.parameters:
            if p.name in params:
                full_params[p.name] = params[p.name]
            elif not p.required and p.default is not None:
                full_params[p.name] = p.default
        
        full_params.update({k: v for k, v in params.items() if k not in full_params})
        
        return self.func(**full_params)

    def to_prompt_desc(self) -> str:
        if not self.parameters:
            return f"- {self.name}(): {self.description}"
        
        params_str = ", ".join(
            f"{p.name}: {p.type}" + (" (可选)" if not p.required else "")
            for p in self.parameters
        )
        return f"- {self.name}({params_str}): {self.description}"

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {
                            "type": p.type,
                            "description": p.description,
                        }
                        for p in self.parameters
                    },
                    "required": [p.name for p in self.parameters if p.required],
                },
            },
        }
