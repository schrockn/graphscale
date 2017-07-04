import datetime
from typing import Any, cast, Optional
import iso8601

from graphql.language.ast import StringValue, Value
from graphql import GraphQLScalarType


def typed_parse_date(value: Any) -> datetime.datetime:
    return cast(datetime.datetime, iso8601.parse_date(value))


def serialize_date(value: datetime.datetime) -> str:
    return value.isoformat()


def coerce_date(value: Any) -> Optional[datetime.datetime]:
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        return typed_parse_date(value)  # let's see what we can do
    return None  # should I throw?


def parse_date_literal(ast: Value) -> Optional[datetime.datetime]:
    if isinstance(ast, StringValue):
        return typed_parse_date(ast.value)
    return None


GraphQLDate = GraphQLScalarType(
    name='Date',
    description='ISO-8601 Date',
    serialize=serialize_date,
    parse_value=coerce_date,
    parse_literal=parse_date_literal,
)