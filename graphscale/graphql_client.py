from typing import Any, Dict, NamedTuple, cast

from graphql import graphql as graphql_main
from graphql import GraphQLSchema
from graphql.execution import ExecutionResult

from .pent import PentContext, PentContextfulObject


class GraphQLArg(NamedTuple):
    name: str
    arg_type: str
    value: Any


class InProcessGraphQLClient:
    def __init__(self, root_value: PentContextfulObject, graphql_schema: GraphQLSchema) -> None:
        self.root_value = root_value
        self.graphql_schema = graphql_schema

    @property
    def context(self) -> PentContext:
        return self.root_value.context

    async def gen_mutation(self, graphql_text: str, *args: GraphQLArg) -> dict:
        return await self._gen_operation(graphql_text, 'mutation', *args)

    async def gen_query(self, graphql_text: str, *args: GraphQLArg) -> dict:
        return await self._gen_operation(graphql_text, 'query', *args)

    async def _gen_operation(self, graphql_text: str, operation: str, *args: GraphQLArg) -> dict:
        arg_strings = []
        for name, arg_type, _value in args:
            arg_strings.append("${name}: {arg_type}".format(name=name, arg_type=arg_type))

        arg_list = ', '.join(arg_strings)

        full_query = (
            '{operation} ({arg_list}) '.format(arg_list=arg_list, operation=operation) + '{' +
            graphql_text + '}'
        )
        arg_dict = {arg.name: arg.value for arg in args}
        result = await (
            exec_in_mem_graphql(
                self.graphql_schema, self.context, full_query, self.root_value, arg_dict
            )
        )
        if result.errors:
            _process_error(result)

        return cast(dict, result.data)


def _process_error(result: ExecutionResult) -> None:
    # this is pretty horrific. need a better generalized story to getting reasonable
    # stack traces
    print(repr(result.errors[0]))
    if hasattr(result.errors[0], 'original_error'):
        print(repr(result.errors[0].original_error))
        original_error = result.errors[0].original_error
        import traceback
        trace = original_error.__traceback__
        trace_string = ''.join(traceback.format_tb(trace))
        print('ORIGINAL: ' + trace_string)


async def exec_in_mem_graphql(
    graphql_schema: GraphQLSchema,
    pent_context: PentContext,
    query: str,
    root_value: Any,
    variables: Dict[str, Any]=None
) -> ExecutionResult:
    return await graphql_main(
        graphql_schema,
        query,
        context_value=pent_context,
        variable_values=variables,
        root_value=root_value
    )
