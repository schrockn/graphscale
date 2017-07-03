import asyncio
import traceback
import re
import sys
from uuid import UUID

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLID,
    GraphQLInt,
)


def reverse_dict(dict_to_reverse):
    return {v: k for k, v in dict_to_reverse.items()}


def execute_gen(gen):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(gen)
    loop.close()
    return result


def execute_sql(shard, sql):
    with shard.create_safe_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
    return sql


async def async_array(coros):
    return await asyncio.gather(*coros)


async def async_tuple(*coros):
    return tuple(await asyncio.gather(*coros))


def print_error(val):
    sys.stderr.write(str(val) + '\n')


def to_snake_case(camel_case):
    with_underscores = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', with_underscores).lower()


def is_camel_case(string):
    return re.search('[A-Z]', string)