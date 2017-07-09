Introduction
===============

What is Graphscale?
-------------------

Graphscale is an opinionated Python framework for creating scalable GraphQL servers. This guide assumes a deep familiarity with GraphQL and the concepts behind it. For more information please see the `GraphQL Website <http://www.graphql.org/>`_

Graphscale is vertically integrated stack comprised of three layers of software:

- **Kvetch**: A MySQL-backed, minimal, schemaless, eventually consistent graph database designed for predictable performance and horizontal scalability.

- **Pent**: A python object model designed specifically to power a GraphQL server. It is designed for easily managing concurrency in a single-threaded environment to efficiency interaction with a storage tier via batching.

- **Grapple**: A code generation engine that produces GraphQL python type definitions, pent code, and kvetch configuration based on annotated GraphQL files in an opinionated layout and style.



Horizontal Scalability 
------------------------

As service workloads, data sets, and utilization increases, a service must, at some point, horizontally scale. There is a limit to the size and capability of single machiens, so more machines must be employed to satisfied the requirements of the system. 

Portions of systems that are stateless are trivial to scale: divide requests among different instances of the service and deploy as many computing nodes as necessary to satisfy peak demand. Many modern container systems actually automatically manage this process. 

However at some point almost every non-trivial system requires state. Stateful portions of a system are much more challenging to scale. A typical strategy is to "shard" storage across many nodes. To shard means a piece of software determines what storage node data rest in. A typical naive strategy to take a user id and modulo it by the number of storage nodes in the system. All objects tied to a single user are then stored in a single shard. As the number of users increases, so do the number of shards.

Some systems are straightforward to horizontally scale. Take email. In an email system a user's data is their own, with limited interconnectivity -- emails are copied "by value" semantically -- and mutability requirements -- emails cannot be changed once sent. Those attributes make the system straightforward to scale by sharding by user. For a counterexample, take a social network. They are more difficult to scale, as they typically contain highly interconnected, heterogeneous data with many users viewing a single canonical copy of an object rather than an object-per-user. In applications with highly interconnected data, there is no obvious sharding strategy over traditional databases that leads to good performance across all the different views that an application needs. It is even more difficult to create this structure in a generic fashion.

In hortizontally scaled systems many of tools used to construct application graphs from backing stores no longer function. Developers using relational stores use JOINs to transform relational rows into data format suitable for view construction. The properties of a JOIN on a single storage node are well known. However, with most stores you cannot do cross node joins. Some stores take the challenge and attempt to provide this abstraction. 

Graphscale takes the position that these may be well-suited for, say, analytics workloads forth, but they will not be suitable for applications that require reliably low latency queries. Simply put, traditional relational data-modeling is the wrong model for most distributed, high performance applications.

Without support for high-performing, horizontally scalable queries at the storage layer, system developers must orchestrate these interactions with storage nodes with their own software. This is a non-trivial task, and one of the biggest challenges for systems that operate at scale. Managing this orchestration is one of the biggest motivators behind Graphscale.