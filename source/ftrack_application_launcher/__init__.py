# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import pprint
import re
import os
import subprocess
import collections
import base64
import json
import logging
from operator import itemgetter
from distutils.version import LooseVersion

import ftrack_api
from ftrack_action_handler.action import BaseAction


#: Default expression to match version component of executable path.
#: Will match last set of numbers in string where numbers may contain a digit
#: followed by zero or more digits, periods, or the letters 'a', 'b', 'c' or 'v'
#: E.g. /path/to/x86/some/application/folder/v1.8v2b1/app.exe -> 1.8v2b1
DEFAULT_VERSION_EXPRESSION = re.compile(
    r'(?P<version>\d[\d.vabc]*?)[^\d]*$'
)


def prependPath(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    try:
        environment[key] = (
            os.pathsep.join([
                path, environment[key]
            ])
        )
    except KeyError:
        environment[key] = path

    return environment


def appendPath(path, key, environment):
    '''Append *path* to *key* in *environment*.'''
    try:
        environment[key] = (
            os.pathsep.join([
                environment[key], path
            ])
        )
    except KeyError:
        environment[key] = path

    return environment


class ApplicationStore(object):
    '''Discover and store available applications on this host.'''

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session):
        '''Instantiate store and discover applications.'''
        super(ApplicationStore, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._session = session

        # Discover applications and store.
        self.applications = self._discoverApplications()

    def getApplication(self, identifier):
        '''Return first application with matching *identifier*.

        *identifier* may contain a wildcard at the end to match the first
        substring matching entry.

        Return None if no application matches.

        '''
        hasWildcard = identifier[-1] == '*'
        if hasWildcard:
            identifier = identifier[:-1]

        for application in self.applications:
            if hasWildcard:
                if application['identifier'].startswith(identifier):
                    return application
            else:
                if application['identifier'] == identifier:
                    return application

        return None

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name',
                'variant': 'version',
                'description': 'description',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications

    def _searchFilesystem(self, expression, label, applicationIdentifier,
                          versionExpression=None, icon=None,
                          launchArguments=None, variant='', 
                          description=None):
        '''
        Return list of applications found in filesystem matching *expression*.

        *expression* should be a list of regular expressions to match against
        path segments up to the executable. Each path segment traversed will be
        matched against the corresponding expression part. The first expression
        part must not contain any regular expression syntax and must match
        directly to a path existing on disk as it will form the root of the
        search. Example::

            ['C:\\', 'Program Files.*', 'Company', 'Product\d+', 'product.exe']

        *versionExpression* is a regular expression used to find the version of
        *the application. It will be applied against the full matching path of
        *any discovered executable. It must include a named 'version' group
        *which can be used in the label and applicationIdentifier templates.

        For example::

            '(?P<version>[\d]{4})'

        If not specified, then :py:data:`DEFAULT_VERSION_EXPRESSION` will be
        used.

        *label* is the label the application will be given. *label* should be on
        the format "Name of app".

        *applicationIdentifier* should be on the form
        "application_name_{version}" where version is the first match in the
        regexp.

        *launchArguments* may be specified as a list of arguments that should
        used when launching the application.

        *variant* can be used to differentiate between different variants of
        the same application, such as versions. Variant can include '{version}'
        which will be replaced by the matched version.

        *description* can be used to provide a helpful description for the
        user.
        '''
        applications = []

        if versionExpression is None:
            versionExpression = DEFAULT_VERSION_EXPRESSION
        else:
            versionExpression = re.compile(versionExpression)

        pieces = expression[:]
        start = pieces.pop(0)
        if sys.platform == 'win32':
            # On Windows C: means current directory so convert roots that look
            # like drive letters to the C:\ format.
            if start and start[-1] == ':':
                start += '\\'

        if not os.path.exists(start):
            raise ValueError(
                'First part "{0}" of expression "{1}" must match exactly to an '
                'existing entry on the filesystem.'
                .format(start, expression)
            )

        expressions = map(re.compile, pieces)
        expressionsCount = len(expressions)

        for location, folders, files in os.walk(start, topdown=True, followlinks=True):
            level = location.rstrip(os.path.sep).count(os.path.sep)
            expression = expressions[level]

            if level < (expressionsCount - 1):
                # If not yet at final piece then just prune directories.
                folders[:] = [folder for folder in folders
                              if expression.match(folder)]
            else:
                # Match executable. Note that on OSX executable might equate to
                # a folder (.app).
                for entry in folders + files:
                    match = expression.match(entry)
                    if match:
                        # Extract version from full matching path.
                        path = os.path.join(start, location, entry)

                        versionMatch = versionExpression.search(path)
                        if versionMatch:
                            version = versionMatch.group('version')
                            
                            try:
                                loose_version = LooseVersion(version)
                            except AttributeError:
                                self.logger.warning(
                                    'Could not parse version'
                                    ' {0} from {1}'.format(
                                        version, path
                                    )
                                )
                                # If no version is found, let's set it to a default.
                                loose_version = LooseVersion('0.0.0')

                            applications.append({
                                'identifier': applicationIdentifier.format(
                                    version=version
                                ),
                                'path': path,
                                'launchArguments': launchArguments,
                                'version': loose_version,
                                'label': label.format(version=version),
                                'icon': icon,
                                'variant': variant.format(version=version),
                                'description': description
                            })
                        else:
                            self.logger.debug(
                                'Discovered application executable, but it '
                                'does not appear to o contain required version '
                                'information: {0}'.format(path)
                            )

                # Don't descend any further as out of patterns to match.
                del folders[:]

        return sorted(applications, key=itemgetter('version'), reverse=True)


class ApplicationLauncher(object):
    '''Launch applications described by an application store.

    Launched applications are started detached so exiting current process will
    not close launched applications.

    '''

    @property
    def location(self):
        '''Return current location.'''
        return self._session.pick_location()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, applicationStore):
        '''Instantiate launcher with *applicationStore* of applications.

        *applicationStore* should be an instance of :class:`ApplicationStore`
        holding information about applications that can be launched.

        '''
        super(ApplicationLauncher, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.applicationStore = applicationStore
        self._session = applicationStore.session

    def launch(self, applicationIdentifier, context=None):
        '''Launch application matching *applicationIdentifier*.

        *context* should provide information that can guide how to launch the
        application.

        Return a dictionary of information containing:

            success - A boolean value indicating whether application launched
                      successfully or not.
            message - Any additional information (such as a failure message).

        '''
        # Look up application.
        applicationIdentifierPattern = applicationIdentifier

        application = self.applicationStore.getApplication(
            applicationIdentifierPattern
        )

        if application is None:
            return {
                'success': False,
                'message': (
                    '{0} application not found.'
                    .format(applicationIdentifier)
                )
            }

        # Construct command and environment.
        command = self._getApplicationLaunchCommand(application, context)
        environment = self._getApplicationEnvironment(application, context)

        # Environment must contain only strings.
        self._conformEnvironment(environment)

        success = True
        message = '{0} application started.'.format(application['label'])

        try:
            options = dict(
                env=environment,
                close_fds=True
            )

            # Ensure that current working directory is set to the root of the
            # application being launched to avoid issues with applications
            # locating shared libraries etc.
            applicationRootPath = os.path.dirname(application['path'])
            options['cwd'] = applicationRootPath

            # Ensure subprocess is detached so closing connect will not also
            # close launched applications.
            if sys.platform == 'win32':
                options['creationflags'] = subprocess.CREATE_NEW_CONSOLE
            else:
                options['preexec_fn'] = os.setsid

            launchData = dict(
                command=command,
                options=options,
                application=application,
                context=context
            )

            self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic='ftrack.connect.application.launch',
                    data=launchData
                ),
                synchronous=True
            )

            # Reset variables passed through the hook since they might
            # have been replaced by a handler.
            command = launchData['command']
            options = launchData['options']
            application = launchData['application']
            context = launchData['context']

            self.logger.debug(
                'Launching {0} with options {1}'.format(command, options)
            )
            process = subprocess.Popen(command, **options)

        except (OSError, TypeError):
            self.logger.exception(
                '{0} application could not be started with command "{1}".'
                .format(applicationIdentifier, command)
            )

            success = False
            message = '{0} application could not be started.'.format(
                application['label']
            )

        else:
            self.logger.debug(
                '{0} application started. (pid={1})'.format(
                    applicationIdentifier, process.pid
                )
            )

        return {
            'success': success,
            'message': message
        }

    def _getApplicationLaunchCommand(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        command = None

        if sys.platform in ('win32', 'linux2'):
            command = [application['path']]

        elif sys.platform == 'darwin':
            command = ['open', application['path']]

        else:
            self.logger.warning(
                'Unable to find launch command for {0} on this platform.'
                .format(application['identifier'])
            )

        # Add any extra launch arguments if specified.
        launchArguments = application.get('launchArguments')
        if launchArguments:
            command.extend(launchArguments)

        return command

    def _findLatestComponent(self, entityId, entityType, extension=''):
        '''Return latest published component from *entityId* and *entityType*.

        *extension* can be used to find suitable components by matching with
        their file system path.

        '''
        if entityType == 'task':
            versions = self.session.query(
                'select components from AssetVersion where task.id is {}'.format(
                    entityId
                )
            ).all()
        elif entityType == 'assetversion':
            versions = [
                self.session.query(
                    'select components from AssetVersion where id is {}'.format(
                        entityId
                    )
                )
            ]
        else:
            self.logger.debug(
                (
                    'Unable to find latest version from entityId={entityId} '
                    'with entityType={entityType}.'
                ).format(
                    entityId=entityId,
                    entityType=entityType
                )
            )
            return None

        lastDate = None
        latestComponent = None
        for version in versions:
            for component in version['components']:
                fileSystemPath = self.location.get_filesystem_path(component)
                if fileSystemPath and fileSystemPath.endswith(extension):
                    if (
                        lastDate is None or
                        version.getDate() > lastDate
                    ):
                        latestComponent = component
                        lastDate = version.getDate()

        return latestComponent

    def _getApplicationEnvironment(
        self, application, context=None
    ):
        '''Return mapping of environment for *application* using *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        # Copy all environment variables to new environment and strip the once
        # we know cause problems if copied.
        environment = os.environ.copy()

        environment.pop('PYTHONHOME', None)
        environment.pop('FTRACK_EVENT_PLUGIN_PATH', None)

        # Add FTRACK_EVENT_SERVER variable.
        environment = prependPath(
            self.session.event_hub.get_server_url(),
            'FTRACK_EVENT_SERVER', environment
        )

        egg_dependencies = [egg_path for egg_path in sys.path if egg_path.endswith('.egg')]

        for dependency in egg_dependencies:
            self.logger.debug('Adding {} to PYTHOPATH'.format(dependency))
            environment = prependPath(
                dependency, 'PYTHONPATH', environment
            )

        # Add ftrack connect event to environment.
        if context is not None:
            try:
                applicationContext = base64.b64encode(
                    json.dumps(
                        context
                    )
                )
            except (TypeError, ValueError):
                self.logger.exception(
                    'The eventData could not be converted correctly. {0}'
                    .format(context)
                )
            else:
                environment['FTRACK_CONNECT_EVENT'] = applicationContext

        return environment

    def _conformEnvironment(self, mapping):
        '''Ensure all entries in *mapping* are strings.

        .. note::

            The *mapping* is modified in place.

        '''
        if not isinstance(mapping, collections.MutableMapping):
            return

        for key, value in mapping.items():
            if isinstance(value, collections.Mapping):
                self._conformEnvironment(value)
            else:
                value = str(value)

            del mapping[key]
            mapping[str(key)] = value


class ApplicationLaunchAction(BaseAction)
    context_type = []

    @property
    def session(self):
        '''Return convenient exposure of the self._session reference.'''
        return self._session

    def __init__(self, session, application_store, launcher):
        super(LaunchApplicationAction, self).__init__(session)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.application_store = application_store
        self.launcher = launcher

    def validate_selection(self, entities):
        '''Return True if the selection is valid.

        Utility method to check *entities* validity.

        '''
        if not self.context_type:
            raise ValueError('No valid context type set for discovery')

        if not entities:
            return False

        entity_type, entity_id = entities[0]
        if entity_type in self.context_type:
            return True

        return False

    def _discover(self, event):
        if not self.validate_selection(entities):
            return

        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            application_identifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'icon': application.get('icon', 'default'),
                'variant': application.get('variant', None),
                'applicationIdentifier': application_identifier
            })

        return {
            'items': items
        }

    def _launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        event.stop()

        if not self.validate_selection(
            event['data'].get('selection', [])
        ):
            return

        application_identifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            application_identifier, context
        )

    def register(self):
        '''Register discover actions on logged in user.'''
        
        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )