Pythonic, Mostly
----------------

Graphscale follows most of the recommendations of the Python community, recommendations being the idioms that are "Pythonic." Most of them are sensisible and result in elegant code and good software. However there are some specific subjects where Graphscale explicitly diverges from standard best practices in the Python community, mostly around error handling. These are documented here.

"Reponsible Users" and Immutability
===================================
Python is famous for eskewing information hiding and encapsulation. This was previously expressed with the phrase that Python user are all "consenting adults" which has now been `bowdlerized <https://github.com/kennethreitz/python-guide/issues/525/>`_ to the more Victorian-era-friendly phrase that Python programmers are "responsible users." Programmers may be responsible, but they are mortal and fallible. Distributed systems development is a complex task, and any tools that can reduce this complexity should be used. 

Python programmers, believing in the responsibility of other Python programmers, default to public read-write properties and expose functionality in modules and packages by default. Python misses a big opportunity here because these practices default to mutable objects. Immutability is a powerful concept in software and leads to more manageable, intuitive code when utilizied property. This is a deep topic beyond the scope of this guide. A great starting place on the topics of immutability is Rich Hickey. See `this <https://youtu.be/-6BsiVyC1kM/>`_ talk or this `talk <https://www.infoq.com/presentations/Are-We-There-Yet-Rich-Hickey/>`_ for some excellent coverage of this topic. In fact, just go and listen to everything that Rich Hickey has ever said.

Graphscale heavily utilizes the "namedtuple" abstraction built into python, which is a Pythonic, concise way of building immutable tuples with named fields. Hopefully more immutability-friendly abstractions like namedtuple get introduced into idiomatic Python.

Pents are not immutable but they are read-only. They accumulate state over the their object lifetime, and anytime any of that state changes, the object should be discarded. While this does not allow for the strong guarantees that purely immutable objects do they still retain important properties. They can be cached in a per-request cache easily.

Importantly, write paths are covered by completely different set of abstractions. One of the biggest mistakes that traditional ORMs make is commingling read and write functionality in the same object. This often leads to use of trigger-like mechanisms to chain and cascade the side effects of mutations across your application in difficult to understand ways. Instead, mutations in graphscale are just functions where side effects are explicitly managed. As the mutations mature it will evolve in the spirit of the `Redux <http://redux.js.org/>`_ framework, very popular in the JS community.


In Software, Permission not Forgiveness
=======================================
Python has adopted a strategy of "Ask forgiveness not permission" when it comes to error handling. This means that programmers are expected to know what errors are thrown from code that they invoke and then catch the errors and do some backup behavior. For example if you google "how to tell if string can be an int in python" or something similar to you will a stack overflow question/answer like the `following <http://bit.ly/2rsUmwC/>`_. So the Pythonic method of performing this task is:


.. code-block:: python

    try:
        int(s)
        # do something with s knowing it's an int
    except ValueError:
        # do some other behavior

Python also frequently uses exceptions as control flow. For example, the core generator abstraction in Python uses the ``StopIteration`` exception to signal to calling code that there are no further items in a sequence. These exceptions are regularily thrown in an otherwise well-functionality python program.

Graphscale takes the opposite approach deliberately, so-called "Look Before You Leap" or LBYL. This means in effect that programmers are expected to write code any exception thrown means there was a programming error, some sort of system failure (e.g. an external system goes down), or to end a computation and signal user error (e.g. malformed input).

Additionally, during the vast majority of tasks a developer should never write an ``except`` block. Error handling should be processed by common infrastructure and abstractions. This abstraction in Graphscale is known as an error boundary. See the error boundary documentation for more details.

Don't Assert or Document, Check
===============================

Python has an assert statement that is frequently used to perform tasks like type-checking and invariant checking. In addition, Python programmers often rely on documentation, rather than type-checking in order to know what functions can accept or return. Graphscale does not abide by this philosophy. Rather it does runtime type-checking for public APIs that have achieved some level of stability, using the "check" module in graphscale.

This follows the philosophy of LBYL stated above and is also encoded in the philosophy of error boundaries. The basic tenet is this: if a programming error is detected, you should terminiate the current scope computation as delimited by an error boundary. When a program gets into a unexpected state, very bad things can happen. Critical data can leak, data can be overwritten, systems can become fundamentally destabilized and etc. Crashes or terminated computation, by comparison have relatively known and low cost. This is especially true in a server environment where one can redeploy code quickly. (Client-side code has different tradeoffs in this area). Rather than just "logging and soldiering on" or simply ignoring errors, an exception should be thrown which will terminate the current computational task in scope (as delienated by an error boundary).

Should a runtime check be in a function that is very frequently executed and adds overhead such that it is user perceptiple or reaches some large threshold in terms of an efficiency regression for your entire server fleet, then remove them selectively. The important thing is to default to type-checking.


Error Boundaries
================