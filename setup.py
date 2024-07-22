from setuptools import setup, find_packages

setup(
    name='bdupdater',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'bdupdater=updater.main:main',
        ],
    },
    description='A tool to update BetterDiscord when Discord updates',
    author="Lofn",
    author_email="lofngames@gmail.com",
    url='https://github.com/Loofn/bdupdater',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Lisence :: OSI Approved :: MIT Lisence',
        'Operating System :: OS Independent',
    ],
)