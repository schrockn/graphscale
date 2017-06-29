import graphscale.check as check

from .kvetch import (
    Kvetch,
    Schema,
    define_schema,
    define_edge,
    define_object,
    define_string_index,
    define_int_index,
)


def init_from_conn(conn_info, schema):
    # for now handle circular dep until further refactoring
    from .kvetch_dbshard import (KvetchDbShard, KvetchDbSingleConnectionPool, ConnectionInfo)
    from .kvetch_dbschema import init_shard_db_tables

    # check.param(conn_info, ConnectionInfo, 'conn_info')
    check.param(schema, Schema, 'schema')
    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    init_shard_db_tables(shards[0], schema.indexes)
    return Kvetch.from_schema(shards=shards, schema=schema)


def hard_init_from_conn(conn_info, schema):
    # for now handle circular dep until further refactoring
    from .kvetch_dbshard import (KvetchDbShard, KvetchDbSingleConnectionPool, ConnectionInfo)
    from .kvetch_dbschema import init_shard_db_tables, drop_shard_db_tables

    # check.param(conn_info, ConnectionInfo, 'conn_info')
    check.param(schema, Schema, 'schema')
    shards = [KvetchDbShard(pool=KvetchDbSingleConnectionPool(conn_info))]
    drop_shard_db_tables(shards[0], schema.indexes)
    init_shard_db_tables(shards[0], schema.indexes)
    return Kvetch.from_schema(shards=shards, schema=schema)


def init_in_memory(schema):
    # for now handle circular dep until further refactoring
    from .kvetch_memshard import KvetchMemShard

    check.param(schema, Schema, 'schema')
    return Kvetch.from_schema(shards=[KvetchMemShard()], schema=schema)
