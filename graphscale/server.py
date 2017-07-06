from typing import Callable, Any

from graphql import GraphQLSchema

from sanic import Sanic
from sanic_graphql import GraphQLView

from .pent import PentContextfulObject, PentLoader


def create_graphql_app(
    root_object: PentContextfulObject, schema: GraphQLSchema, debug: bool=True
) -> Sanic:
    """ Creates a Sanic app and adds a graphql/graphiql endpoint """
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

    # this is totally gross and I need a better story for managing context lifetime
    # versus loader lifetime. The context houses the in-memory shards in in memory
    # case currently so you cannot create a new one with every request. However
    # you do need a new loader every request because it is affined with its
    # asyncio event loop
    def root_factory() -> Any:
        root_object.context.loader = PentLoader(root_object.context)
        return root_object

    app.add_route(
        GraphQLView.as_view(
            schema=schema, graphiql=True, root_factory=root_factory, context=root_object.context
        ), '/graphql'
    )
    return app


def run_graphql_endpoint(
    root_object: PentContextfulObject, schema: GraphQLSchema, debug: bool=True, port: int=8080
) -> None:
    """Create app, add graphql endpoint, and run it. Never returns."""

    app = create_graphql_app(root_object, schema, debug)
    app.run(host='0.0.0.0', debug=debug, port=port)
