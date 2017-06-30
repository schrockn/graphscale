from graphql import GraphQLNonNull, GraphQLList

from .grapple_types import (
    define_default_resolver,
    define_default_gen_resolver,
    async_field_error_boundary,
    define_pent_mutation_resolver,
)

from .date import GraphQLDate
from .uuid import GraphQLUUID


def req(ttype):
    return GraphQLNonNull(type=ttype)


def list_of(ttype):
    return GraphQLList(type=ttype)


__all__ = [
    'list_of',
    'req',
    'GraphQLDate',
    'GraphQLUUID',
    'define_default_resolver',
    'define_default_gen_resolver',
    'async_field_error_boundary',
    'define_pent_mutation_resolver',
]
