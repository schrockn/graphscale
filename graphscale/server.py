from graphql import GraphQLSchema

from sanic import Sanic
from sanic_graphql import GraphQLView

from graphscale import check


def create_graphql_app(root_object, schema, debug=True):
    """ Creates a Sanic app and adds a graphql/graphiql endpoint """

    check.param(schema, GraphQLSchema, 'schema')
    check.bool_param(debug, 'debug')

    app = Sanic(__name__)
    app.debug = debug

    if debug:
        # hack from https://github.com/channelcat/sanic/issues/168
        # for some reason pylint is confused by this import
        #E0611 no name in module
        #pylint: disable=E0611
        from aoiklivereload import LiveReloader
        reloader = LiveReloader()
        reloader.start_watcher_thread()

    context = root_object.context

    app.add_route(
        GraphQLView.as_view(schema=schema, context=context, root_value=root_object, graphiql=True),
        '/graphql'
    )
    return app


def run_graphql_endpoint(root_object, schema, debug=True, port=8080):
    """Create app, add graphql endpoint, and run it. Never returns."""

    check.param(schema, GraphQLSchema, 'schema')
    check.bool_param(debug, 'debug')
    check.int_param(port, 'port')

    app = create_graphql_app(root_object, schema, debug)
    app.run(host='0.0.0.0', debug=debug, port=port)
