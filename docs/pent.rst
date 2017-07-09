Pent
====

In the previous section we introduced Kvetch, the graph database that powers Graphscale. Next is Pent, the Python object model designed to power a GraphQL API tier. It is important to know about the attributes and constraints of kvetch, but most business logic in a Graphscale-driver Python codebase will be against the Pent API. Pent relies heavily on async/await -- new in Python 3.5 -- and although optional, use of mypy is strongly recommended.

Todo Example
------------

Here is a minimal Pent hierarchy based on the ever-present Todo app.

.. code-block:: python

    class TodoUser(Pent):
        @property
        def name(self) -> str:
            return self._data['name']

        async def gen_todo_lists(self, first: int=100, after: UUID) -> list
            cls, edge = TodoList, 'user_to_list_edge'
            return await self.gen_edge_pents(cls, edge, first, after)

    class TodoList(Pent):
        @property
        def name(self) -> str:
            return self._data['name']

        async def gen_owner(self) -> TodoUser:
            return TodoUser.gen(self.context, self._data['owner_id']

        async def gen_todo_items(self, first: int, after: UUID) -> List[TodoItem]
            cls, edge = TodoItem, 'list_to_item_edge'
            return await self.gen_edge_pents(cls, edge, first, after)

    class TodoItem(Pent)
        @property
        def text(self) -> str:
            return self._data['text']

        async def gen_todo_list(self) -> TodoList:
            return TodoList.gen(self.context, self._data['todo_list_id']

Going back to our previous example, let's imagine we are building a view that displays the first 10 todo lists of a user the first 5 items from each of those lists.

.. code-block:: python

    async def gen_seq(func, seq):
        return await gather(*[func(item) for item in seq])

    async def create_view(context: PentContext, user_id: UUID) -> SomeView:
        user = await TodoUser.gen(context, user_id)
        view = SomeView(user)
        todo_lists = await user.gen_todo_lists(first=10)
        todo_item_chunks = await gen_seq(
            lambda todo_list: todo_list.gen_todo_items(first=5),
            todo_lists)

        for todo_list, todo_items in zip(todo_lists, todo_item_chunks):
            view.add_list(todo_list, todo_items)

        return view


Pent Properties
---------------

1. Read-only
2. Global ID
3. Designed for asynchronous programming



Pent-GraphQL Isomorphism
------------------------
Pent is designed to be a python type system that has a direct one-to-one mapping (i.e. a bijection) with the exposed GraphQL type system. In concrete terms, this means there are **no** free-standing custom resolvers in Graphscale. All business logic are properties and methods on Pent objects. This ensures that internal business logic, scripts, and server-side computation shares the same exact behavior as your client.

Pent is also designed to feel "native" to python. That means that although the GraphQL abides by GraphQL conventions -- like camel-casing -- Pent follows python conventions. Grapple -- the code generation engine interface between GraphQL and Pent -- manages the mapping between the two conventions. Aesthetics and taste matter, and the APIs should feel natural to GraphQL programmers who know nothing about Python, and to Python programmers who know nothing about GraphQL.


DataLoader
----------
DataLoader is an important abstraction in the GraphQL ecosystem as it addresses this serial fetching problem. DataLoader, in `whatever <https://github.com/facebook/dataloader/>`_ `language <https://github.com/syrusakbary/aiodataloader/>`_ it is `implemented <https://github.com/sheerun/dataloader/>`_ in, has the same form. It uses the language's facility or primitives for asynchronous programming -- whether it be callbacks, Promises, co-routines, awaitables, or otherwise -- to coalesce individual requests to backing storage into batches. This allows the application developer to think about fetching in serial fashion -- far easier to ordinary mortals to manage -- while a centralized piece of software managed the batching process for the developer.