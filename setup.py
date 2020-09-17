# :coding: utf-8
# :copyright: Copyright (c) 2017-2020 ftrack

import os

from pkg_resources import DistributionNotFound, get_distribution
from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')


try:
    release = get_distribution('ftrack-action-handler').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])

except DistributionNotFound:
    # package is not installed
    VERSION = 'Unknown version'


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest

        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


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
        'write_to': 'source/ftrack-application-launcher/_version.py',
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
    cmdclass={
        'test': PyTest
    },
    zip_safe=True,
)
