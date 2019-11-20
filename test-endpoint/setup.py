# Always prefer setuptools over distutils:
from setuptools import setup, find_packages
from setuptools.command.install import install
from subprocess import Popen


with open('version', 'r') as version_file:
    __version__ = version_file.read().strip()


def runCmd(command):
    try:
        print('RunCmd: ' + command)
        process = Popen(command, shell=True, universal_newlines=True)
        process.wait()
    except Exception as e:
        print('Error: ' + e)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        runCmd('sudo cp test_ixendpoint/files/etc/systemd/test-endpoint.service /lib/systemd/system/')
        runCmd('cp test_ixendpoint/files/run /trinity/endpoint/test-endpoint')
        runCmd('sudo chmod 755 /trinity/endpoint/test-endpoint/run')
        runCmd('sudo systemctl daemon-reload')
        runCmd('sudo service test-endpoint start')
        install.run(self)


setup(
    name='test-endpoint',
    url='https://gitlab.trinity.cc/endpoint/test-endpoint',
    version=__version__,
    packages=find_packages(exclude=['doc', 'src']),
    include_package_data=True,
    package_data={
        'version': ['version'],
    },
    entry_points={
        'console_scripts': [
            'test-endpoint=test_ixendpoint.client:main',
            'test-iperf=test_ixendpoint.iperf:main'
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
    install_requires=[
        'celery',
        'psutil',
        'test-common',
    ]
)
