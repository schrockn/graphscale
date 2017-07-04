from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Iterable, List, NamedTuple, Sequence
from uuid import UUID, uuid4

from graphscale.utils import async_list

KvetchData = Dict[str, Any]


class ObjectDefinition(NamedTuple):
    type_name: str
    type_id: int


class IndexType(Enum):
    STRING = auto()
    INT = auto()


class IndexDefinition(NamedTuple):
    index_name: str
    indexed_type: str
    indexed_attr: str
    index_type: IndexType


class StoredIdEdgeDefinition(NamedTuple):
    edge_name: str
    edge_id: int
    stored_id_attr: str
    stored_on_type: str


class Schema(NamedTuple):
    objects: List[ObjectDefinition]
    indexes: List[IndexDefinition]
    edges: List[StoredIdEdgeDefinition]


class EdgeData(NamedTuple):
    from_id: UUID
    to_id: UUID
    created: datetime
    data: KvetchData


class KvetchShard:
    async def gen_object(self, _obj_id: UUID) -> KvetchData:
        raise Exception('not implemented')

    async def gen_objects(self, _obj_ids: List[UUID]) -> Dict[UUID, KvetchData]:
        raise Exception('not implemented')

    async def gen_update_object(self, _obj_id: UUID, _data: KvetchData) -> KvetchData:
        raise Exception('not implemented')

    async def gen_insert_object(self, _new_id: UUID, _type_id: int, _data: KvetchData) -> UUID:
        raise Exception('not implemented')

    async def gen_insert_edge(
        self,
        _edge_definition: StoredIdEdgeDefinition,
        _from_id: UUID,
        _to_id: UUID,
        _data: KvetchData=None
    ) -> None:
        raise Exception('not implemented')

    async def gen_insert_index_entry(
        self, _index: IndexDefinition, _index_value: Any, _target_id: UUID
    ) -> None:
        raise Exception('not implemented')

    async def gen_delete_object(self, _obj_id: UUID) -> UUID:
        raise Exception('not implemented')

    async def gen_delete_index_entry(
        self, _index: IndexDefinition, _index_value: Any, _target_id: UUID
    ) -> None:
        raise Exception('not implemented')

    async def gen_insert_objects(
        self, _new_ids: List[UUID], _type_id: int, _datas: List[KvetchData]
    ) -> List[UUID]:
        raise Exception('not implemented')

    async def gen_objects_of_type(self, _type_id: int, _after: UUID=None,
                                  _first: int=None) -> Dict[UUID, KvetchData]:
        raise Exception('not implemented')

    async def gen_edges(
        self,
        _edge_definition: StoredIdEdgeDefinition,
        _from_id: UUID,
        _after: UUID=None,
        _first: int=None
    ) -> List[EdgeData]:
        raise Exception('not implemented')

    async def gen_index_entries(self, _index: IndexDefinition, _value: Any) -> List[Dict]:
        raise Exception('not implemented')


def define_string_index(
    *, index_name: str, indexed_type: str, indexed_attr: str
) -> IndexDefinition:
    return IndexDefinition(
        index_name=index_name,
        indexed_type=indexed_type,
        indexed_attr=indexed_attr,
        index_type=IndexType.STRING
    )


def define_int_index(*, index_name: str, indexed_type: str, indexed_attr: str) -> IndexDefinition:
    return IndexDefinition(
        index_name=index_name,
        indexed_type=indexed_type,
        indexed_attr=indexed_attr,
        index_type=IndexType.INT
    )


class Kvetch:
    def __init__(self, *, shards: Sequence[KvetchShard], schema: Schema) -> None:

        self._shards = shards
        # shard => shard_id
        self._shard_lookup = dict(zip(self._shards, range(0, len(shards))))
        # index_name => index
        self._index_dict = dict(zip([index.index_name for index in schema.indexes], schema.indexes))
        # edge_name => edge
        self._edge_dict = dict(zip([edge.edge_name for edge in schema.edges], schema.edges))

        self._object_dict = dict(zip([obj.type_name for obj in schema.objects], schema.objects))

    def get_index(self, index_name: str) -> IndexDefinition:
        return self._index_dict[index_name]

    def get_edge_definition_by_name(self, edge_name: str) -> StoredIdEdgeDefinition:
        return self._edge_dict[edge_name]

    def get_shard_from_obj_id(self, obj_id: UUID) -> KvetchShard:
        shard_id = self.get_shard_id_from_obj_id(obj_id)
        return self._shards[shard_id]

    def get_shard_id_from_obj_id(self, obj_id: UUID) -> int:
        # do something less stupid like consistent hashing
        # excellent description here http://michaelnielsen.org/blog/consistent-hashing/
        return obj_id.int % len(self._shards)

    async def gen_update_object(self, obj_id: UUID, data: KvetchData) -> None:

        shard = self.get_shard_from_obj_id(obj_id)
        await shard.gen_update_object(obj_id, data)

    def get_indexed_type_id(self, index: IndexDefinition) -> int:
        return self._object_dict[index.indexed_type].type_id

    def get_edge_stored_on_type_id(self, edge_definition: StoredIdEdgeDefinition) -> int:
        return self._object_dict[edge_definition.stored_on_type].type_id

    def iterate_applicable_indexes(self, type_id: int,
                                   data: KvetchData) -> Iterable[IndexDefinition]:
        for index in self._index_dict.values():
            if self.get_indexed_type_id(index) != type_id:
                continue

            attr = index.indexed_attr
            if not (attr in data) or not data[attr]:
                continue
            yield index

    async def gen_delete_object(self, obj_id: UUID) -> UUID:
        shard = self.get_shard_from_obj_id(obj_id)

        obj = await shard.gen_object(obj_id)

        type_id = obj['type_id']

        await shard.gen_delete_object(obj_id)

        # do edges

        for index in self.iterate_applicable_indexes(type_id, obj):
            indexed_value = obj[index.indexed_attr]
            indexed_shard = self.get_shard_from_obj_id(obj_id)
            await indexed_shard.gen_delete_index_entry(index, indexed_value, obj_id)

        return obj_id

    async def gen_insert_object(self, type_id: int, data: KvetchData) -> UUID:
        new_id = uuid4()
        shard = self.get_shard_from_obj_id(new_id)
        await shard.gen_insert_object(new_id, type_id, data)

        for edge_definition in self._edge_dict.values():
            attr = edge_definition.stored_id_attr
            if self.get_edge_stored_on_type_id(edge_definition) != type_id:
                continue
            if not (attr in data) or not data[attr]:
                continue

            from_id = data[attr]
            from_id_shard = self.get_shard_from_obj_id(from_id)
            await from_id_shard.gen_insert_edge(edge_definition, from_id, new_id, {})

        for index in self.iterate_applicable_indexes(type_id, data):
            indexed_value = data[index.indexed_attr]
            indexed_shard = self.get_shard_from_obj_id(new_id)
            await indexed_shard.gen_insert_index_entry(index, indexed_value, new_id)

        return new_id

    async def gen_insert_objects(self, type_id: int, datas: List[KvetchData]) -> List[UUID]:
        if len(self._shards) > 1:
            raise Exception('shards > 1 currently not supported')

        shard = self._shards[0]

        new_ids = []
        for _ in range(0, len(datas)):
            new_ids.append(uuid4())

        await shard.gen_insert_objects(new_ids, type_id, datas)
        return new_ids

    async def gen_object(self, obj_id: UUID) -> KvetchData:
        shard = self.get_shard_from_obj_id(obj_id)
        return await shard.gen_object(obj_id)

    async def gen_objects(self, obj_ids: List[UUID]) -> Dict[UUID, KvetchData]:
        # construct dictionary of shard_id to all ids in that shard
        shard_to_ids = {}  # type: Dict[int, List[UUID]]
        for obj_id in obj_ids:
            shard_id = self.get_shard_id_from_obj_id(obj_id)
            if not shard_id in shard_to_ids:
                shard_to_ids[shard_id] = []
            shard_to_ids[shard_id].append(obj_id)

        # construct list of coros (one per shard) in order to fetch in parallel
        unawaited_gens = []
        for shard_id, ids_in_shard in shard_to_ids.items():
            shard = self._shards[shard_id]
            unawaited_gens.append(shard.gen_objects(ids_in_shard))

        obj_dict_per_shard = await async_list(unawaited_gens)

        # flatten results into single dict
        results = {}
        for obj_dict in obj_dict_per_shard:
            for obj_id, obj in obj_dict.items():
                results[obj_id] = obj
        return results

    async def gen_objects_of_type(self, type_id: int, after: UUID=None,
                                  first: int=None) -> Dict[UUID, KvetchData]:
        if len(self._shards) > 1:
            raise Exception('shards > 1 currently not supported')

        shard = self._shards[0]
        return await shard.gen_objects_of_type(type_id, after, first)

    async def gen_edges(
        self,
        edge_definition: StoredIdEdgeDefinition,
        from_id: UUID,
        after: UUID=None,
        first: int=None
    ) -> List[EdgeData]:
        shard = self.get_shard_from_obj_id(from_id)
        return await shard.gen_edges(edge_definition, from_id, after, first)

    async def gen_from_index(self, index: IndexDefinition,
                             index_value: Any) -> Dict[UUID, KvetchData]:
        obj_ids = []
        for shard in self._shards:
            index_entries = await shard.gen_index_entries(index, index_value)
            obj_ids.extend([entry['target_id'] for entry in index_entries])

        return await self.gen_objects(obj_ids)

    async def gen_id_from_index(self, index_name: str, index_value: Any) -> UUID:
        index = self.get_index(index_name)
        obj_ids = await self.gen_ids_from_index(index, index_value)
        if not obj_ids:
            return None

        return obj_ids[0]

    async def gen_ids_from_index(self, index: IndexDefinition, index_value: Any) -> List[UUID]:
        obj_ids = []
        for shard in self._shards:
            index_entries = await shard.gen_index_entries(index, index_value)
            obj_ids.extend([entry['target_id'] for entry in index_entries])
        return obj_ids
