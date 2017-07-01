from collections import namedtuple
from uuid import UUID, uuid4
from enum import Enum, auto

import graphscale.check as check
from graphscale.utils import async_array, print_error


class KvetchShard:
    def check_insert_object_vars(self, new_id, type_id, data):
        check.param(new_id, UUID, 'new_id')
        check.param(type_id, int, 'type_id')
        check.param(data, dict, 'data')
        check.param_violation('obj_id' in data, 'data')
        check.param_violation('type_id' in data, 'data')


ObjectTypeDefinition = namedtuple('ObjectTypeDefinition', 'type_name type_id')


class IndexType(Enum):
    STRING = auto()
    INT = auto()


IndexDefinition = namedtuple('IndexDefinition', 'index_name indexed_type indexed_attr index_type')

StoredIdEdgeDefinition = namedtuple(
    'EdgeDefinition',
    'edge_name edge_id, from_id_attr',
)

Schema = namedtuple('Schema', 'objects indexes edges')


def define_object(*, type_name, type_id):
    check.str_param(type_name, 'type_name')
    check.int_param(type_id, 'type_id')
    return ObjectTypeDefinition(type_name, type_id)


def define_schema(*, objects=None, indexes, edges):
    if not objects:
        objects = []
    check.list_param(objects, 'objects')
    check.list_param(indexes, 'indexes')
    check.list_param(edges, 'edges')
    return Schema(objects, indexes, edges)


def define_string_index(*, index_name, indexed_type, indexed_attr):
    check.str_param(index_name, 'index_name')
    check.str_param(indexed_type, 'indexed_type')
    check.str_param(indexed_attr, 'indexed_attr')

    return IndexDefinition(
        index_name=index_name,
        indexed_type=indexed_type,
        indexed_attr=indexed_attr,
        index_type=IndexType.STRING
    )


def define_int_index(*, index_name, indexed_type, indexed_attr):
    check.str_param(index_name, 'index_name')
    check.str_param(indexed_type, 'indexed_type')
    check.str_param(indexed_attr, 'indexed_attr')

    return IndexDefinition(
        index_name=index_name,
        indexed_type=indexed_type,
        indexed_attr=indexed_attr,
        index_type=IndexType.INT
    )


def define_stored_id_edge(*, edge_name, edge_id, from_id_attr):
    check.str_param(edge_name, 'edge_name')
    check.int_param(edge_id, 'edge_id')
    check.str_param(from_id_attr, 'from_id_attr')
    return StoredIdEdgeDefinition(edge_name, edge_id, from_id_attr)


class Kvetch:
    @staticmethod
    def from_schema(shards, schema):
        check.param(schema, Schema, 'schema')
        return Kvetch(
            shards=shards, edges=schema.edges, indexes=schema.indexes, objects=schema.objects
        )

    def __init__(self, *, shards, edges, indexes, objects=None):
        if not objects:
            objects = []
        check.param(shards, list, 'shards')
        check.param(edges, list, 'edges')
        check.param(indexes, list, 'indexes')

        self._shards = shards
        # shard => shard_id
        self._shard_lookup = dict(zip(self._shards, range(0, len(shards))))
        # index_name => index
        self._index_dict = dict(zip([index.index_name for index in indexes], indexes))
        # edge_name => edge
        self._edge_dict = dict(zip([edge.edge_name for edge in edges], edges))

        self._object_dict = dict(zip([obj.type_name for obj in objects], objects))

    def get_index(self, index_name):
        check.param(index_name, str, 'index_name')
        return self._index_dict[index_name]

    def get_edge_definition_by_name(self, edge_name):
        for edge in self._edge_dict.values():
            if edge.edge_name == edge_name:
                return edge
        raise Exception('edge %s not found in Kvetch' % edge_name)

    def get_shards(self):
        return self._shards

    def get_shard_from_obj_id(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        shard_id = self.get_shard_id_from_obj_id(obj_id)
        return self._shards[shard_id]

    def get_shard_id_from_obj_id(self, obj_id):
        # do something less stupid like consistent hashing
        # excellent description here http://michaelnielsen.org/blog/consistent-hashing/
        check.param(obj_id, UUID, 'obj_id')
        return int(obj_id) % len(self._shards)

    async def gen_update_object(self, obj_id, data):
        check.param(obj_id, UUID, 'obj_id')
        check.param(data, dict, 'data')

        shard = self.get_shard_from_obj_id(obj_id)
        return await shard.gen_update_object(obj_id, data)

    def get_indexed_type_id(self, index):
        check.param(index, IndexDefinition, 'index')
        type_id = self._object_dict[index.indexed_type].type_id
        return type_id

    def iterate_applicable_indexes(self, type_id, data):
        for index in self._index_dict.values():
            if self.get_indexed_type_id(index) != type_id:
                continue

            attr = index.indexed_attr
            if not (attr in data) or not data[attr]:
                continue
            yield index

    async def gen_delete_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
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

    async def gen_insert_object(self, type_id, data):
        check.param(type_id, int, 'type_id')
        check.param(data, dict, 'data')

        new_id = uuid4()
        shard = self.get_shard_from_obj_id(new_id)
        await shard.gen_insert_object(new_id, type_id, data)

        for edge_definition in self._edge_dict.values():
            attr = edge_definition.from_id_attr
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

    async def gen_insert_objects(self, type_id, datas):
        check.param(datas, list, 'datas')
        if len(self._shards) > 1:
            raise Exception('shards > 1 currently not supported')

        shard = self._shards[0]

        new_ids = []
        for _ in range(0, len(datas)):
            new_ids.append(uuid4())

        await shard.gen_insert_objects(new_ids, type_id, datas)
        return new_ids

    async def gen_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        shard = self.get_shard_from_obj_id(obj_id)
        return await shard.gen_object(obj_id)

    async def gen_objects(self, ids):
        # construct dictionary of shard_id to all ids in that shard
        shard_to_ids = {}  # shard_id => [id]
        for obj_id in ids:
            shard_id = self.get_shard_id_from_obj_id(obj_id)
            if not shard_id in shard_to_ids:
                shard_to_ids[shard_id] = []
            shard_to_ids[shard_id].append(obj_id)

        # construct list of coros (one per shard) in order to fetch in parallel
        unawaited_gens = []
        for shard_id, ids_in_shard in shard_to_ids.items():
            shard = self._shards[shard_id]
            unawaited_gens.append(shard.gen_objects(ids_in_shard))

        obj_dict_per_shard = await async_array(unawaited_gens)

        # flatten results into single dict
        results = {}
        for obj_dict in obj_dict_per_shard:
            for obj_id, obj in obj_dict.items():
                results[obj_id] = obj
        return results

    async def gen_objects_of_type(self, type_id, after=None, first=None):
        if len(self._shards) > 1:
            raise Exception('shards > 1 currently not supported')

        shard = self._shards[0]
        return await shard.gen_objects_of_type(type_id, after, first)

    async def gen_edges(self, edge_definition, from_id, after=None, first=None):
        check.uuid_param(from_id, 'from_id')
        shard = self.get_shard_from_obj_id(from_id)
        return await shard.gen_edges(edge_definition, from_id, after=after, first=first)

    async def gen_from_index(self, index, index_value):
        ids = []
        for shard in self._shards:
            index_entries = await shard.gen_index_entries(index, index_value)
            ids.extend([entry['target_id'] for entry in index_entries])

        return await self.gen_objects(ids)

    async def gen_id_from_index(self, index_name, index_value):
        index = self.get_index(index_name)
        ids = await self.gen_ids_from_index(index, index_value)
        if not ids:
            return None

        return ids[0]

    async def gen_ids_from_index(self, index, index_value):
        ids = []
        for shard in self._shards:
            index_entries = await shard.gen_index_entries(index, index_value)
            ids.extend([entry['target_id'] for entry in index_entries])
        return ids
