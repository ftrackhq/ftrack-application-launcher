
import sys
import pprint
import tempfile
import os
import shutil
import re

import platform

cwd = os.path.dirname(__file__)

sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))

sys.path.append(sources)


import ftrack_api
import ftrack_application_launcher



integrations = {'some': ['ftrack-connect-application']}

class LaunchAction(ftrack_application_launcher.ApplicationLaunchAction):
    context = ['Task', 'Project']
    identifier = 'ftrack-connect-launch-application'
    label = 'An Application'




class ApplicationStore(ftrack_application_launcher.ApplicationStore):

    def _discover_applications(self):
        applications = []

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._search_filesystem(
                expression=prefix + ['Something.*', 'Something\\d[\\w.]+.app'],
                label='An Application',
                variant='{version}',
                applicationIdentifier='an-application_{variant}',
                icon='an_application',
                integrations=integrations
            ))

        if self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._search_filesystem(
                expression=prefix + ["Something.*", "Something\\d.+.exe"],
                label='An Application',
                variant='{version}',
                applicationIdentifier='an-application_{variant}',
                versionExpression="(?P<version>[\\d.]+[vabc]+[\\dvabc.]*)",
                icon='an_application',
                integrations=integrations

            ))

        if self.current_os == 'linux':
            prefix = ["/", "usr", "local", "Something.*"]

            applications.extend(self._search_filesystem(
                expression=prefix +["Something.*", "Something\\d.+.exe"],
                label='An Application',
                variant='{version}',
                applicationIdentifier='an-application_{variant}',
                versionExpression="(?P<version>[\\d.]+[vabc]+[\\dvabc.]*)",
                icon='an_application',
                integrations=integrations
            ))

        return applications


class ApplicationLauncher(ftrack_application_launcher.ApplicationLauncher):
    '''Passthrough class'''


def register(session, **kw):
    '''Register hooks for Adobe plugins.'''

    if not isinstance(session, ftrack_api.session.Session):
        return

    application_store = ApplicationStore(session)

    launcher = ApplicationLauncher(application_store)

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(session, application_store, launcher)
    action.register()

