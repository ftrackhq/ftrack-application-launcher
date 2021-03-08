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

Below a complete configuration for a generic application.

 .. literalinclude:: examples/config-example.json



Code based
----------


Below a complete code based launcher for a generic application.



 .. literalinclude:: examples/code-example.py

