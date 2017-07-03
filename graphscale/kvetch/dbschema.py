import contextlib
from typing import Iterator, List
from warnings import filterwarnings, resetwarnings

import pymysql

from .dbshard import KvetchDbShard
from .kvetch import IndexDefinition, IndexType


@contextlib.contextmanager
def disable_pymysql_warnings() -> Iterator:
    filterwarnings('ignore', category=pymysql.Warning)  # type: ignore
    yield
    resetwarnings()


def execute_ddl(shard: KvetchDbShard, ddl: str) -> str:
    with disable_pymysql_warnings():
        with shard.create_safe_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
    return ddl


def create_kvetch_objects_table_sql() -> str:
    return """CREATE TABLE IF NOT EXISTS kvetch_objects (
    row_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    obj_id BINARY(16) NOT NULL,
    type_id INT NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL,
    body MEDIUMBLOB,
    UNIQUE KEY (obj_id),
    UNIQUE KEY (type_id, obj_id),
    KEY (updated)
) ENGINE=InnoDB;
"""


def create_kvetch_index_table_sql(
    index_column: str, index_sql_type: str, target_column: str, index_name: str
) -> str:

    # something is up here. the two indexing keys (not updated) should be unique
    return """CREATE TABLE IF NOT EXISTS %s (
    row_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    %s %s NOT NULL,
    %s BINARY(16) NOT NULL,
    created DATETIME NOT NULL,
    KEY (%s, %s),
    KEY (%s, %s),
    KEY (created)
) ENGINE=InnoDB;
""" % (
        index_name, index_column, index_sql_type, target_column, index_column, target_column,
        target_column, index_column
    )


def create_kvetch_edge_table_sql() -> str:
    return """CREATE TABLE IF NOT EXISTS kvetch_edges (
    row_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    edge_id INT NOT NULL,
    from_id BINARY(16) NOT NULL,
    to_id BINARY(16) NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL,
    body MEDIUMBLOB,
    UNIQUE KEY(edge_id, from_id, to_id),
    UNIQUE KEY(edge_id, from_id, row_id),
    KEY(updated)
) ENGINE=InnoDB;
"""


def create_kvetch_objects_table(shard: KvetchDbShard) -> None:
    execute_ddl(shard, create_kvetch_objects_table_sql())


def create_kvetch_edges_table(shard: KvetchDbShard) -> None:
    execute_ddl(shard, create_kvetch_edge_table_sql())


def create_kvetch_index_table(shard: KvetchDbShard, shard_index: IndexDefinition):
    mapping = {
        IndexType.STRING: 'VARCHAR(512)',
        IndexType.INT: 'INT',
    }
    sql_type = mapping[shard_index.index_type]

    sql = create_kvetch_index_table_sql(
        shard_index.indexed_attr, sql_type, 'target_id', shard_index.index_name
    )
    execute_ddl(shard, sql)


def init_shard_db_tables(shard: KvetchDbShard, indexes: List[IndexDefinition]):
    create_kvetch_objects_table(shard)
    create_kvetch_edges_table(shard)
    for shard_index in indexes:
        create_kvetch_index_table(shard, shard_index)


def drop_shard_db_tables(shard: KvetchDbShard, indexes: List[IndexDefinition]):
    execute_ddl(shard, 'DROP TABLE IF EXISTS kvetch_objects')
    execute_ddl(shard, 'DROP TABLE IF EXISTS kvetch_edges')
    for shard_index in indexes:
        execute_ddl(shard, 'DROP TABLE IF EXISTS %s' % shard_index.index_name)
