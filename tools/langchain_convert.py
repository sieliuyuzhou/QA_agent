from typing import Any, Callable, Dict, List, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

from tools.base import Tool

_TYPE_MAP: Dict[str, Type] = {
    "string": str,
    "str": str,
    "integer": int,
    "int": int,
    "number": float,
    "float": float,
    "boolean": bool,
    "bool": bool,
}


def _build_args_schema(tool: Tool) -> Type:
    fields = {}
    for p in tool.parameters:
        py_type = _TYPE_MAP.get(p.type, str)
        if not p.required:
            py_type = Optional[py_type]
            default = p.default if p.default is not None else None
            fields[p.name] = (py_type, Field(default=default, description=p.description))
        else:
            fields[p.name] = (py_type, Field(description=p.description))
    return create_model(f"{tool.name}Args", **fields)


def _wrap_func(tool: Tool) -> Callable[..., Any]:
    def wrapper(**kwargs: Any) -> Any:
        return tool.run(kwargs)
    wrapper.__name__ = tool.name
    wrapper.__doc__ = tool.description
    return wrapper


def to_structured_tool(tool: Tool) -> StructuredTool:
    schema = _build_args_schema(tool)
    return StructuredTool.from_function(
        _wrap_func(tool),
        name=tool.name,
        description=tool.description,
        args_schema=schema,
        return_direct=False,
    )


def to_structured_tools(tools: List[Tool]) -> List[StructuredTool]:
    return [to_structured_tool(t) for t in tools]
