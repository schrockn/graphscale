import pytest
from graphscale.utils import reverse_dict, async_list, async_tuple, is_camel_case, to_snake_case


def test_reverse_dictionary():
    assert reverse_dict({1: '1', 2: '2'}) == {'2': 2, '1': 1}


def test_reverse_dictionary_dup_key():
    assert reverse_dict({1: '1', 2: '1'})


@pytest.mark.asyncio
async def test_async_list():
    async def gen_num(num):
        return num

    list_of_gens = [gen_num(1)]

    list_of_one = await async_list(list_of_gens)

    assert list_of_one == [1]

    list_of_two = await async_list([gen_num(1), gen_num(2)])
    assert list_of_two == [1, 2]


@pytest.mark.asyncio
async def test_async_tuple():
    async def gen_num(num):
        return num

    one, two = await async_tuple(gen_num(1), gen_num(2))

    assert one == 1
    assert two == 2

    single_result = await async_tuple(gen_num(1))

    assert single_result == (1, )

    two, one = await async_tuple(gen_num(2), gen_num(1))

    assert one == 1
    assert two == 2


def test_is_camel_case():
    assert is_camel_case('testFoo') is True
    assert is_camel_case('test_foo') is False
    assert is_camel_case('testfoo') is False


def test_to_snake_case():
    assert to_snake_case('foo') == 'foo'
    assert to_snake_case('fooBar') == 'foo_bar'
