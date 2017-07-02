from warnings import filterwarnings, resetwarnings
import contextlib
import pymysql

import graphscale.check as check
from graphscale.utils import execute_sql, execute_gen
from .kvetch import IndexDefinition, IndexType


def create_kvetch_objects_table_sql():
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


def create_kvetch_index_table_sql(index_column, index_sql_type, target_column, index_name):
    check.param(index_column, str, 'index_column')
    check.param(target_column, str, 'target_column')
    check.param(index_name, str, 'index_name')

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


def create_kvetch_edge_table_sql():
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


@contextlib.contextmanager
def disable_pymysql_warnings():
    filterwarnings('ignore', category=pymysql.Warning)
    yield
    resetwarnings()


def create_kvetch_objects_table(shard):
    with disable_pymysql_warnings():
        execute_sql(shard, create_kvetch_objects_table_sql())


def create_kvetch_edges_table(shard):
    with disable_pymysql_warnings():
        execute_sql(shard, create_kvetch_edge_table_sql())


def create_kvetch_index_table(shard, shard_index):
    check.param(shard_index, IndexDefinition, 'shard_index')

    mapping = {
        IndexType.STRING: 'VARCHAR(512)',
        IndexType.INT: 'INT',
    }
    sql_type = mapping[shard_index.index_type]

    sql = create_kvetch_index_table_sql(
        shard_index.indexed_attr, sql_type, 'target_id', shard_index.index_name
    )
    with disable_pymysql_warnings():
        execute_sql(shard, sql)


def init_shard_db_tables(shard, indexes):
    check.param(indexes, list, 'indexes')
    create_kvetch_objects_table(shard)
    create_kvetch_edges_table(shard)
    for shard_index in indexes:
        create_kvetch_index_table(shard, shard_index)


def drop_shard_db_tables(shard, indexes):
    check.param(indexes, list, 'indexes')
    with disable_pymysql_warnings():
        execute_sql(shard, 'DROP TABLE IF EXISTS kvetch_objects')
        execute_sql(shard, 'DROP TABLE IF EXISTS kvetch_edges')
        for shard_index in indexes:
            execute_sql(shard, 'DROP TABLE IF EXISTS %s' % shard_index.index_name)


def build_index(shard, index):
    create_kvetch_index_table(shard, index)
    objects = execute_gen(shard.gen_objects_of_type(index.indexed_type_id))
    attr = index.indexed_attr
    for obj_id, obj in objects.items():
        if attr in obj:
            execute_gen(shard.gen_insert_index_entry(index, obj[attr], obj_id))
