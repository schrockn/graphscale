import traceback
from typing import Callable, List, Dict, Any

import pymysql
import pymysql.cursors
from graphql import GraphQLSchema, graphql

from graphscale import check
from graphscale.pent import PentContext, PentContextfulObject
from graphscale.sql import ConnectionInfo, pymysql_conn_from_info
from graphscale.utils import print_error


class MagnusConn:
    is_up = None

    @staticmethod
    def get_unittest_conn_info() -> ConnectionInfo:
        return MagnusConn.get_conn_info('graphscale-unittest')

    @staticmethod
    def is_db_unittest_up() -> bool:
        """Tests to see if the unittest-mysql is up and running on the localhost
        This allows for the conditional execution of tests on the db shards in addition
        to the memory shards"""

        if MagnusConn.is_up is not None:
            return MagnusConn.is_up

        try:
            conn_info = MagnusConn.get_unittest_conn_info()
            conn = pymysql_conn_from_info(conn_info)
        except pymysql.err.OperationalError as error:
            print('Could not connect to local mysql instance:')
            print('All tests will run locally')
            print(error)
            MagnusConn.is_up = False
        else:
            MagnusConn.is_up = True
            conn.close()  # type: ignore
        return MagnusConn.is_up

    @staticmethod
    def get_conn_info(db_name: str) -> ConnectionInfo:
        return ConnectionInfo(
            host='localhost',
            user='magnus',
            password='magnus',
            db=db_name,
        )


def db_mem_fixture(*, mem: Callable, db: Callable) -> List[Callable]:
    fixture_funcs = []
    if MagnusConn.is_db_unittest_up():
        fixture_funcs.append(db)
    fixture_funcs.append(mem)
    return fixture_funcs


async def async_test_graphql(
    query: str,
    pent_context: PentContext,
    graphql_schema: GraphQLSchema,
    root_value: PentContextfulObject=None,
    variable_values: Dict[str, Any]=None,
):
    # check.str_param(query, 'query')
    # check.param(pent_context, PentContext, 'pent_context')
    # check.param(graphql_schema, GraphQLSchema, 'graphql_schema')
    # check.opt_dict_param(variable_values, 'variable_values')

    result = await graphql(
        graphql_schema,
        query,
        context_value=pent_context,
        root_value=root_value,
        variable_values=variable_values
    )
    if result.errors:
        error = result.errors[0]
        print_error('GRAPHQL ERROR')
        print_error(error)
        orig = error.original_error

        print_error('ORIGINAL ERROR')
        print_error(orig)

        trace = orig.__traceback__
        print_error(''.join(traceback.format_tb(trace)))

        raise error
    return result