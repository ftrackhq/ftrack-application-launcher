# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import shutil

from pkg_resources import parse_version
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages, Command
import pip

if parse_version(pip.__version__) < parse_version('19.3.0'):
    raise ValueError('Pip should be version 19.3.0 or higher')

from pip._internal import main as pip_main


from pkg_resources import DistributionNotFound, get_distribution
from setuptools import find_packages, setup

PLUGIN_NAME = 'ftrack-application-launcher-{0}'

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

SOURCE_PATH = os.path.join(ROOT_PATH, 'source')

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')

STAGING_PATH = os.path.join(BUILD_PATH, PLUGIN_NAME)

HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')
CONFIG_PATH = os.path.join(RESOURCE_PATH, 'config')


try:
    release = get_distribution('ftrack-application-launcher').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])

except DistributionNotFound:
    # package is not installed
    VERSION = 'unknown-version'

STAGING_PATH = STAGING_PATH.format(VERSION)


class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy hook files
        shutil.copytree(
            CONFIG_PATH,
            os.path.join(STAGING_PATH, 'config')
        )

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )
        # Install local dependencies
        pip_main.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies')
            ]
        )

        # Generate plugin zip
        shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                PLUGIN_NAME.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )


version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2017-2020 ftrack

__version__ = {version!r}
'''

# Configuration.
setup(
    name='ftrack-application-launcher',
    version=VERSION,
    description='Base Class for handling application startup.',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack/ftrack-application-launcher',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    project_urls={
        'Source Code': 'https://bitbucket.org/ftrack/ftrack-application-launcher/src/{}'.format(VERSION),
    },
    setup_requires=[
        'lowdown >= 0.1.0, < 2',
        'setuptools>=30.3.0',
        'setuptools_scm',
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
    ],
    tests_require=['pytest >= 2.3.5, < 3'],
    use_scm_version={
        'write_to': 'source/ftrack_application_launcher/_version.py',
        'write_to_template': version_template,
    },
    install_requires=[
        'ftrack-python-api >= 1, < 3',
        'future >=0.16.0, < 1',
        'ftrack-action-handler'
    ],
    python_requires='>= 2.7.9, < 4.0',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
    cmdclass={'build_plugin':BuildPlugin},
    zip_safe=False,
)
