import os
import sys
import logging

import ftrack_api
from ftrack_application_launcher.discover_applications import DiscoverApplications


def register(api_object, **kw):
    '''Register hooks.'''
    # Validate that registry is the event handler registry. If not,
    # assume that register is being called to regiter Locations or from a new
    # or incompatible API, and return without doing anything.

    if not isinstance(api_object, ftrack_api.Session):
        return

    cwd = os.path.dirname(__file__)
    default_config_path = os.path.abspath(os.path.join(cwd, '..', 'config'))

    # Ensure the config path is in form of a list
    config_paths = os.environ.setdefault(
        'FTRACK_APPLICATION_LAUNCHER_CONFIG_PATHS',
        default_config_path
    ).split(os.path.pathsep)

    logging.info('using config path: {}'.format(config_paths))
    # Create store containing applications.
    applications = DiscoverApplications(api_object, config_paths)
    applications.register()
