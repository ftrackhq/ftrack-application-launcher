import sys
import os
import json
import platform
import logging
from ftrack_application_launcher import ApplicationStore, ApplicationLaunchAction, ApplicationLauncher


class DiscoverApplications(object):

    @property
    def current_os(self):
        return platform.system().lower()

    def __init__(self, session, applications_config_path):
        super(DiscoverApplications, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._actions = []

        self._session = session
        configurations = self._parse_configurations(applications_config_path)
        self._build_launchers(configurations)

    def _parse_configurations(self, config_path):
        if not os.path.exists(config_path):
            raise ValueError('{} does not exist'.format(config_path)
        )

        files = os.listdir(config_path)
        filtered_files = [
            open(os.path.join(config_path, config), 'r').read()
            for config in files
            if config.endswith('json')
        ]
        loaded_filtered_files = map(json.loads, filtered_files)
        return loaded_filtered_files

    def _build_launchers(self, configurations):
        for config in configurations:
            store = ApplicationStore(self._session)
            # extract data from app config
            search_path = config['search_path'][self.current_os]
            prefix = search_path['prefix']
            expression = search_path['expression']
            launch_with_latest = config.get('launch_with_latest', False)
            extension = config.get('extension')

            applications = store._searchFilesystem(
                expression=prefix + expression,
                label=config['label'],
                applicationIdentifier=config['applicationIdentifier'],
                icon=config['icon'],
                variant=config['variant'],
                launchArguments=config.get('launch_arguments'),
            )

            # add extra information to the launcher
            for application in applications:
                application['launchWithLatest'] = launch_with_latest
                application['extension'] = extension

            self.logger.info('Discovered applications {}'.format(applications))
            store.applications = applications

            launcher = ApplicationLauncher(store)

            action = ApplicationLaunchAction(
                self._session,
                store,
                launcher,
                config['label'],
                config['variant'],
                config['identifier'],
                config['context']
            )

            self.logger.info('Creating App launcher {}'.format(action))

            self._actions.append(action)

    def register(self):
        for action in self._actions:
            action.register()



