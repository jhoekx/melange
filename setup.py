from setuptools import setup, find_packages

setup(
    name='Melange',
    version='1.0',
    packages=find_packages(),
    package_data={
        '': [
            'templates/*',
            'static/*',
        ]
    },
    license='GPLv3',
)
