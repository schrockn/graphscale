import datetime
import iso8601
from graphql.language.ast import StringValue
from graphql import GraphQLScalarType


def serialize_date(date):
    return date.isoformat()


def coerce_date(value):
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return datetime.date(value.year, value.month.value.day)
    if isinstance(value, str):
        return iso8601.parse_date(value)  # let's see what we can do
    return None  # should I throw?


def parse_date_literal(ast):
    if isinstance(ast, StringValue):
        return iso8601.parse_date(ast.value)


GraphQLDate = GraphQLScalarType(
    name='Date',
    description='ISO-8601 Date',
    serialize=serialize_date,
    parse_value=coerce_date,
    parse_literal=parse_date_literal,
)