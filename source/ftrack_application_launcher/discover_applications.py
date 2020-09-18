import sys
import json
import platform
from ftrack_application_launcher import ApplicationStore, ApplicationLaunchAction, ApplicationLauncher



class DiscoverApplications(object)

    @property
    def current_os(self):
        return platform.system.lower()

    def __init__(session, applications_config_path):
        self._session = session
        configurations = self._sarch_configurations(applications_config_path)
        stores = self._build_stores(configurations)

    def _sarch_configurations(self):
        if not os.path.exists(self._config_path):
            raise ValueError(
                'config path {} does not exists'.format(self._config_path)
            )
        files = os.listdir(self._config_path)
        filtered_files = [config for config in files if config.endswith('json')]
        return map(json.loads, filtered_files)

    def _discover_applications(self, application_config):

    def _build_stores(self, configurations):
        for config in configurations:
            applications = []
            store = ApplicationStore(self._session)
            # extract data from app config
            applicationIdentifier = config['applicationIdentifier']
            search_path = config['search_path'][self.current_os]
            prefix = search_path['prefix']
            expression = search_path['expression']

            store._searchFilesystem(
                expression=prefix + expression,
                label=config['label'],
                applicationIdentifier = config['applicationIdentifier']
                icon=config['icon'],
                variant=config['variant']
            )



