# graphscale

Graphscale is an opinionated Python framework for creating scalable GraphQL servers.

Graphscale requires Python 3.6. Mypy is also highly recommended. Graphscale code generation emits type-annotated python.

Introduction By Example
-----------------------

In order to get started with graphscale you write a .graphql file that defines your schema and then build scaffolding and generated code.

Let's build the beginning of a todo app.

```sh
    type Query {
      todoUser(id: UUID!): TodoUser @readPent
    }

    type TodoUser @pent(typeId: 10000){
      id: UUID!
      name: String!
    }
```