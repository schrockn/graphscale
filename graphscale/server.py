from sanic import Sanic
from sanic_graphql import GraphQLView


def create_graphql_app(root_object, schema, debug=True):
    app = Sanic(__name__)
    app.debug = debug

    if debug:
        # hack from https://github.com/channelcat/sanic/issues/168
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
    app = create_graphql_app(root_object, schema, debug)
    app.run(host='0.0.0.0', debug=debug, port=port)
