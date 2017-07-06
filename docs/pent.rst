Pent
====

In the previous section we introduced Kvetch, the graph database that powers Graphscale. Next is Pent, the Python object model designed to power a GraphQL API tier. It is important to know about the attributes and constraints of kvetch, but vast amount of application logic will be about Pents. 



DataLoader
----------
DataLoader is an important abstraction in the GraphQL ecosystem as it addresses this serial fetching problem. DataLoader, in `whatever <https://github.com/facebook/dataloader/>`_ `language <https://github.com/syrusakbary/aiodataloader/>`_ it is `implemented <https://github.com/sheerun/dataloader/>`_ in, has the same form. It uses the language's facility or primitives for asynchronous programming -- whether it be callbacks, Promises, co-routines, awaitables, or otherwise -- to coalesce individual requests to backing storage into batches. This allows the application developer to think about fetching in serial fashion -- far easier to ordinary mortals to manage -- while a centralized piece of software managed the batching process for the developer.