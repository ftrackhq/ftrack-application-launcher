##########
Developing
##########



Creating a new launcher
=======================

In order to be able to find and manage applications and integrations,
Launchers requires to be either configured or written from scratch using the base libraries included in this module.

The configuration mode is suggested for all the base cases,
where the code base is suggested in case of special application launch behaviour.


Below we'll be looking at the same launch application expressed in configuration and code.

.. note::

    For simplicity we'll be taking the config arguments as example as are easier to read.


Attributes
----------

Let's have a look at the common attributes you'll find in both, split by mandatory and optional attributes.


**Mandatory attributes**
........................

* **context**:

    Provide a list to fill up with named contexts.
    The launcher will appear only in the given contexts.

* **identifier**:

    Defines a unique identifier for this launcher


* **applicationIdentifier**:

    Defines a unique identifier for the application to be launch.

    .. note::

        **applicationIdentifier** should always include the **{variant}** variable.



* **label**:

    A descriptive label to identify the application.

* **icon**:

    An icon to represent the application to launch.

    .. note::

        Icon can be either one of the application mapped or a full url path to a given icon.

* **variant**:

    Defines the variant of the application to be launched.

    .. note::

        **variant** should always include the **{version}** variable.


* **search_path**:




**Optional attributes**
.......................


* **priority** *(optional)*:

    Define the priority on which this event will be discovered.


* **integrations** *(optional)*:





Configuration based launcher
----------------------------

 .. literalinclude:: examples/config-example.json



Code based launcher
-------------------


 .. literalinclude:: examples/code-example.py

