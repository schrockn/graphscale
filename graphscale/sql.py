from collections import namedtuple
import pymysql
import pymysql.cursors

from graphscale import check

ConnectionInfo = namedtuple('ConnectionInfo', 'host user password db charset cursorclass')


def create_conn_info(
    *, host, user, password, db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
):
    check.str_param(host, 'host')
    check.str_param(user, 'user')
    check.str_param(password, 'password')
    check.str_param(db, 'db')
    check.str_param(charset, 'charset')

    return ConnectionInfo(
        host=host, user=user, password=password, db=db, charset=charset, cursorclass=cursorclass
    )


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
