from typing import Any, Optional
from uuid import UUID
from graphql.language.ast import StringValue, Value
from graphql import GraphQLScalarType


def serialize_uuid(uuid: UUID) -> str:
    return str(uuid)


def coerce_uuid(value: Any) -> Optional[UUID]:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(hex=value)
    return None


def parse_uuid_literal(ast: Value) -> Optional[UUID]:
    if isinstance(ast, StringValue):
        return UUID(hex=ast.value)
    return None


GraphQLUUID = GraphQLScalarType(
    name='UUID',
    description='UUID',
    serialize=serialize_uuid,
    parse_value=coerce_uuid,
    parse_literal=parse_uuid_literal,
)