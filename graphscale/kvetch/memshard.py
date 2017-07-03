from datetime import datetime
from uuid import UUID
from collections import OrderedDict, defaultdict

import graphscale.check as check
from graphscale.kvetch.kvetch import (
    KvetchShard,
)

from typing import Dict, List, Any


class KvetchMemShard(KvetchShard):
    def __init__(self):
        self._objects = {}
        self._all_indexes = defaultdict(lambda: defaultdict(list))
        self._all_edges = defaultdict(lambda: defaultdict(list))

    async def gen_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        return self._objects.get(obj_id)

    async def gen_objects(self, ids):
        check.param(ids, list, 'ids')
        check.param_invariant(ids, 'ids')
        return {obj_id: self._objects.get(obj_id) for obj_id in ids}

    async def gen_objects_of_type(self, type_id, after=None, first=None):
        objs = {}
        for obj_id, obj in self._objects.items():
            if obj['type_id'] == type_id:
                objs[obj_id] = obj

        tuple_list = sorted(objs.items(), key=lambda t: t[0])

        if after:
            index = 0
            for obj_id, _obj in tuple_list:
                if after >= obj_id:
                    index += 1
            tuple_list = tuple_list[index:]

        if first:
            tuple_list = tuple_list[:first]

        return OrderedDict(tuple_list)

    async def gen_insert_index_entry(self, index, index_value, target_id):
        index_name = index.index_name
        index_dict = self._all_indexes[index_name]
        index_entry = {'target_id': target_id, 'updated': datetime.now()}
        index_dict[index_value].append(index_entry)
        return index_entry

    async def gen_delete_index_entry(self, index, index_value, target_id):
        index_dict = self._all_indexes[index.index_name]
        index_dict[index_value] = filter(
            lambda e: e['target_id'] != target_id, index_dict[index_value]
        )

    async def gen_index_entries(self, index, index_value):
        index_name = index.index_name
        index_dict = self._all_indexes[index_name]
        return index_dict.get(index_value, [])

    async def gen_update_object(self, obj_id, data):
        check.param(obj_id, UUID, 'obj_id')
        check.param(data, dict, 'data')

        if not obj_id in self._objects:
            return None

        obj = self._objects[obj_id]

        for key, val in data.items():
            obj[key] = val

        obj['updated'] = datetime.now()

        self._objects[obj_id] = obj

        return obj

    async def gen_delete_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        if obj_id in self._objects:
            del self._objects[obj_id]

    async def gen_insert_object(self, new_id, type_id, data):
        self._objects[new_id] = {
            **{'obj_id': new_id, 'type_id': type_id, 'updated': datetime.now()},
            **data
        }
        return new_id

    async def gen_insert_edge(self, edge_definition, from_id, to_id, data=None):
        check.param(from_id, UUID, 'from_id')
        check.param(to_id, UUID, 'to_id')
        if data is None:
            data = {}
        check.param(data, dict, 'data')

        edge_name = edge_definition.edge_name
        now = datetime.now()
        edge_entry = {
            'edge_id': edge_definition.edge_id,
            'from_id': from_id,
            'to_id': to_id,
            'data': data,
            'created': now,
            'updated': now,
        }
        self._all_edges[edge_name][from_id].append(edge_entry)

    def get_after_index(self, edges, after):
        index = 0
        for edge in edges:
            if after == edge['to_id']:
                return index + 1
            index += 1
        return index

    async def gen_edges(self, edge_definition, from_id, after=None, first=None):
        check.param(from_id, UUID, 'from_id')
        edge_name = edge_definition.edge_name
        edges = self._all_edges[edge_name].get(from_id)

        if after:
            index = self.get_after_index(edges, after)
            edges = edges[index:]
        if first:
            edges = edges[0:first]

        return edges

    async def gen_edge_ids(self, edge_definition, from_id, after=None, first=None):
        edges = await self.gen_edges(edge_definition, from_id, after, first)
        return [edge['to_id'] for edge in edges]
