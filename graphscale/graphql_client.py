from collections import namedtuple
from graphql import graphql as graphql_main

GraphQLArg = namedtuple('GraphQLArg', 'name arg_type value')


class InProcessGraphQLClient:
    def __init__(self, root_value, graphql_schema):
        self.root_value = root_value
        self.graphql_schema = graphql_schema

    @property
    def context(self):
        return self.root_value.context

    async def gen_mutation(self, graphql_text, *args):
        return await self.gen_operation(graphql_text, 'mutation', *args)

    async def gen_query(self, graphql_text, *args):
        return await self.gen_operation(graphql_text, 'query', *args)

    async def gen_operation(self, graphql_text, operation, *args):
        arg_strings = []
        for name, arg_type, _value in args:
            arg_strings.append("${name}: {arg_type}".format(name=name, arg_type=arg_type))

        arg_list = ', '.join(arg_strings)

        full_query = "{operation} ({arg_list}) ".format(arg_list=arg_list, operation=operation)
        full_query += '{' + graphql_text + '}'
        arg_dict = {arg.name: arg.value for arg in args}
        resp = await (
            exec_in_mem_graphql(
                self.graphql_schema, self.context, full_query, self.root_value, arg_dict
            )
        )
        if resp.errors:
            print(repr(resp.errors[0]))
            if hasattr(resp.errors[0], 'original_error'):
                print(repr(resp.errors[0].original_error))
                original_error = resp.errors[0].original_error
                import traceback
                trace = original_error.__traceback__
                trace_string = ''.join(traceback.format_tb(trace))
                print('ORIGINAL: ' + trace_string)
            raise resp.errors[0]

        return resp.data


async def exec_in_mem_graphql(graphql_schema, pent_context, query, root_value, variables=None):
    result = await graphql_main(
        graphql_schema,
        query,
        context_value=pent_context,
        variable_values=variables,
        root_value=root_value
    )
    return result
