from graphql import GraphQLNonNull, GraphQLList
from graphql.type.definition import GraphQLType

from .grapple_types import (
    define_default_resolver,
    define_default_gen_resolver,
    async_field_error_boundary,
    define_pent_mutation_resolver,
)

from .date import GraphQLDate
from .uuid import GraphQLUUID
from .enum import GraphQLPythonEnumType


def req(ttype: GraphQLType) -> GraphQLNonNull:
    return GraphQLNonNull(type=ttype)


def list_of(ttype: GraphQLType) -> GraphQLList:
    return GraphQLList(type=ttype)


__all__ = [
    'list_of',
    'req',
    'GraphQLDate',
    'GraphQLUUID',
    'GraphQLPythonEnumType',
    'define_default_resolver',
    'define_default_gen_resolver',
    'async_field_error_boundary',
    'define_pent_mutation_resolver',
]
