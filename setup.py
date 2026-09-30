# type: ignore

from setuptools import setup, find_packages

setup(
    name='proj',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'tomli >= 1.1.0 ; python_version < "3.11"',
    ],
    extras_require={
        "progressbar": [
            "enlighten>1.0.0,<2.0.0"
        ],
        "test": [
            "pytest>=8.0.0,<10.0.0",
            "pytest-skip-slow==0.0.5",
            "typing-extensions>=4.0.0,<5.0.0",
            "nclib>=1.0.0,<2.0.0",
        ],
        "xdist": [
            "pytest-xdist>=3.0.0,<4.0.0",
        ]
    },
    entry_points={
        'console_scripts': ['proj = proj.__main__:entrypoint' ]
    },
)
