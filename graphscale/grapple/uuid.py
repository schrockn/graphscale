from uuid import UUID
from graphql.language.ast import StringValue
from graphql import GraphQLScalarType
from graphscale import check


def serialize_uuid(uuid):
    check.uuid_param(uuid, 'uuid')
    return str(uuid)


def coerce_uuid(value):
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(hex=value)
    return None


def parse_uuid_literal(ast):
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