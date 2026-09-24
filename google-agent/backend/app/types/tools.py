from typing import Literal, NotRequired, Protocol, TypeAlias, TypedDict

from app.types.json_types import JSONValue

ToolArguments: TypeAlias = dict[str, JSONValue]


class AgentTool(Protocol):
    def __call__(self, **kwargs: JSONValue) -> str: ...


class ToolPropertySchema(TypedDict, total=False):
    type: str
    description: str
    items: JSONValue


class ToolParametersSchema(TypedDict):
    type: str
    properties: dict[str, ToolPropertySchema]
    required: list[str]


class ToolFunctionSchema(TypedDict):
    name: str
    description: str
    parameters: ToolParametersSchema


class ToolSchema(TypedDict):
    type: Literal["function"]
    function: ToolFunctionSchema
