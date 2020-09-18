import os
import sys


cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(sources)

import ftrack_api
from ftrack_application_launcher.discover_applications import DiscoverApplications

configs = os.environ.setdefault(
    'FTRACK_APPLICATION_LAUNCHER_CONFIG_PATH',
    os.path.abspath(os.path.join('resource', 'config'))
)

def register(api_object, **kw):
    '''Register hooks.'''
    # Validate that registry is the event handler registry. If not,
    # assume that register is being called to regiter Locations or from a new
    # or incompatible API, and return without doing anything.

    if not isinstance(api_object, ftrack_api.Session):
        return



    print('using config path: {}'.format(configs))
    # Create store containing applications.
    applications = DiscoverApplications(api_object, configs)
    applications.register()
