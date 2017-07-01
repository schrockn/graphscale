from collections import namedtuple
import pymysql
from graphscale import check

ConnectionInfo = namedtuple('ConnectionInfo', 'host user password db charset cursorclass')


def pymysql_conn_from_info(conn_info):
    check.param(conn_info, ConnectionInfo, 'conn_info')
    return pymysql.connect(
        host=conn_info.host,
        user=conn_info.user,
        password=conn_info.password,
        db=conn_info.db,
        charset=conn_info.charset,
        cursorclass=conn_info.cursorclass,
        autocommit=True,
    )
