Graphscale
=========

Graphscale is an opinionated Python framework for creating scalable GraphQL servers. This guide assumes a deep familiarity with GraphQL and the concepts behind it. For more information please see the `GraphQL Website <http://www.graphql.org/>`_ or get a practical introduction on `How to GraphQL <https://www.howtographql.com>`_.

Graphscale is a vertically integrated stack comprised of three layers of software:

- **Kvetch**: A MySQL-backed, minimal, schemaless, eventually consistent graph database designed for predictable performance and horizontal scalability.

- **Pent**: A python object model designed specifically to power a GraphQL server. 

- **Grapple**: A code generation engine that produces GraphQL python type definitions, pent code, and kvetch configuration based on annotated GraphQL files in an opinionated layout and style.

Graphscale requires Python 3.6. Mypy is also highly recommended. Graphscale code generation emits type-annotated python.

Installation
------------

Graphscale requires modified versions of three libraries: graphql-core, graphql-server-core, and Sanic-GraphQL. They are included as git submodules in this repo at the present time.

Virtual environments (e.g. venv) should be used to manage this. If you depend on the versions of these libraries currently in pypi this will not work. 

Before running anything you should create a virtual environment and then run script in the root of the repo,

``./install_dev_dependencies``

This installs the submodules in graphql, graphql-server-core, and sanic-graphql in that order.

Then install the remaining requirements in the requirements.txt file.

``pip3 install -r requirements.txt``

Then ensure that everything is working:

``python3 -m pytest tests``


Introduction By Example
-----------------------

In order to get started with graphscale you write a .graphql file that defines your schema and then build scaffolding and generated code. This scaffolding and generated code builds on a Python object model ("Pent") designed to power GraphQL backends, and a (mostly) schemaless store ("Kvetch") built on Redis and MySQL designed to model application graphs. 

Let's build the beginning of a todo app.


.. code-block:: python
  
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

Then run the following command:


``graphscale scaffold graphscale_todo.graphql``

This generates code and scaffolding in the following pattern:

.. code-block:: python

  graphscale_todo.graphql
  graphscale_todo/
      serve.py # run this to serve graphql requests
      graphql_schema/
          __init__.py # scaffolded
          generated.py # GraphQL definitions auto-generated
      kvetch/
          __init__.py # scaffolded
          generated.py # Kvetch configuration auto-generated
          kvetch_schema.py # scaffolded
      pent/
          __init__.py # scaffolded
          autopents.py # complete auto-generated pentish objects
          generated.py # pent generated base classes
          pents.py # manual pent implementations, scaffolded

 
Now simply run
 
``python3 serve.py``

And a full operational in-memory graphql server is running on localhost:8080/graphql. Navigate to it in a web browser and it loads graphiql.

See full example repo here: https://github.com/schrockn/graphscale_todo

Read the documentation for more information: http://graphscale.readthedocs.io
