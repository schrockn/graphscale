from typing import List
import pytest
import asyncio
from aiodataloader import DataLoader

from graphscale.utils import async_list

pytestmark = pytest.mark.asyncio


class StringLoader(DataLoader):
    def __init__(self) -> None:
        super().__init__(batch_load_fn=self._batch_load_fn)
        self.calls = []  # type: List[List[int]]

    async def _batch_load_fn(self, keys: List[int]) -> List[str]:
        self.calls.append(keys)
        return [str(key) for key in keys]


async def test_aiodataloader_singleload() -> None:
    loader = StringLoader()
    promise1 = loader.load(1)

    value1 = await promise1
    assert value1 == '1'
    assert loader.calls == [[1]]


async def test_aiodataloder_manyload() -> None:
    loader = StringLoader()
    values = await loader.load_many([1, 2])
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_aiodataloader_loadparallel() -> None:
    loader = StringLoader()
    values = await asyncio.gather(loader.load(1), loader.load(2))
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_aiodataloader_asynclist() -> None:
    loader = StringLoader()
    values = await async_list([loader.load(1), loader.load(2)])
    assert values == ['1', '2']
    assert loader.calls == [[1, 2]]


async def test_caching() -> None:
    loader = StringLoader()
    values = await asyncio.gather(loader.load(1), loader.load(2))
    assert values == ['1', '2']
    another_load = await loader.load(1)
    assert another_load == '1'
    assert loader.calls == [[1, 2]]
