from graphscale.sql import ConnectionInfo

from .kvetch import Kvetch, Schema
from .dbshard import KvetchDbShard, KvetchDbSingleConnectionPool, ConnectionInfo
from .dbschema import init_shard_db_tables, drop_shard_db_tables
from .memshard import KvetchMemShard


def init_from_conn(conn_info: ConnectionInfo, schema: Schema) -> Kvetch:
    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    init_shard_db_tables(shards[0], schema.indexes)
    return Kvetch(shards=shards, schema=schema)


def nuke_conn(conn_info: ConnectionInfo, schema: Schema) -> None:
    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    drop_shard_db_tables(shards[0], schema.indexes)
    init_shard_db_tables(shards[0], schema.indexes)


def init_in_memory(schema: Schema) -> Kvetch:
    return Kvetch(shards=[KvetchMemShard()], schema=schema)
