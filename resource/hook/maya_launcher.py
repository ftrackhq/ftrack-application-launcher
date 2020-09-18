import os
import sys
import re
import pprint

import ftrack_api

from ftrack_application_launcher import ApplicationStore, ApplicationLauncher, ApplicationLaunchAction


class MayaLaunchAction(ApplicationLaunchAction):
    context_type = ['task']


class MayaApplicationStore(ApplicationStore):

    def _check_maya_location(self):
        prefix = None

        maya_location = os.getenv('MAYA_LOCATION')

        if maya_location and os.path.isdir(maya_location):
            prefix = maya_location.split(os.sep)
            prefix[0] += os.sep

        return prefix

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']
            maya_location = self._check_maya_location()
            if maya_location:
                prefix = maya_location

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'maya.+', 'Maya.app'],
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']
            maya_location = self._check_maya_location()
            if maya_location:
                prefix = maya_location

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'Maya.+', 'bin', 'maya.exe'],
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        elif 'linux' in sys.platform:
            prefix = ['/', 'usr', 'autodesk', 'maya.+']
            maya_location = self._check_maya_location()
            if maya_location:
                prefix = maya_location

            maya_version_expression = re.compile(
                r'maya(?P<version>\d{4})'
            )

            applications.extend(self._searchFilesystem(
                expression=prefix + ['bin', 'maya$'],
                versionExpression=maya_version_expression,
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class MayaApplicationLauncher(ApplicationLauncher):

    def register(api_object, **kw):
        '''Register hooks.'''
        # Validate that registry is the event handler registry. If not,
        # assume that register is being called to regiter Locations or from a new
        # or incompatible API, and return without doing anything.
        if api_object is not isinstance(ftrack_api.Session):
            return

        # Create store containing applications.
        application_store = MayaApplicationStore()

        # Create a launcher with the store containing applications.
        launcher = ApplicationLauncher(application_store)

        # Create action and register to respond to discover and launch actions.
        action = MayaApplicationLauncher(application_store, launcher)
        action.register()
