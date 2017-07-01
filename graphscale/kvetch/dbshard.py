from collections import OrderedDict, namedtuple
from contextlib import contextmanager
from datetime import datetime
from uuid import UUID

import graphscale.check as check
from graphscale.kvetch.kvetch import KvetchShard
from graphscale.sql import ConnectionInfo, pymysql_conn_from_info

from .kvetch_utils import body_to_data, data_to_body, row_to_obj


class KvetchDbSingleConnectionPool:
    def __init__(self, conn_info):
        check.param(conn_info, ConnectionInfo, 'conn_info')
        self._conn_info = conn_info

    def conn_info(self):
        return self._conn_info

    @contextmanager
    def create_safe_conn(self):
        conn = pymysql_conn_from_info(self._conn_info)
        yield conn
        conn.close()


class KvetchDbShard(KvetchShard):
    def __init__(self, *, pool):
        self._pool = pool

    def create_safe_conn(self):
        return self._pool.create_safe_conn()

    async def gen_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        with self.create_safe_conn() as conn:
            return _kv_shard_get_object(conn, obj_id)

    async def gen_objects(self, ids):
        check.param(ids, list, 'ids')
        check.param_invariant(ids, 'ids must have at least 1 element')
        with self.create_safe_conn() as conn:
            return _kv_shard_get_objects(conn, ids)

    async def gen_browse_objects(self, type_id, limit=100, offset=0):
        check.int_param(type_id, 'type_id')
        check.int_param(limit, 'limit')
        check.int_param(offset, 'offset')

    async def gen_objects_of_type(self, type_id, after=None, first=None):
        check.param(type_id, int, 'type_id')
        with self.create_safe_conn() as conn:
            return _kv_shard_get_objects_by_type(conn, type_id, after, first)

    async def gen_insert_index_entry(self, index, index_value, target_id):
        attr = index.indexed_attr
        with self.create_safe_conn() as conn:
            _kv_shard_insert_index_entry(
                shard_conn=conn,
                index_name=index.index_name,
                index_column=attr,
                index_value=index_value,
                target_id=target_id,
            )

    async def gen_delete_index_entry(self, index, index_value, target_id):
        attr = index.indexed_attr
        with self.create_safe_conn() as conn:
            _kv_shard_delete_index_entry(
                shard_conn=conn,
                index_name=index.index_name,
                index_column=attr,
                index_value=index_value,
                target_id=target_id,
            )

    async def gen_insert_edge(self, edge_definition, from_id, to_id, data=None):
        check.param(from_id, UUID, 'from_id')
        check.param(to_id, UUID, 'to_id')
        if data is None:
            data = {}
        check.param(data, dict, 'data')
        with self.create_safe_conn() as conn:
            _kv_shard_insert_edge(conn, edge_definition.edge_id, from_id, to_id, data)

    async def gen_insert_object(self, new_id, type_id, data):
        self.check_insert_object_vars(new_id, type_id, data)
        with self.create_safe_conn() as conn:
            _kv_shard_insert_object(conn, new_id, type_id, data)
        return new_id

    async def gen_insert_objects(self, new_ids, type_id, datas):
        with self.create_safe_conn() as conn:
            _kv_shard_insert_objects(conn, new_ids, type_id, datas)
        return new_ids

    async def gen_update_object(self, obj_id, data):
        check.param(obj_id, UUID, 'obj_id')
        check.param(data, dict, 'data')
        old_object = await self.gen_object(obj_id)
        for key, val in data.items():
            old_object[key] = val
        with self.create_safe_conn() as conn:
            _kv_shard_replace_object(conn, obj_id, old_object)

    async def gen_delete_object(self, obj_id):
        check.param(obj_id, UUID, 'obj_id')
        with self.create_safe_conn() as conn:
            _kv_shard_delete_object(conn, obj_id)

    async def gen_edges(self, edge_definition, from_id, after=None, first=None):
        check.opt_param(from_id, UUID, 'from_id')
        with self.create_safe_conn() as conn:
            return _kv_shard_get_edges(conn, edge_definition.edge_id, from_id, after, first)

    async def gen_edge_ids(self, edge_definition, from_id, after=None, first=None):
        edges = await self.gen_edges(edge_definition, from_id, after, first)
        return [edge['to_id'] for edge in edges]

    async def gen_index_entries(self, index, value):
        with self.create_safe_conn() as conn:
            return _kv_shard_get_index_entries(
                shard_conn=conn,
                index_name=index.index_name,
                index_column=index.indexed_attr,
                index_value=value
            )


def _kv_shard_get_objects_by_type(shard_conn, type_id, after=None, first=None):
    sqls = ['SELECT obj_id, type_id, body FROM kvetch_objects WHERE type_id = %s']

    params = [type_id]

    if after:
        sqls.append(' AND obj_id > %s')
        params.append(after.bytes)

    sqls.append(' ORDER BY obj_id')

    if first:
        sqls.append(' LIMIT %s')
        params.append(first)

    with shard_conn.cursor() as cursor:
        cursor.execute(''.join(sqls), tuple(params))
        rows = cursor.fetchall()

    ids_out = [UUID(bytes=row['obj_id']) for row in rows]
    obj_list = [row_to_obj(row) for row in rows]
    return OrderedDict(zip(ids_out, obj_list))


def _kv_shard_get_object(shard_conn, obj_id):
    obj_dict = _kv_shard_get_objects(shard_conn, [obj_id])
    return obj_dict.get(obj_id)


def _kv_shard_get_objects(shard_conn, ids):
    values_sql = ', '.join(['%s' for x in range(0, len(ids))])
    sql = 'SELECT obj_id, type_id, body FROM kvetch_objects WHERE obj_id in (' + values_sql + ')'

    with shard_conn.cursor() as cursor:
        cursor.execute(sql, [obj_id.bytes for obj_id in ids])
        rows = cursor.fetchall()

    out_dict = OrderedDict.fromkeys(ids, None)
    for row in rows:
        obj_id = UUID(bytes=row['obj_id'])
        out_dict[obj_id] = row_to_obj(row)
    return out_dict


def _kv_shard_insert_object(shard_conn, new_id, type_id, data):
    with shard_conn.cursor() as cursor:
        now = datetime.now()
        sql = (
            'INSERT INTO kvetch_objects(obj_id, type_id, created, updated, body) ' +
            'VALUES (%s, %s, %s, %s, %s)'
        )
        cursor.execute(sql, (new_id.bytes, type_id, now, now, data_to_body(data)))

    return new_id


def _kv_shard_insert_objects(shard_conn, new_ids, type_id, datas):
    assert len(new_ids) == len(datas)
    insert_tuples = []
    now = datetime.now()
    sql = (
        'INSERT INTO kvetch_objects(obj_id, type_id, created, updated, body) ' +
        'VALUES (%s, %s, %s, %s, %s)'
    )
    for new_id, data in zip(new_ids, datas):
        insert_tuples.append((new_id.bytes, type_id, now, now, data_to_body(data)))

    with shard_conn.cursor() as cursor:
        cursor.executemany(sql, insert_tuples)
    return new_ids


def _kv_shard_replace_object(shard_conn, obj_id, data):
    sql = 'UPDATE kvetch_objects SET body = %s, updated = %s WHERE obj_id = %s'
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, (data_to_body(data), datetime.now(), obj_id.bytes))


def _kv_shard_delete_object(shard_conn, obj_id):
    sql = 'DELETE FROM kvetch_objects WHERE obj_id = %s'
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, (obj_id.bytes))


def _to_sql_value(value):
    direct_types = (datetime, int, str)
    if isinstance(value, UUID):
        return value.bytes
    if isinstance(value, direct_types):
        return value
    raise Exception('type not supported yet: ' + str(type(value)))


def _kv_shard_insert_index_entry(shard_conn, index_name, index_column, index_value, target_id):
    sql = 'INSERT INTO %s (%s, target_id, created)' % (index_name, index_column)
    sql += ' VALUES(%s, %s, %s)'
    values = [index_value, target_id, datetime.now()]
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, tuple(_to_sql_value(v) for v in values))


def _kv_shard_delete_index_entry(shard_conn, index_name, index_column, index_value, target_id):

    sql = 'DELETE FROM {index_table} WHERE {index_column} = %s AND target_id = %s'.format(
        index_table=index_name,
        index_column=index_column,
    )

    args = [_to_sql_value(index_value), _to_sql_value(target_id)]
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, args)


def _kv_shard_insert_edge(shard_conn, edge_id, from_id, to_id, data):
    now = datetime.now()
    sql = 'INSERT into kvetch_edges (edge_id, from_id, to_id, body, created, updated) '
    sql += 'VALUES(%s, %s, %s, %s, %s, %s)'
    values = (edge_id, from_id.bytes, to_id.bytes, data_to_body(data), now, now)
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, values)


def _kv_shard_get_edges(shard_conn, edge_id, from_id, after, first):
    sql = 'SELECT from_id, to_id, created, body '
    sql += 'FROM kvetch_edges WHERE edge_id = %s AND from_id = %s'
    args = [edge_id, from_id.bytes]
    if after:
        sql += """AND row_id >
        (SELECT row_id from kvetch_edges WHERE edge_id = %s
        AND from_id = %s
        AND to_id = %s) """
        args.extend([edge_id, from_id.bytes, after.bytes])
    sql += ' ORDER BY row_id'
    if first:
        sql += ' LIMIT %s' % first

    with shard_conn.cursor() as cursor:
        cursor.execute(sql, tuple(args))
        rows = cursor.fetchall()

    def edge_from_row(row):
        return {
            'from_id': UUID(bytes=row['from_id']),
            'to_id': UUID(bytes=row['to_id']),
            'created': row['created'],
            'data': body_to_data(row['body'])
        }

    return [edge_from_row(row) for row in rows]


def _kv_shard_get_index_entries(shard_conn, index_name, index_column, index_value):
    sql = 'SELECT target_id FROM %s WHERE %s = ' % (index_name, index_column)
    sql += '%s'
    sql += ' ORDER BY target_id'
    rows = []
    with shard_conn.cursor() as cursor:
        cursor.execute(sql, (_to_sql_value(index_value)))
        rows = cursor.fetchall()

    for row in rows:
        row['target_id'] = UUID(bytes=row['target_id'])
    return rows
