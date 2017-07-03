import asyncio
import re
import sys
from typing import Dict, TypeVar, Awaitable, List, Tuple, Any

K = TypeVar('K')
V = TypeVar('V')


def reverse_dict(dict_to_reverse: Dict[K, V]) -> Dict[V, K]:
    """Swap the keys and values of a dictionary. Duplicate values (that will become keys)
    do not cause error. One of the keys will be the new value non-deterministically
    """
    return {v: k for k, v in dict_to_reverse.items()}


T = TypeVar('T')


def execute_gen(gen: Awaitable[T]) -> T:
    """It's useful, especially in the context of scripts and tests, so be able to
    synchronous execute async functions. This is a convenience for doing that.
    """
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(gen)
    loop.close()
    return result


async def async_list(coros: List[Awaitable[T]]) -> List[T]:
    """Use to await a list and return a list.
    Example: list_of_results = await async_list(list_of_gens)
    """
    return await asyncio.gather(*coros)


async def async_tuple(*coros: Awaitable) -> Tuple[Any, ...]:
    """Await on a parameters and get a tuple back.
    Example: result_one, result_two = await async_tuple(gen_one(), gen_two())
    """
    return tuple(await asyncio.gather(*coros))


def print_error(val: Any) -> None:
    """Print value to stderr"""
    sys.stderr.write(str(val) + '\n')


def to_snake_case(camel_case: str) -> str:
    """Convert a camel case string to snake case. e.g. fooBar ==> foo_bar"""
    with_underscores = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', with_underscores).lower()


def is_camel_case(string: str) -> bool:
    """Is the string potentially camel case? Only checks for capital letters currently"""
    return bool(re.search('[A-Z]', string))