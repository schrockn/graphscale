Grapple
=======

This documentation has covered Kvetch -- a schemaless database designed to serve application graphs in a scalable fashion -- and Pent -- a python object model designed to model graphs and power GraphQL servers. Next is grapple, a code generation engine vertically integrates GraphQL, Pent, and Kvetch.

Grapple uses .graphql files with custom directives to emit Kvetch-Pent-powered backends. Grapple produces three layers of generated code.

1. GraphQL: Graphscale developers do not need to write GraphQL definitions in Python. They are automatically generated.

2. Pent Scaffolding: TODO

3. Kvetch: TODO

Code generation is not the endstate of a Graphscale-powered system, but only the beginning. Indeed as a system develops and more custom logic is needed in the application tier, the code generation should go away and should be replaced by manually implemented code. Code generation will only describe the most simple and trivial interactions. Anything beyond that should be implemented in code.

