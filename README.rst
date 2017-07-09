# graphscale

Graphscale is an opinionated Python framework for creating scalable GraphQL servers.

Graphscale requires Python 3.6. Mypy is also highly recommended. Graphscale code generation emits type-annotated python.

Introduction By Example
-----------------------

In order to get started with graphscale you write a .graphql file that defines your schema and then build scaffolding and generated code. This scaffolding and generated code builds on a Python object model ("Pent") designed to power GraphQL backends, and a (mostly) schemaless store ("Kvetch") built on Redis and MySQL designed to model application graphs. 

Let's build the beginning of a todo app.

mkdir graphscale_todo
touch graphscale_todo/graphscale_todo.graphql
cd graphscale_todo

Make the contents of graphscale_todo.graphql:

.. code-block:: python
  type Query {
    todoUser(id: UUID!): TodoUser @readPent
  }

  type TodoUser @pent(typeId: 10000){
    id: UUID!
    name: String!
  }
    
  type Mutation {
    createTodoUser(data: CreateTodoUserData!): CreateTodoUserPayload @createPent
    updateTodoUser(id: UUID!, data: UpdateTodoUserData!): UpdateTodoUserPayload @updatePent
    deleteTodoUser(id: UUID!): DeleteTodoUserPayload @deletePent(type: "TodoUser")
  }
    
  input CreateTodoUserData @pentMutationData { name: String! }

  type CreateTodoUserPayload @pentMutationPayload { todoUser: TodoUser }

  input UpdateTodoUserData @pentMutationData { name: String! }

  type UpdateTodoUserPayload @pentMutationPayload { todoUser: TodoUser }

  type DeleteTodoUserPayload @pentMutationPayload { deletedId: UUID }

::
   graphscale scaffold graphscale_todo.graphql


This generates code and scaffolding in the following pattern:


graphscale_todo.graphql
graphscale_todo/
    serve.py # run this to serve graphql requests
    graphql_schema/
        __init__.py # scaffolded
        generated.py # GraphQL definitions auto-generated
    kvetch/
        __init__.py # scaffolded
        generated.py # Kvetch configuration auto-generated
        kvetch_schema.py #scaffolded
    pent/
        __init__.py # scaffolded
        autopents.py # complete auto-generated pentish objects
        generated.py # pent generated base classes
        pents.py # manual pent implementations, scaffolded

 
Now simply run
 
> python3 serve.py

And a full operational in-memory graphql server is running on localhost:8080/graphql. Navigate to it in a web browser and it loads graphiql.

Read the documentation for more information
