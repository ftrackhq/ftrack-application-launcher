# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import pprint
import re
import os
import subprocess
import collections
import base64
import getpass
import json
import logging
import platform
from operator import itemgetter
from distutils.version import LooseVersion

import ftrack_api
from ftrack_action_handler.action import BaseAction
from ftrack_application_launcher.configure_logging import configure_logging


configure_logging(__name__)


#: Default expression to match version component of executable path.
#: Will match last set of numbers in string where numbers may contain a digit
#: followed by zero or more digits, periods, or the letters 'a', 'b', 'c' or 'v'
#: E.g. /path/to/x86/some/application/folder/v1.8v2b1/app.exe -> 1.8v2b1
DEFAULT_VERSION_EXPRESSION = re.compile(
    r'(?P<version>\d[\d.vabc]*?)[^\d]*$'
)


def prepend_path(path, key, environment):
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


def append_path(path, key, environment):
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
    def current_os(self):
        return platform.system().lower()

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
        self.applications = self._discover_applications()

    def get_application(self, identifier):
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

    def _discover_applications(self):
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

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

        return applications

    def _search_filesystem(self, expression, label, applicationIdentifier,
                           versionExpression=None, icon=None,
                           launchArguments=None, variant='',
                           description=None, integrations=None):
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

        if self.current_os == 'windows':
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

        expressions = list(map(re.compile, pieces))
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
                        loose_version = LooseVersion('0.0.0')

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
                        variant_str = variant.format(version=str(loose_version))
                        if integrations:
                            variant_str = "{} | {}".format(variant_str, ':'.join(list(integrations.keys())))

                        application = {
                            'identifier': applicationIdentifier.format(
                                version=str(loose_version)
                            ),
                            'path': path,
                            'launchArguments': launchArguments,
                            'version': loose_version,
                            'label': label.format(version=str(loose_version)),
                            'icon': icon,
                            'variant': variant_str,
                            'description': description,
                            'integrations': integrations
                        }

                        applications.append(application)

                # Don't descend any further as out of patterns to match.
                del folders[:]

        results = sorted(applications, key=itemgetter('version'), reverse=True)
        self.logger.debug('Discovered applications {}'.format(results))
        return results


class ApplicationLauncher(object):
    '''Launch applications described by an application store.

    Launched applications are started detached so exiting current process will
    not close launched applications.

    '''

    @property
    def current_os(self):
        return platform.system().lower()

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

        application = self.applicationStore.get_application(
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
        command = self._get_application_launch_command(application, context)
        environment = self._get_application_environment(application, context)

        # Environment must contain only strings.
        self._conform_environment(environment)

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
            if self.current_os == 'windows':
                options['creationflags'] = subprocess.CREATE_NEW_CONSOLE
            else:
                options['preexec_fn'] = os.setsid

            launchData = dict(
                command=command,
                options=options,
                application=application,
                context=context,
                integration={
                    'name': None,
                    'version': None
                }
            )

            results = self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic='ftrack.connect.application.launch',
                    data=launchData
                ),
                synchronous=True
            )

            if not results:
                self.logger.error(
                    'No information returned from : {}.'.format(launchData)
                )

            env_dict = {}

            # parse integration returned from listeners.
            returned_integrations_names = set([result.get('integration', {}).get('name') for result in results])

            for integration_group, requested_integration_names in list(context.get('integrations', {}).items()):

                difference = set(requested_integration_names).difference(returned_integrations_names)

                if difference:
                    self.logger.info(
                        'Ignoring group {} as integration {} has not been discovered.'.format(
                            integration_group, difference
                        )
                    )
                    continue

                for requested_integration_name in requested_integration_names:

                    result = [
                        result for result in results
                        if result['integration']['name'] == requested_integration_name
                    ][0]

                    self.logger.info(
                        'Integration for group {}, have been found.'.format(integration_group)
                    )

                    envs = result.get('env', {})

                    if not envs:
                        self.logger.warning(
                            'No environments exported from integration {}'.format(
                                requested_integration_name
                            )
                        )
                        continue

                    self.logger.info(
                        'Merging environment variables for integration {}'.format(requested_integration_name)
                    )
                    env_dict.update(envs)

            # Reset variables passed through the hook since they might
            # have been replaced by a handler.
            command = launchData['command']
            options = launchData['options']
            application = launchData['application']
            context = launchData['context']
            options['env'].update(env_dict)

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

    def _get_application_launch_command(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        command = None
        context = context or {}

        if self.current_os in ('windows', 'linux'):
            command = [application['path']]

        elif self.current_os == 'darwin':
            command = ['open', application['path']]

        else:
            self.logger.warning(
                'Unable to find launch command for {0} on this platform.'
                .format(application['identifier'])
            )

        # Add any extra launch arguments if specified.
        AppLaunchArguments = application.get('launchArguments')
        if AppLaunchArguments:
            command.extend(AppLaunchArguments)

        CtxApplaunchArguments = context.get('launchArguments')
        if CtxApplaunchArguments:
            command.extend(CtxApplaunchArguments)

        return command

    def _find_latest_component(self, entityId, entityType, extension=''):
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

    def _get_application_environment(
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
        environment = prepend_path(
            self.session.event_hub.get_server_url(),
            'FTRACK_EVENT_SERVER', environment
        )

        laucher_dependencies = os.path.normpath(
            os.path.join(
                os.path.abspath(
                    os.path.dirname(__file__)
                ),
                '..'
            )
        )
        self.logger.debug('Adding {} to PYTHOPATH'.format(laucher_dependencies))
        environment = prepend_path(
            laucher_dependencies, 'PYTHONPATH', environment
        )

        # Add ftrack connect event to environment.
        if context is not None:
            try:
                applicationContext = base64.b64encode(
                    json.dumps(
                        context
                    ).encode("utf-8")
                )
            except (TypeError, ValueError):
                self.logger.exception(
                    'The eventData could not be converted correctly. {0}'
                    .format(context)
                )
            else:
                environment['FTRACK_CONNECT_EVENT'] = applicationContext

        return environment

    def _conform_environment(self, mapping):
        '''Ensure all entries in *mapping* are strings.

        .. note::

            The *mapping* is modified in place.

        '''
        if not isinstance(mapping, collections.MutableMapping):
            return

        for key, value in mapping.copy().items():
            if isinstance(value, collections.Mapping):
                self._conform_environment(value)
            else:
                value = str(value)

            del mapping[key]
            mapping[str(key)] = value


class ApplicationLaunchAction(BaseAction):
    context = []

    def __repr__(self):
        return "<label:{}|id:{}|ctx:{}>".format(
            self.label,
            self.identifier,
            ' '.join(self.context)
        )

    @property
    def session(self):
        '''Return convenient exposure of the self._session reference.'''
        return self._session

    def __init__(
            self, session, application_store, launcher, priority=sys.maxsize
    ):
        super(ApplicationLaunchAction, self).__init__(session)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.priority = priority
        self.application_store = application_store
        self.launcher = launcher

    def validate_selection(self, entities):
        '''Return True if the selection is valid.

        Utility method to check *entities* validity.

        '''
        if not self.context:
            raise ValueError('No valid context type set for discovery')

        if not entities:
            return False

        entity_type, entity_id = entities[0]
        resolved_entity_type = self.session.get(entity_type, entity_id).entity_type

        if resolved_entity_type in self.context:
            return True

        return False

    def _discover(self, event):

        entities, event = self._translate_event(self.session, event)
        if not self.validate_selection(
            entities
        ):
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
                'applicationIdentifier': application_identifier,
                'integrations': application.get('integrations'),
                'host': platform.node()
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

        entities, event = self._translate_event(self.session, event)

        if not self.validate_selection(
            entities
        ):
            return

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            application_identifier, context
        )

    def register(self):
        '''Register discover actions on logged in user.'''

        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover '
            'and source.user.username={0}'.format(
                self.session.api_user
            ),
            self._discover,
            priority=self.priority
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch '
            'and source.user.username={0} '
            'and data.actionIdentifier={1} '
            'and data.host={2}'.format(
                self.session.api_user,
                self.identifier,
                platform.node()
            ),
            self._launch,
            priority=self.priority
        )
