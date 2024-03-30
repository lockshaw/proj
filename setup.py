from setuptools import setup

setup(
    name='proj',
    version='0.0.1',
    packages=['proj'],
    install_requires=[], 
    entry_points={ 
        'console_scripts': ['proj = proj.__main__:main' ] 
    },
)
