# type: ignore

from setuptools import setup, find_packages

setup(
    name='proj',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'typing-extensions',
    ], 
    entry_points={ 
        'console_scripts': ['proj = proj.__main__:entrypoint' ] 
    },
)
