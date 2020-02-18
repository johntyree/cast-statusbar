#!/usr/bin/env python
# coding: utf8

from setuptools import setup

setup(
    name='cast_statusbar',
    version='0.0.1',
    packages=['cast_statusbar'],
    author='John Tyree',
    author_email='johntyree@gmail.com',
    license='GPL3+',
    url='http://github.com/johntyree/caststatus',
    description="Chromecast Status Monitor",
    keywords="chromecast cast status",
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['caststatus = caststatus:main'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: "
        "GNU General Public License v3 or later (GPLv3+)",
    ],
)
