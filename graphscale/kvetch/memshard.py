from collections import OrderedDict, defaultdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from graphscale.kvetch.kvetch import KvetchShard

from .kvetch import EdgeData, IndexDefinition, KvetchData, StoredIdEdgeDefinition, IndexEntry


class KvetchMemShard(KvetchShard):
    def __init__(self) -> None:
        self._objects = {}  # type: Dict[UUID, KvetchData]
        self._all_indexes = defaultdict(lambda: defaultdict(list)
                                        )  # type: Dict[str, Dict[str, List[Dict]]]
        self._all_edges = defaultdict(lambda: defaultdict(list)
                                      )  # type: Dict[str, Dict[UUID, List[Dict]]]

    async def gen_object(self, obj_id: UUID) -> KvetchData:
        return self._objects.get(obj_id)

    async def gen_objects(self, ids: List[UUID]) -> Dict[UUID, KvetchData]:
        return {obj_id: self._objects.get(obj_id) for obj_id in ids}

    async def gen_objects_of_type(self, type_id: int, after: UUID=None,
                                  first: int=None) -> Dict[UUID, KvetchData]:
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

    async def gen_insert_index_entry(
        self, index: IndexDefinition, index_value: Any, target_id: UUID
    ) -> None:
        index_name = index.index_name
        index_dict = self._all_indexes[index_name]
        index_entry = {'target_id': target_id, 'updated': datetime.now()}
        index_dict[index_value].append(index_entry)

    async def gen_delete_index_entry(
        self, index: IndexDefinition, index_value: Any, target_id: UUID
    ):
        index_dict = self._all_indexes[index.index_name]
        index_dict[index_value
                   ] = list(filter(lambda e: e['target_id'] != target_id, index_dict[index_value]))

    async def gen_index_entries(self, index: IndexDefinition, value: Any) -> List[IndexEntry]:
        index_name = index.index_name
        index_dict = self._all_indexes[index_name]
        entries_data = index_dict.get(value, [])
        return [IndexEntry(target_id=data['target_id']) for data in entries_data]

    async def gen_update_object(self, obj_id: UUID, data: KvetchData) -> None:

        if not obj_id in self._objects:
            return None

        obj = self._objects[obj_id]

        for key, val in data.items():
            obj[key] = val

        obj['updated'] = datetime.now()

        self._objects[obj_id] = obj

    async def gen_delete_object(self, obj_id: UUID) -> UUID:
        if obj_id in self._objects:
            del self._objects[obj_id]
        return obj_id

    async def gen_insert_object(self, new_id: UUID, type_id: int, data: KvetchData) -> UUID:
        self._objects[new_id] = {
            **{'obj_id': new_id, 'type_id': type_id, 'updated': datetime.now()},
            **data
        }
        return new_id

    async def gen_insert_objects(self, new_ids: List[UUID], type_id: int,
                                 datas: List[KvetchData]) -> List[UUID]:
        for new_id, data in zip(new_ids, datas):
            await self.gen_insert_object(new_id, type_id, data)
        return new_ids

    async def gen_insert_edge(
        self,
        edge_definition: StoredIdEdgeDefinition,
        from_id: UUID,
        to_id: UUID,
        data: KvetchData=None
    ) -> None:
        data = data or {}

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

    @staticmethod
    def __get_after_index(edges: List[Dict], after: UUID) -> int:
        for index, edge in enumerate(edges):
            if after == edge['to_id']:
                return index + 1
        return len(edges)

    async def gen_edges(
        self,
        edge_definition: StoredIdEdgeDefinition,
        from_id: UUID,
        after: UUID=None,
        first: int=None
    ) -> List[EdgeData]:

        edge_name = edge_definition.edge_name
        edges = self._all_edges[edge_name].get(from_id)

        if after:
            index = KvetchMemShard.__get_after_index(edges, after)
            edges = edges[index:]
        if first:
            edges = edges[0:first]

        return [
            EdgeData(
                from_id=obj['from_id'],
                to_id=obj['to_id'],
                created=obj['created'],
                data=obj['data']
            ) for obj in edges
        ]

    async def gen_edge_ids(
        self,
        edge_definition: StoredIdEdgeDefinition,
        from_id: UUID,
        after: UUID=None,
        first: int=None
    ) -> List[UUID]:
        edges = await self.gen_edges(edge_definition, from_id, after, first)
        return [edge.to_id for edge in edges]
