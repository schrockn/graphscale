Introduction
===============

What is Graphscale?
-------------------

Graphscale is a Python framework for easily creating scalable GraphQL servers. This guide assumes a deep familiarity with GraphQL and the concepts behind it. For more information please see the `GraphQL Website <http://www.graphql.org/>`_

It is a vertically integrated stack comprised of three layers of software:

- **Kvetch**: A MySQL-backed, minimal, schemaless, eventually consistent graph database designed for predictable performance and horizontal scalability.

- **Pent**: A python object model designed specifically to power a GraphQL server. It is designed for easily managing concurrency in a single-threaded environment to efficiency interaction with a storage tier via batching.

- **Grapple**: A code generation engine that produces GraphQL python type definitions, pent code, and kvetch configuration based on annotated GraphQL files.

Horizontally Scalability 
------------------------

As services workloads increased they must scale. More machines must be employed to satisfied the requirements of the system. Portions of systems that are stateless are trivial to scale: divide requests among different instances of the service and deploy as many computing nodes as necessary to satisfy peak demand. Many modern container systems actually automatically manage this process. 

However at some point almost every non-trivial requires state. Stateful portions of a system are much more challenging to scale. A typical strategy is add storage nodes and then "shard" the storage. To shard means a piece of software determines what storage node data rest in. A typical naive strategy to take a user id and module it by the number of storage nodes in the system. All objects tied to a single user are then stored in a single shard.

Some systems are straightforward to scale. For example in an email system a users data is their own, with limited interconnectivity -- emails are copied "by value" semantically -- and mutability requirements -- emails cannot be changed once sent. Those attributes make the system straightforward to scale by sharding by user. For a counterexample, take a social network. They are more difficult to scale, as there is highly interconnected, heterogeneous data with many users viewing a single canonical copy of an object rather than an object-per-user. In applications with highly interconnected data there is no obvious sharding strategy that leads to good performance across all the different views that an application needs. It is even more difficult to create this structure in a generic fashion.

In hortizontally scaled systems many of tools used to construct application graphs from backing stores no longer function. Developers using relational stores use JOINs to transform relational rows into an interconnected graph suitable for user consumption. The properties of a JOIN on a single storage node are well known. However, with most stores you cannot do cross node joins. Some stores take the challenge and attempt to provide this abstraction. Graphscale takes the position that these may be well-suited for, say, analytics workloads forth, but they will not be suitable for applications that require reliably low latency queries. Simply put, relational storage is the wrong model for most massively distributed, high performance applications.

Without support for high-performing, horizontally scalable queries at the storage layer, system developers must orchestrate these interactions with storage nodes with their own software. This is a non-trivial task, and one of the biggest challenges for systems that operate at scale. Managing this orchestration is one of the biggest motivators behind Graphscale.

The Kvetch backing store operates on basic graph primitives. The Kvetch API allows for fetching nodes and edges. Nodes are fetched via globally unique IDs (UUIDs, currently) and are bags of key-value pairs. Edges provide connections to nodes (experienced users of relational systems would recognize edges as rows in a many-to-many join table) and allows the system to traverse along an application graph. 

In order to do this traversal, the application tier must interact with the storage tier repeatedly. For example, imagine a view in a collaborative todo app that displays the first few lists a user manages and then the first few items from each one of those lists. With a single relational database this would be implemented with a single query that joined two (or more) tables to fetch the user, her lists, and their items in one query. With kvetch, this requires multiple interactions with storage tier. First, the user must be fetched; then the edges connecting the user to their lists; then the lists themselves; then the edges to the items; and finally all of the items. 

Naively implemented this process could be extraordinarily inefficient. 

.. code-block:: python

    def todo_list_view(user_id)
        view = SomeView()
        user = fetch_user(user_id)
        view.add_user(user)
        for list_id in fetch_list_ids(user_id, first=10):
            list = fetch_list(list_id)
            view.add_list(list)
            for item_id = fetch_item_ids(list_id, first=5):
                item = fetch_item(item_id)
                view.add_item(item)

        return view

In this case, for a simple view, the code will issue well over 50 synchronous queries to the storage tier. An obvious solution would be to manually batch these calls -- for example by fetching all items as once instead of one at a time in the inner loop. That is true in this particular example. However dealing with this generically is more difficult, especially in the context of a GraphQL server.

.. code-block:: python

 todoUser($id) {
    name
    todoLists(first: 10) {
        name
        todoItems(first: 5) { text }
    }
 }

In GraphQL servers, fields are implemented by function calls, known as "resolvers." This is a simple, clear mapping. However it can lead to large number of serial interactions with storage for complex queries. In the above example the most obvious implementation of this queries would issue 10 separate serial fetches for the 10 sets of todo items required to materialize this GraphQL request. Each of the resolver calls to satisfy ``todoItems(first: 5)`` run serially by the execution environment.

Asynchronous Batching with DataLoader and async/await
-----------------------------------------------------

DataLoader is an important abstraction in the GraphQL ecosystem as it addresses this serial fetching problem. DataLoader, in `whatever <https://github.com/facebook/dataloader/>`_ `language <https://github.com/syrusakbary/aiodataloader/>`_ it is `implemented <https://github.com/sheerun/dataloader/>`_ in, has the same form. It uses the language's facility or primitives for asynchronous programming -- whether it be callbacks, Promises, co-routines, awaitables, or otherwise -- to coalesce individual requests to backing storage into batches. This allows the application developer to think about fetching in serial fashion -- far easier to ordinary mortals to manage -- while a centralized piece of software batches it for the developer.

As of version 3.5, Python supports ``async/await``, which is a major advance in asynchronous programming. Graphscale relies heavily on this new language construct in its Pent framework.  

Take the following example where there are two pre-existing functions that a developer does not wish to modifiy ``fetch_other_objects`` and ``fetch_some_other_objs``) but wishes to reuse to construct a new view of data. The developer dutifully writes a function that fetches these data.

.. code-block:: python

    def fetch_other_objs(obj_ids):
        # sync_fetch_objects synchronously fetches N objects from storage
        objects = sync_fetch_objects(obj_ids) 
        other_ids = [obj.other_id for obj in objects]
        return sync_fetch_objects(other_ids)

    def fetch_some_other_objs(obj_ids):
        objects = sync_fetch_objects(obj_ids)
        some_other_ids = [obj.some_other_id for obj in objects]
        return sync_fetch_objects(some_other_ids)

    def do_fetching(obj_ids):
        other_objects = fetch_other_objects(obj_ids)
        some_other_objects =  fetch_some_other_objs(obj_ids)
        return (other_objects, some_other_objects)

    
As implemented this would perform four serial, synchronous interactions with the storage tier. Async/await changes this interaction, while not invasively changing the code, as callbacks would, for example.

.. code-block:: python 

    async def gen_other_objs(loader, obj_ids):
        objects = await loader.load_many(obj_ids) 
        other_ids = [obj.other_id for obj in objects]
        return await loader.load_many(other_ids)

    async def gen_some_other_objs(loader, obj_ids):
        objects = await loader.load_many(obj_ids) 
        some_other_ids = [obj.some_other_id for obj in objects]
        return await loader.load_many(some_other_ids)

    class ObjectLoader(DataLoader):
        async def batch_load_fn(self, obj_ids):
            return sync_fetch_objects(obj_ids)

    async def gen_objects(obj_ids):
        return sync_fetch_objects(obj_ids)

    async def do_fetching(obj_ids):
        loader = DataLoader(sync_fetch_objects)
        other_objects, some_other_objects = await asyncio.gather(
            gen_other_objects(loader, obj_ids), gen_some_other_objs(loader, obj_ids)
        )
        return other_objects, some_other_objects

Note that ``gen_other_objs`` and ``gen_some_other_objs``  are quite similar to their synchronous counterparts: What were raw function calls are now await statements. The developer essentially now has the illusion of synchronous control flow.

The end result of this code running is two roundtrips. In addition, DataLoader adds a caching layer so that previously fetched objects with the same id are not re-fetched. Computation in each async function proceeds until an await is encountered whose semantics dictate return of control to the event loop -- as DataLoader.load_many does if all objects are not in cache. So in this case, ``asyncio.gather`` has created two concurrent async function invocations. The first executes until the first ``load_many`` and then yields control back to the central event loop. This event loop then executes ``gen_some_other_objs`` until it enqueues its fetch. With no more async functions left to do any work the event loops yields control to DataLoader which executes a single synchronous fetch. (In this case the data loader calls the existing function ``sync_fetch_objects``) Execution then resumes where the last ``await`` occurred in each function. Both functions execute until their next ``load_many`` call which enqueue two distinct sets of ids to fetch. These are then batched and fetched synchronously.

This is a large mental shift as computation now unrolls as a DAG (directed, acyclic graph) of async functions invocations rather than a stack of synchronous functions calls. Once a developer has a adjusted to this fact, it's quite intuitive. 

Enter Pent
----------

TODO