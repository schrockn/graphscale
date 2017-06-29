import graphscale.check as check
from graphscale.utils import execute_gen
from graphscale.kvetch.kvetch import KvetchShard


class SyncedShard:
    def __init__(self, shard):
        check.param(shard, KvetchShard, 'shard')
        self.shard = shard

    def delete_object(self, obj_id):
        return execute_gen(self.shard.gen_delete_object(obj_id))

    def insert_object(self, new_id, type_id, data):
        return execute_gen(self.shard.gen_insert_object(new_id, type_id, data))

    def update_object(self, obj_id, data):
        return execute_gen(self.shard.gen_update_object(obj_id, data))

    def get_object(self, obj_id):
        return execute_gen(self.shard.gen_object(obj_id))

    def get_objects(self, ids):
        return execute_gen(self.shard.gen_objects(ids))

    def browse_objects(self, type_id, limit=100, offset=0):
        return execute_gen(self.shard.gen_browse_objects(type_id, limit, offset))

    def get_objects_of_type(self, type_id, after=None, first=None):
        return execute_gen(self.shard.gen_objects_of_type(type_id, after, first))

    def insert_edge(self, edge_def, from_id, to_id, data=None):
        return execute_gen(self.shard.gen_insert_edge(edge_def, from_id, to_id, data))

    def get_edge_ids(self, edge_def, from_id, after=None, first=None):
        return execute_gen(self.shard.gen_edge_ids(edge_def, from_id, after, first))

    def insert_index_entry(self, index_name, index_value, target_id):
        return execute_gen(self.shard.gen_insert_index_entry(index_name, index_value, target_id))

    def get_index_entries(self, index, index_value):
        return execute_gen(self.shard.gen_index_entries(index, index_value))

    def get_index_ids(self, index, index_value):
        entries = self.get_index_entries(index, index_value)
        return [entry['target_id'] for entry in entries]
