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


class InvariantViolation(Exception):
    pass


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


def sanitize_column_name(name):
    replace_me = {
        ' /-': '_',
        '?': '',
    }
    name = name.strip().lower()[:64]
    for (old_chars, new_char) in replace_me.items():
        for old_char in old_chars:
            name = name.replace(old_char, new_char)

    # currently if a data source has a column called row_id
    # it conflicts with the one that latus adds
    if name == 'row_id':
        return 'row_id_dup'

    return name


def sanitize_columns(original_columns):
    columns = [sanitize_column_name(original_column) for original_column in original_columns]
    column_set = set()
    for column in columns:
        if column in column_set:
            raise Exception('duplicate column {column}'.format(column=column))
        column_set.add(column)
    return columns
