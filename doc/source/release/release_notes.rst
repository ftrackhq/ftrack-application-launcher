
..
    :copyright: Copyright (c) 2021 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    .. change:: changed
        :tags: Adobe Hook

        Hide adobe after efects and premier pro from being discovered.

.. release:: 1.0.5
    :date: 2022-06-20

    .. change:: fixed
        :tags: Config

        Hiero does not discover under linux.

    .. change:: fixed
        :tags: Config

        NukeX does not get discovered correctly.

    .. change:: fixed
        :tags: Config

        cineSync Play is wrongly named CineSync Play.
        

.. release:: 1.0.4
    :date: 2022-05-18

    .. change:: changed
        :tags: Config

        Remove discovery of cinesync play Beta and target stable release.

.. release:: 1.0.3
    :date: 2022-03-21

    .. change:: fixed
        :tags: Core

        os.pathsep is not a function, eliminate list modification while iterating

    .. change:: changed
        :tags: Core

        Rework event for better tracking.
        Use :ref:`ftrack_connect.usage.send_event`.

    .. change:: changed
        :tags: Core

        Consolidate application and integration usage information.


.. release:: 1.0.2
    :date: 2022-01-15

    .. change:: new
        :tags: Launcher

        Add CineSyncPlay Beta launcher.

    .. change:: changed
        :tags: Setup

        Remove documentation dependencies from setup.py as already present in doc/requirements.txt

    .. change:: new
        :tags: Core

        Provide current "platform" as new event data.

    .. change:: new
        :tags: Core
        
        Allow configurations to be disabled through event.   

.. release:: 1.0.1
    :date: 2021-10-01


    .. change:: new
        :tags: Config

         Provide nuke-x configuration for pipeline integration. 


.. release:: 1.0.0
    :date: 2021-09-07

    .. change:: new

        First release version.
