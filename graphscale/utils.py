import asyncio
import re
import sys

from . import check


def reverse_dict(dict_to_reverse):
    """Swap the keys and values of a dictionary. Duplicate values (that will become keys)
    do not cause error. One of the keys will be the new value non-deterministically
    """
    check.dict_param(dict_to_reverse, 'dict_to_reverse')
    return {v: k for k, v in dict_to_reverse.items()}


def execute_gen(gen):
    """It's useful, especially in the context of scripts and tests, so be able to
    synchronous execute async functions. This is a convenience for doing that.
    """
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(gen)
    loop.close()
    return result


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