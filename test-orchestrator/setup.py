# Always prefer setuptools over distutils:
from setuptools import setup, find_packages
from setuptools.command.install import install

with open('version', 'r') as version_file:
    __version__ = version_file.read().strip()


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)


setup(
    # --- METADATA ---
    name='test-orchestrator',

    url='https://gitlab.trinity.cc/endpoint/test-orchestrator',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html

    version=__version__,


    # --- PACKAGING ---

    packages=find_packages(exclude=['doc', 'src']),

    include_package_data=True,
    package_data={'version': ['version']},

    entry_points={
        'console_scripts': [
                'test-orchestrator=test_orchestrator.orchestrator:main',
                'test-trigger=test_orchestrator.trigger:main'
            ],
        },

    cmdclass={
        'install': PostInstallCommand,
    },


    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'celery',
        'test-common',
        'cassandra-migrate'
        ]
)
