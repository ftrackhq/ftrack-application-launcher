# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import sys
import pprint
import logging
import json
import re
import datetime

import platform

cwd = os.path.dirname(__file__)

sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))

sys.path.append(sources)

import ftrack_api
import ftrack_application_launcher


class ApplicationLauncher(ftrack_application_launcher.ApplicationLauncher):
    '''Discover and launch hieroplayer.'''

    def _get_application_environment(self, application, context=None):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            ApplicationLauncher, self
        )._get_application_environment(application, context)

        environment = ftrack_application_launcher.append_path(
            sources,
            'PYTHONPATH',
            environment
        )

        return environment


class LaunchHieroPlayerAction(ftrack_application_launcher.ApplicationLaunchAction):
    '''Adobe plugins discover and launch action.'''
    context = [None, 'Task', 'AssetVersion']
    identifier = 'ftrack-connect-launch-hieroplayer'
    label = 'hieroplayer'

    def __init__(self, session,  application_store, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchHieroPlayerAction, self).__init__(
            session=session,
            application_store=application_store,
            launcher=launcher,
            priority=0
        )

    def _launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()

        return self.launcher.launch(
            applicationIdentifier, context
        )


class ApplicationStore(ftrack_application_launcher.ApplicationStore):

    def _discover_applications(self):

        applications = []

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._search_filesystem(
                expression=prefix + ['Nuke.*', 'HieroPlayer\d[\w.]+.app'],
                label='Review with HieroPlayer',
                variant='{version}',
                applicationIdentifier='hieroplayer_{variant}_with_review',
                icon='hieroplayer',
                integrations={'legacy':['ftrack-connect-hieroplayer']}
            ))

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

            version_expression = re.compile(
                r'Nuke(?P<version>[\d.]+[\w\d.]*)'
            )

            applications.extend(self._search_filesystem(
                expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
                versionExpression=version_expression,
                label='Review with HieroPlayer',
                variant='{version}',
                applicationIdentifier='hieroplayer_{variant}_with_review',
                icon='hieroplayer',
                launchArguments=['--player'],
                integrations={'legacy':['ftrack-connect-hieroplayer']}
            ))

        elif self.current_os == 'linux':

            applications.extend(self._search_filesystem(
                expression=['/', 'usr', 'local', 'Nuke.*', 'Nuke\d.+'],
                label='Review with HieroPlayer',
                variant='{version}',
                applicationIdentifier='hieroplayer_{variant}_with_review',
                icon='hieroplayer',
                launchArguments=['--player'],
                integrations={'legacy':['ftrack-connect-hieroplayer']}
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications

def register(session, **kw):
    '''Register hooks.'''

    logger = logging.getLogger(
        'ftrack_plugin:ftrack_connect_hieroplayer_hook.register'
    )

    # Validate that registry is ftrack.EVENT_HANDLERS. If not, assume that
    # register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    # Create store containing applications.
    application_store = ApplicationStore(session)

    # Create a launcher with the store containing applications.
    launcher = ApplicationLauncher(
        application_store
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchHieroPlayerAction(session, application_store, launcher)
    action.register()
