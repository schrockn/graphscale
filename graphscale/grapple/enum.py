from collections import OrderedDict
from enum import Enum
from typing import Any
from graphql import GraphQLEnumType
from graphql.type import GraphQLEnumValue
from graphql.language.ast import EnumValue, Value


class GraphQLPythonEnumType(GraphQLEnumType):
    def __init__(self, python_enum_type: Any, description: str=None) -> None:
        self.python_enum_type = python_enum_type
        name = python_enum_type.__name__
        values = OrderedDict()  # type: OrderedDict[Any, GraphQLEnumValue]
        for enum_value in python_enum_type.__members__.keys():
            values[enum_value] = GraphQLEnumValue(value=enum_value)
        super().__init__(name, values, description=description)

    def serialize(self, value: Enum) -> str:
        return value.name

    def parse_value(self, value: str) -> Enum:
        return self.python_enum_type(value)  # type: ignore

    def parse_literal(self, value_ast: Value) -> Enum:
        if not isinstance(value_ast, EnumValue):
            return None
        return self.python_enum_type(value_ast.value)  # type: ignore
