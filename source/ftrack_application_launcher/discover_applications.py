import sys
import os
import json
import platform
from ftrack_application_launcher import ApplicationStore, ApplicationLaunchAction, ApplicationLauncher


class DiscoverApplications(object):

    @property
    def current_os(self):
        return platform.system().lower()

    def __init__(self, session, applications_config_path):
        print('initialising discover application')
        self._actions = []

        self._session = session
        configurations = self._sarch_configurations(applications_config_path)
        stores = self._build_stores(configurations)

    def _sarch_configurations(self, config_path):
        if not os.path.exists(config_path):
            raise ValueError('{} does not exist'.format(config_path)
        )

        files = os.listdir(config_path)
        filtered_files = [open(os.path.join(config_path, config), 'r').read() for config in files if config.endswith('json')]
        loaded_filtered_files = map(json.loads, filtered_files)
        print(loaded_filtered_files)
        return loaded_filtered_files

    def _build_stores(self, configurations):
        for config in configurations:
            print('using config: {}'.format(config))
            applications = []
            store = ApplicationStore(self._session)
            # extract data from app config
            applicationIdentifier = config['applicationIdentifier']
            search_path = config['search_path'][self.current_os]
            prefix = search_path['prefix']
            expression = search_path['expression']

            applications = store._searchFilesystem(
                expression=prefix + expression,
                label=config['label'],
                applicationIdentifier = config['applicationIdentifier'],
                icon=config['icon'],
                variant=config['variant']
            )

            store.applications = applications

            launcher = ApplicationLauncher(store)

            Action = ApplicationLaunchAction
            Action.label = config['label']
            Action.variant = config['variant']
            Action.identifier = config['identifier']
            action = Action(self._session, store, launcher)
            action.context_type = config['discoverable_in']
            self._actions.append(action)

    def register(self):
        for action in self._actions:
            action.register()



