import pytest
import asyncio
from aiodataloader import DataLoader

pytestmark = pytest.mark.asyncio


async def async_list(seq):
    return await asyncio.gather(*seq)


class StringLoader(DataLoader):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def batch_load_fn(self, keys):
        self.calls.append(keys)
        return [str(key) for key in keys]


async def test_aiodataloader_singleload():
    loader = StringLoader()
    promise1 = loader.load(1)

    value1 = await promise1
    assert value1 == '1'
    assert loader.calls == [[1]]


async def test_aiodataloder_manyload():
    loader = StringLoader()
    values = await loader.load_many([1, 2])
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_aiodataloader_loadparallel():
    loader = StringLoader()
    values = await asyncio.gather(loader.load(1), loader.load(2))
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_aiodataloader_asynclist():
    loader = StringLoader()
    values = await async_list([loader.load(1), loader.load(2)])
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_caching():
    loader = StringLoader()
    values = await asyncio.gather(loader.load(1), loader.load(2))
    assert values == ['1', '2']
    another_load = await loader.load(1)
    assert another_load == '1'
    assert loader.calls == [[1, 2]]
