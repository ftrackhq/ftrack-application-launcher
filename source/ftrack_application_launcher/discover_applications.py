import sys
import os
import json
import platform
import pprint
import logging
from ftrack_application_launcher import ApplicationStore, ApplicationLaunchAction, ApplicationLauncher


class DiscoverApplications(object):

    @property
    def current_os(self):
        return platform.system().lower()

    def __init__(self, session, applications_config_paths):
        super(DiscoverApplications, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # If a single path is passed by mistake, handle it here.
        if isinstance(applications_config_paths, basestring):
            applications_config_paths = [applications_config_paths]

        self._actions = []

        self._session = session
        configurations = self._parse_configurations(applications_config_paths)
        self._build_launchers(configurations)

    def _parse_configurations(self, config_paths):

        loaded_filtered_files = []
        for config_path in config_paths:
            if not os.path.exists(config_path) or not os.path.isdir(config_path):
                self.logger.warning(
                    '{} directory cannot be found.'.format(config_path)
                )
                continue

            files = os.listdir(config_path)
            json_configs = [
                open(os.path.join(config_path, config), 'r').read()
                for config in files
                if config.endswith('json')
            ]

            for config in json_configs:
                try:
                    loaded_filtered_files.append(json.loads(config))
                except Exception as error:
                    self.logger.warning(
                        '{} could not be loaded due to {}'.format(
                            config, error
                        )
                    )
        
        return loaded_filtered_files

    def _build_launchers(self, configurations):
        for config in configurations:
            store = ApplicationStore(self._session)
            # extract data from app config
            search_path = config['search_path'].get(self.current_os)
            if not search_path:
                self.logger.warning(
                    'No entry found for os: {} in config {}'.format(
                        self.current_os, config['label']
                    )
                )
                continue

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
            self.logger.info('launch with latest: {}, extension {}'.format(launch_with_latest, extension))
            # add extra information to the launcher
            for application in applications:
                if launch_with_latest and extension:
                    application['launchWithLatest'] = launch_with_latest
                    application['extension'] = extension

            self.logger.info(
                'Discovered applications {}'.format(
                    pprint.pformat(applications)
                )
            )
            store.applications = applications

            launcher = ApplicationLauncher(store)

            NewAction = type(
                'ApplicationLauncherAction-{}'.format(config['label']),
                (ApplicationLaunchAction,),
                {
                    'label': config['label'],
                    'identifier': config['identifier'],
                    'variant': config['variant'],
                    'context': config['context']
                }
            )
            action = NewAction(self._session, store, launcher)

            self.logger.info('Creating App launcher {}'.format(action))

            self._actions.append(action)

    def register(self):
        for action in self._actions:
            action.register()



