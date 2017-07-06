from enum import Enum
from typing import Callable, Any
import pytest

from graphql import GraphQLObjectType, GraphQLField, graphql, GraphQLSchema, GraphQLArgument

from graphscale.grapple.enum import GraphQLPythonEnumType

pytestmark = pytest.mark.asyncio


class EnumTest(Enum):
    VALUE_ONE = 'VALUE_ONE'
    VALUE_TWO = 'VALUE_TWO'


def define_schema(resolver: Callable, enumType: GraphQLObjectType) -> GraphQLSchema:
    def resolve_input(_obj: Any, args: dict, *_: Any) -> Any:
        assert isinstance(args['testEnumArg'], EnumTest)
        return args['testEnumArg']

    query_type = GraphQLObjectType(
        name='Query',
        fields={
            'testEnum':
            GraphQLField(type=enumType, resolver=resolver),
            'testEnumArg':
            GraphQLField(
                type=enumType,
                args={'testEnumArg': GraphQLArgument(type=enumType)},
                resolver=resolve_input
            )
        }
    )
    return GraphQLSchema(query=query_type)


GraphQLEnumTest = GraphQLPythonEnumType(EnumTest)


async def test_out_enum() -> None:
    schema = define_schema(lambda *_: EnumTest.VALUE_ONE, GraphQLEnumTest)
    result = await graphql(schema, '{ testEnum }')
    assert result.data['testEnum'] == 'VALUE_ONE'

    schema = define_schema(lambda *_: EnumTest.VALUE_TWO, GraphQLEnumTest)
    result = await graphql(schema, '{ testEnum }')
    assert result.data['testEnum'] == 'VALUE_TWO'


async def test_enum_args() -> None:
    schema = define_schema(lambda *_: EnumTest.VALUE_ONE, GraphQLEnumTest)
    result = await graphql(schema, '{ testEnumArg(testEnumArg: VALUE_ONE) }')
    assert result.data['testEnumArg'] == 'VALUE_ONE'

    result = await graphql(schema, '{ testEnumArg(testEnumArg: VALUE_TWO) }')
    assert result.data['testEnumArg'] == 'VALUE_TWO'
