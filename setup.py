from setuptools import setup, find_packages

setup(
    name='proj',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[], 
    entry_points={ 
        'console_scripts': ['proj = proj.__main__:main' ] 
    },
)
