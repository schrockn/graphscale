Kvetch
======

Kvetch is horizontally scalable graph storage system built over Redis and MySQL. 

While it is built on MySql it uses very few of its relational features. The store is largely schemaless and JOINs are not used during the operation. By far, most of the interaction with the applications data will be through the in-memory Redis store. The goal should be to have the entire working set of the application in the memory of the Redis nodes, using MySQL for persistence and to reconstruct cached data on mutations.

MySql is reliable backing store with well-known operational characteristics that has powered large enterprises for decades. MySQL is used at Facebook, `Pinterest <https://medium.com/@Pinterest_Engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96caj6f/>`_, and other massively scaled as the storage engine for application data. It works. 

Additionally storage in Kvetch is schemaless. It actually borrows a lot from the architecture of the now defunct FriendFeed. You can read a description of Friendfeed's backend `here <https://backchannel.org/blog/friendfeed-schemaless-mysql/>`_. Like FriendFeed, Kvetch does not rely on MySQL for schematizing data, and all typing and type management is instead done in software. As you evolve your data model in Kvetch there is no longer a need to run DDL statements on your database shards.

Horizontal Scalability
----------------------

As service workloads, data sets, and utilization increases, a service must, at some point, horizontally scale. There is a limit to the size and capability of single machiens, so more machines must be employed to satisfied the requirements of the system. 

Portions of systems that are stateless are trivial to scale: divide requests among different instances of the service and deploy as many computing nodes as necessary to satisfy peak demand. Many modern container systems actually automatically manage this process. 

However at some point almost every non-trivial system requires state. Stateful portions of a system are much more challenging to scale. A typical strategy is to "shard" storage across many nodes. To shard means a piece of software determines what storage node data rest in. A typical naive strategy to take a user id and modulo it by the number of storage nodes in the system. All objects tied to a single user are then stored in a single shard. As the number of users increases, so do the number of shards.

Some systems are straightforward to horizontally scale. Take email. In an email system a user's data is their own, with limited interconnectivity -- emails are copied "by value" semantically -- and mutability requirements -- emails cannot be changed once sent. Those attributes make the system straightforward to scale by sharding by user. For a counterexample, take a social network. They are more difficult to scale, as they typically contain highly interconnected, heterogeneous data with many users viewing a single canonical copy of an object rather than an object-per-user. In applications with highly interconnected data, there is no obvious sharding strategy over traditional databases that leads to good performance across all the different views that an application needs. It is even more difficult to create this structure in a generic fashion.

In hortizontally scaled systems many of tools used to construct application graphs from backing stores no longer function. Developers using relational stores use JOINs to transform relational rows into data format suitable for view construction. The properties of a JOIN on a single storage node are well known. However, with most stores you cannot do cross node joins. Some stores take the challenge and attempt to provide this abstraction. 

Graphscale takes the position that these may be well-suited for, say, analytics workloads forth, but they will not be suitable for applications that require reliably low latency queries. Simply put, traditional relational data-modeling is the wrong model for most distributed, high performance applications.

Without support for high-performing, horizontally scalable queries at the storage layer, system developers must orchestrate these interactions with storage nodes with their own software. This is a non-trivial task, and one of the biggest challenges for systems that operate at scale. Managing this orchestration is one of the biggest motivators behind Graphscale.

The API
-------

The first chunk of the kvetch API is for objects. You can do basic CRUD (Create, Read, Update, Delete) operations by a globally unique ID. 

.. code-block:: python

  def get_object(obj_id: UUID) -> dict:
  def get_objects(obj_ids: List[UUID]) -> List[dict]

  def create_object(type_id: Int, data: dict) -> UUID
  # only updates the keys present in incoming data
  def update_object(obj_id: UUID, data: dict) -> None
  def delete_object(obj_id: UUID) -> None


However this is not enough to express an application's graph. Relationships between objects must be stored. Kvetch does this in the form of edges. An edge consists of two object ids, an edge id to assign semantic meaning to the relationship, and optional metadata. You can create edges and also query them in a paginateable fashion.

.. code-block:: python

  # Edge is (from_id: UUID, to_id: UUID, data: dict)
  # after and first are there to support pagination
  def get_edges(
    edge_id: Int, 
    from_id: UUID, 
    after: UUID=None, 
    first: int=None) -> List[Edge] 

  def insert_edge(edge_id: Int, edge: Edge) -> None

Lastly there are indexes. Indexes map values to object ids. Every index has a table on every shard. They are sharded by search term. That way a search only queries a single shard.

.. code-block:: python

  def insert_index_entry(
    index_id: Int, 
    index_value: Any, # index-dependent type
    target_id: UUID) -> None

  # get the ids. allows for pagination 
  def query_index(
    index_id: Int, 
    index_value: Any, # index-dependent type
    after: UUID=None, 
    first: int=None) -> List[UUID]

Canonical Data and Eventual Consistency
---------------------------------------

It is important to understand what data is canonical and what data is non canonical. Kvetch provides no transactional guarantees across nodes and can become inconsistent. 

For example let's model a todo list with this model. You would persist a complete graph of a list with two items with the following operations:

.. code-block:: python

    list_id = create_object(LIST_TYPE, { 'name': 'A List' } )

    item_one_data = { 'text': 'Item One', 'list_id': list_id }
    item_one_id = create_object(ITEM_TYPE, item_one_data)
    insert_edge(LIST_TO_ITEM, Edge(from_id=list_id, to_id=item_one_id))

    item_two_data = { 'text': 'Item Two', 'list_id': list_id }
    item_two_id = create_object(ITEM_TYPE, item_two_data)
    insert_edge(LIST_TO_ITEM, Edge(from_id=list_id, to_id=item_two_id))

It is easy for this code to leave the store in an inconsistent state if an error occurs or the process dies. For example imagine if the process died in between the first item creation and the first edge creation.

.. code-block:: python

    list_id = create_object(LIST_TYPE, { 'name': 'A List' } )
    item_one_data = { 'text': 'Item One', 'list_id': list_id }
    item_one_id = create_object(ITEM_TYPE, item_one_data)
    ## PROCESS DIES

Now we are left with an item that can navigate to its parent list, but the list cannot navigate to that item. This would manifest itself as a user-facing bug in the list view.

In order to compensate for this kvetch views certain data as *canonical*. In this case the ``list_id`` embedded in object is considered the canonical data, and the edge is derived from that canonical data. Importantly this means it can be reconstructed. Reconstruction is how kvetch enforces eventual consistency. 

A kvetch installation continuously runs processes that fix object graphs that have been corrupted in this fashion that scan canonical data and ensure that derived data based on the canonical data exists and is well-formed.

While this structure would be unwise for high-frequency finanical transactions or other applications that cannot tolerate inconsistency even for short periods of time, most applications don't requirement that level of consistency. Most applications can tolerate short periods (typically measured in seconds) of inconsistency, provided that errors that cause inconsitent state are relatively rare. 

Code as Schema, Not Storage Schema
----------------------------------

In order for Kvetch to track side effects and maintain graph consistency, it must be aware of the semantics of the graph. It does this via a schema defined in code. Returning to the todo example, the following kvetch schema would describe a mapping of users to lists to items:

.. code-block:: python 

    Schema(
        objects=[
            ObjectDefinition(type_name='TodoUser', type_id=100000),
            ObjectDefinition(type_name='TodoList', type_id=100001),
            ObjectDefinition(type_name='TodoItem', type_id=100002),
        ],
        edges=[
            StoredIdEdgeDefinition(
                edge_name='user_to_list_edge', 
                edge_id=10000, 
                stored_id_attr='owner_id', 
                stored_on_type='TodoList'
            ),
            StoredIdEdgeDefinition(
                edge_name='list_to_item_edge', 
                edge_id=10001, 
                stored_id_attr='list_id', 
                stored_on_type='TodoItem'
            ),
        ],
    )

Through this schema, kvetch can trigger edge inserts, updates, and deletes, and run cleaners to reconstruct inconsitent object graphs. For example, every time a TodoList is created an edge going from the ``owner_id`` stored in the list to the list's id itself is created. The ``StoredIdEdgeDefinition`` with the name ``user_to_list_edge`` defines that relationship.

In Graphscale, most of these configurations will be generated. However it is important for any consumer of the system to understand what is going on.  

Orchestration
-------------

Naively used, Kvetch would be very inefficient. Useful views in applications other involve hundreds or thousands of objects. Again let's take the todo list example. 

Imagine a view that displays the first few lists a user manages and then the first few items from each one of those lists. With a single relational database this would be implemented with a single query that joined two (or more) tables to fetch the user, her lists, and their items in one query. With kvetch, this requires multiple interactions with storage tier. First, the user must be fetched; then the edges connecting the user to their lists; then the lists themselves; then the edges to the items; and finally all of the items.

Naively implemented this process could be extraordinarily inefficient:

.. code-block:: python

    def create_todo_list_view(user_id)
        user = get_object(user_id) 
        view = SomeView(user)
        for list_id in get_edges(USER_TO_LIST, user_id, first=10):
            list = get_object(list_id)
            items = []
            for item_id in get_edges(LIST_TO_ITEMS, list_id, first=5):
                items.append(get_object(item_id))
            view.add_list(list, items)
        return view


In this case, for a simple view, the code will issue well over 50 synchronous queries to the storage tier. An obvious solution would be to manually batch these calls -- for example by fetching all items as once instead of one at a time in the inner loop. That is true in this particular example. However dealing with this generically is more difficult.


Asynchronous fetching async/await
-----------------------------------------------------

As of version 3.5, Python supports ``async/await``, which is a major advance in asynchronous programming. Graphscale relies heavily on this new language construct to efficiently interact with Kvetch.

Here is the todo list view construction written with async/await. Note we are calling ``gen_object`` instead of ``get_object`` to indicate we are calling an awaitable. 

.. code-block:: python

    async def gen_seq(func, seq):
        return await gather(*[func(item) for item in seq])

    async def create_view(user_id):
        user = await gen_object(user_id) 
        view = SomeView(user)
        list_ids = await gen_edges(USER_TO_LIST, user_id, first=10)
        list_datas = await gen_seq(gen_list_data, list_ids)
        for lst, items in list_datas:
            view.add_list(lst, items)        
        return view

    # returns Tuple(todo_list, todo_items)
    async def gen_list_data(list_id):
        todo_list = await gen_object(list_id)
        item_ids = await gen_edges(LIST_TO_ITEMS, list_id, first=5)
        items = await gen_seq(gen_object, item_ids) 
        return (todo_list, items)

Using await we can batch our interactions with Kvetch while still writing composable functions. In this case the call to ``await gen_seq(gen_list_data, list_ids)`` in ``create_todo_list_view`` creates ten awaitables that can execute concurrently. That means there will be separate invocations of ``gen_list_data`` executing concurrently. However because they return control back to a central event loop when they hit an await that blocks, they can cooperate. In this case then 10 seperate calls to ``gen_object(list_id)`` will end up coalescing into one call to fetch all ten lists. Ideally -- assuming all data is cache in the Redis tiere -- this would end up issuing five blocking calls to Redis, which in typical configurations would be on the order of a few microseconds.