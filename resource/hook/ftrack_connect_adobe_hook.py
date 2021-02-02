# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import tempfile
import os
import shutil
import re

import subprocess
import ftrack_api
import ftrack_application_launcher


#: Custom version expression to match versions `2015.5` and `2015`
#  as distinct versions.
ADOBE_VERSION_EXPRESSION = re.compile(
    r'(?P<version>\d[\d.]*)[^\w\d]'
)


class LaunchAction(ftrack_application_launcher.ApplicationLaunchAction):
    '''Adobe plugins discover and launch action.'''
    context = ['Task']
    identifier = 'ftrack-connect-launch-adobe'

    def __init__(self, session,  applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchAction, self).__init__(session,  applicationStore, launcher)

    def _discover(self, event):
        '''Return discovered applications.'''
        selection = event['data'].get('selection', [])
        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'description': application.get('description', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

            if selection:
                items.append({
                    'actionIdentifier': self.identifier,
                    'label': label,
                    'variant': '{variant} with latest version'.format(
                        variant=application.get('variant', '')
                    ),
                    'description': application.get('description', None),
                    'icon': application.get('icon', 'default'),
                    'launchWithLatest': True,
                    'applicationIdentifier': applicationIdentifier
                })

        return {
            'items': items
        }

    def _launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        # Prevent further processing by other listeners.
        # TODO: Only do this when actually have managed to launch a relevant
        # application.
        event.stop()

        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']
        selection = context.get('selection', [])

        # If the selected entity is an asset version, change the selection
        # to parent task/shot instead since it is not possible to publish
        # to an asset version in ftrack connect.
        if (
            selection and
            selection[0]['entityType'] == 'assetversion'
        ):
            # assetVersion = ftrack.AssetVersion(
            #     selection[0]['entityId']
            # )

            asset_version = self.session.get('AssetVersion', selection[0]['entityId'])
            entityId = asset_version['task_id']

            if not entityId:
                asset = asset_version['asset']
                entity = asset['parent']
                entityId = entity['id']

            context['selection'] = [{
                'entityId': entityId,
                'entityType': 'task'
            }]

        return self.launcher.launch(
            applicationIdentifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        # Set version number to empty string since we don't know the version
        # of the plugins at the moment. Once ExManCMD is bundled with Connect
        # we can update this to return information about installed extensions.
        return [
            dict(
                name='ftrack connect photoshop',
                version='-'
            ), dict(
                name='ftrack connect premiere',
                version='-'
            ), dict(
                name='ftrack connect after effects',
                version='-'
            ), dict(
                name='ftrack connect illustrator',
                version='-'
            )
        ]


class ApplicationStore(ftrack_application_launcher.ApplicationStore):

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

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._search_filesystem(
                expression=prefix + [
                    r'Adobe Photoshop ((?:CC )?\d+)', r'Adobe Photoshop ((?:CC )?\d+)\.app'
                ],
                label='Photoshop',
                variant='CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='photoshop'
            ))

            applications.extend(self._search_filesystem(
                expression=prefix + [
                    r'Adobe Premiere Pro ((?:CC )?\d+)', r'Adobe Premiere Pro ((?:CC )?\d+)\.app'
                ],
                label='Premiere Pro',
                variant='CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='premiere'
            ))

            applications.extend(self._search_filesystem(
                expression=prefix + [
                    r'Adobe After Effects ((?:CC )?\d+)', r'Adobe After Effects ((?:CC )?\d+)\.app'
                ],
                label='After Effects',
                variant='CC {version}',
                applicationIdentifier='after_effects_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='after_effects'
            ))

            applications.extend(self._search_filesystem(
                expression=prefix + [
                    r'Adobe Illustrator ((?:CC )?\d+)', r'Adobe Illustrator ?((?:CC )?\d+)?\.app'
                ],
                label='Illustrator',
                variant='CC {version}',
                applicationIdentifier='illustrator_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='illustrator'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._search_filesystem(
                expression=(
                    prefix +
                    ['Adobe', r'Adobe Photoshop ((?:CC )?\d+)',
                     'Photoshop.exe']
                ),
                label='Photoshop',
                variant='CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='photoshop'
            ))

            applications.extend(self._search_filesystem(
                expression=(
                    prefix +
                    ['Adobe', r'Adobe Premiere Pro ((?:CC )?\d+)',
                     'Adobe Premiere Pro.exe']
                ),
                label='Premiere Pro',
                variant='CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='premiere'
            ))

            applications.extend(self._search_filesystem(
                expression=(
                    prefix +
                    ['Adobe', r'Adobe After Effects ((?:CC )?\d+)', 'Support Files',
                     'AfterFX.exe']
                ),
                label='After Effects',
                variant='CC {version}',
                applicationIdentifier='after_effects_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='after_effects'
            ))

            applications.extend(self._search_filesystem(
                expression=(
                    prefix +
                    ['Adobe', r'Adobe Illustrator ((?:CC )?\d+)', 'Support Files',
                     'Contents', 'Windows', 'Illustrator.exe']
                ),
                label='Illustrator',
                variant='CC {version}',
                applicationIdentifier='illustrator_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='illustrator'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_application_launcher.ApplicationLauncher):

    application_extensions = {
        'photoshop_cc': 'psd',
        'premiere_pro_cc': 'prproj',
        'after_effects_cc': 'aep',
        'illustrator_cc': 'ai',
    }

    def _get_temporary_copy(self, filePath):
        '''Copy file at *filePath* to a temporary directory and return path.

        .. note::

            The copied file does not retain the original files meta data or
            permissions.
        '''
        temporaryDirectory = tempfile.mkdtemp(prefix='ftrack_connect')
        targetPath = os.path.join(
            temporaryDirectory, os.path.basename(filePath)
        )
        shutil.copyfile(filePath, targetPath)
        return targetPath

    def _find_latest_component(self, entityId, entityType, extension=''):
        '''Return latest published component from *entityId* and *entityType*.

        *extension* can be used to find suitable components by matching with
        their file system path.

        '''
        self.logger.info('Looking for latest version of {} {} {}'.format(
            entityId, entityType, extension
        ))
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

        last_date = None
        latest_component = None
        for version in versions:
            for component in version['components']:
                file_system_path = self.location.get_filesystem_path(component)
                if file_system_path and file_system_path.endswith(extension):
                    if (
                            last_date is None or
                            version['date'] > last_date
                    ):
                        latest_component = component
                        last_date = version['date']

        return latest_component, file_system_path

    def _get_application_launch_command(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        context = context or {}

        command = super(
            ApplicationLauncher, self
        )._get_application_launch_command(
            application, context
        )

        if command is not None and context is not None:
            self.logger.debug(
                u'Launching action with context {0}'.format(
                    pprint.pformat(context)
                )
            )

            selection = context.get('selection')

            if selection and context.get('launchWithLatest', False):
                entity = selection[0]
                component = None

                for identifier, extension in self.application_extensions.items():
                    if application['identifier'].startswith(identifier):
                        component = self._find_latest_component(
                            entity['entityId'],
                            entity['entityType'],
                            extension
                        )
                        break

                if component is not None:
                    component_path = self.location.get_filesystem_path(component)
                    file_path = self._get_temporary_copy(
                        component_path
                    )
                    self.logger.info(
                        u'Launching application with file {0!r}'.format(
                            file_path
                        )
                    )
                    command.append(file_path)
                else:
                    self.logger.warning(
                        'Unable to find an appropriate component when '
                        'launching with latest version.'
                    )

        return command

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
        selection = context.get('selection', [])

        # If the selected entity is an asset version, change the selection
        # to parent task/shot instead since it is not possible to publish
        # to an asset version in ftrack connect.

        entity_type, entity_id = entities[0]
        resolved_entity = self.session.get(entity_type, entity_id)

        if (
            selection and
            resolved_entity.entity_type == 'AssetVersion'
        ):

            entityId = resolved_entity.get('task_id')

            if not entityId:
                asset = resolved_entity['asset']
                entity = asset['parent']

                entityId = entity['id']

            context['selection'] = [{
                'entityId': entityId,
                'entityType': 'task'
            }]

        return self.launcher.launch(
            application_identifier, context
        )


def register(api_object, **kw):
    '''Register hooks for Adobe plugins.'''

    if not isinstance(api_object, ftrack_api.session.Session):
        return

    applicationStore = ApplicationStore(api_object)

    launcher = ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(api_object, applicationStore, launcher)
    action.register()