from graphscale import check
from graphscale.sql import ConnectionInfo

from .kvetch import Kvetch, Schema
from .dbshard import KvetchDbShard, KvetchDbSingleConnectionPool, ConnectionInfo
from .dbschema import init_shard_db_tables, drop_shard_db_tables
from .memshard import KvetchMemShard


def init_from_conn(conn_info, schema):
    check.param(conn_info, ConnectionInfo, 'conn_info')
    check.param(schema, Schema, 'schema')

    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    init_shard_db_tables(shards[0], schema.indexes)
    return Kvetch.from_schema(shards=shards, schema=schema)


def nuke_conn(conn_info, schema):
    check.param(conn_info, ConnectionInfo, 'conn_info')
    check.param(schema, Schema, 'schema')
    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    drop_shard_db_tables(shards[0], schema.indexes)
    init_shard_db_tables(shards[0], schema.indexes)


def init_in_memory(schema):
    check.param(schema, Schema, 'schema')
    return Kvetch.from_schema(shards=[KvetchMemShard()], schema=schema)
