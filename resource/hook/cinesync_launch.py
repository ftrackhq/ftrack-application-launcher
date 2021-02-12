# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import sys
import logging

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(sources)


import subprocess
import ftrack_api
import ftrack_application_launcher


class CinesyncActionLauncher(ftrack_application_launcher.ApplicationLaunchAction):
    '''Cinesync launch action.'''

    context = ['AssetVersionList', 'AssetVersion', 'ReviewSession']
    identifier = 'ftrack-connect-cinesync-application'
    label = 'cineSync'

    def __init__(self, application_store, session):

        super(CinesyncActionLauncher, self).__init__(
            session=session,
            application_store=application_store
        )

        self.allowed_entity_types_fn = {
            self.context[0]: self._get_version_from_lists,
            self.context[1]: self._get_version,
            self.context[2]: self._get_version_from_review
        }

    def _get_version(self, entity_id):
        '''Return a single *entity_id* from version'''
        return [entity_id]

    def _get_version_from_lists(self, entity_id):
        '''Return list of version ids from AssetVersionList from *entity_id*'''

        asset_version_lists = self.session.query(
            'AssetVersionList where id is {0}'.format(entity_id)
        ).one()

        result = [
            version['id'] for version in asset_version_lists['items']
        ]

        return result

    def _get_version_from_review(self, entity_id):
        '''Return list of versions ids from ReviewSession from *entity_id*'''

        review_session = self.session.query(
            'select review_session_objects.version_id'
            ' from ReviewSession where id is {0}'.format(entity_id)
        ).one()

        result = []
        for version_object in review_session['review_session_objects']:
            result.append(version_object['version_id'])

        return result

    # def is_valid_selection(self, selection):
    #     '''Check whether the given *selection* is valid'''
    #     results = []
    #
    #     for selected_item in selection:
    #         entity_type = selected_item.get('entityType')
    #         entity_id = selected_item.get('entityId')
    #
    #         allowed_entity_types = self.allowed_entity_types_fn.keys()
    #         resolved_entity_type = self.session.get(entity_type, entity_id).entity_type
    #
    #         if resolved_entity_type in allowed_entity_types:
    #             results.append(selected_item)
    #
    #     return results

    def get_versions(self, selection):
        '''Return versions given the *selection*'''
        results = []

        for selected_item in selection:
            entity_type = self._get_entity_type(selected_item)
            entity_id = selected_item.get('entityId')
            resolved_entity_type = self.session.get(entity_type, entity_id).entity_type
            version_id_fn = self.allowed_entity_types_fn[resolved_entity_type]
            versions = version_id_fn(entity_id)
            results.extend(versions)

        return results

    def get_selection(self, event):
        '''From a raw *event* dictionary, extract the selected entities.'''

        data = event['data']
        selection = data.get('selection', [])
        return selection

    # def discover(self, session, entities, event):
    #     '''Return true if we can handle the selected entities.
    # 
    #     *session* is a `ftrack_api.Session` instance
    # 
    #     *entities* is a list of tuples each containing the entity type and the
    #     entity id. If the entity is a hierarchical you will always get the
    #     entity type TypedContext, once retrieved through a get operation you
    #     will have the "real" entity type ie. example Shot, Sequence
    #     or Asset Build.
    # 
    #     *event* the unmodified original event'''
    # 
    #     self.logger.warning('DISCOVERIIIIIIIIIIIIIIIIIIING')
    # 
    #     applications = self.application_store.applications
    #     if not applications:
    #         self.logger.warning('No application found form {}'.format(self))
    #         return False
    # 
    #     selection = self.get_selection(event)
    #     if not selection:
    #         self.logger.debug(
    #             'No entity selected.'
    #         )
    #         return False
    # 
    #     selection = self.get_selection(event)
    #     if not self.is_valid_selection(selection):
    #         valid_types = self.allowed_entity_types_fn.keys()
    #         self.logger.warning(
    #             'No valid entity type selected. Valid types: {0}.'.format(
    #                 ', '.join(valid_types)
    #             )
    #         )
    #         return False
    # 
    #     applications = sorted(
    #         applications, key=lambda application: application['label']
    #     )
    # 
    #     self.variant = applications[0].get('variant', None)
    #     return True

    def open_url(self, asset_version_list):
        ''' Open cinesync url with given *asset_version_list*'''
        url = 'cinesync://ftrack/addVersion?assetVersionList={0}'.format(
            ','.join(asset_version_list)
        )

        self.logger.debug('Opening Cynesinc Url: {0}'.format(url))

        if self.current_os == 'darwin':
            subprocess.call(['open', url])

        elif self.current_os == 'windows':
            subprocess.call(['cmd', '/c', 'start', '', '/b', url])

        elif self.current_os == 'linux':
            subprocess.call(['xdg-open', url])

    def _launch(self, event):
        '''rework logic to run custom launch function'''
        args = self._translate_event(
            self.session, event
        )

        response = self.launch(
            self.session, *args
        )

        return self._handle_result(
            self.session, response, *args
        )

    def launch(self, session, entities, event):
        '''Callback method for the action.

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event

        '''
        # Prevent further processing by other listeners.
        event.stop()
        versions = self.get_versions(event['data']['selection'])
        self.open_url(versions)
        return True


class CinesyncApplicationStore(ftrack_application_launcher.ApplicationStore):
    '''Discover and store available applications on this host.'''

    def _discover_applications(self):
        '''Return list of applications that can be launched from this host.'''
        applications = []

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._search_filesystem(
                expression=prefix + ['cineSync.app'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cinesync',
                versionExpression=r'(?P<version>.*)'
            ))

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._search_filesystem(
                expression=prefix + ['cineSync', 'cineSync.exe'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cinesync'
            ))

        elif self.current_os == 'linux':
            # TODO: Find consistent way to decide where the application is
            # installed. Placeholder for linux
            return

        self.logger.debug('Application found: {0}'.format(applications))
        return applications


def register(session, **kw):
    '''Register hooks for ftrack connect cinesync plugins.'''

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    application_store = CinesyncApplicationStore(session)
    # Create action and register to respond to discover and launch events.
    action = CinesyncActionLauncher(application_store, session)
    action.register()
