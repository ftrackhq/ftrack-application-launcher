##########
Developing
##########



Creating a new launcher
=======================

In order to be able to find and manage applications and integrations,
Launchers requires to be either configured or written from scratch using the base libraries included in this module.

The configuration mode is suggested for all the base cases,
where the code base is suggested in case of special application launch behaviour.


Configuration based
-------------------

Below a complete configuration for an application.

 .. literalinclude:: examples/config-example.json

Let's break down the fields and what they are for:


* **priority**::

    Provide the ability to define a custom priority for the application.


* **context**::

    This list limit the discoverability of the application in the given contexts.
    It can contain either **null**, or Named context such as **Project** , **Task**, or any other custom entity available in the project.



Code based
----------



