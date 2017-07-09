from typing import NamedTuple

import pymysql
import pymysql.cursors


class ConnectionInfo(NamedTuple):
    host: str
    user: str
    password: str
    db: str
    charset: str = 'utf8mb4'


def pymysql_conn_from_info(conn_info: ConnectionInfo) -> pymysql.Connection:
    return pymysql.connect(
        host=conn_info.host,
        user=conn_info.user,
        password=conn_info.password,
        db=conn_info.db,
        charset=conn_info.charset,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
