#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

from setuptools import setup

# Get the version
version_regex = r'__version__ = ["\']([^"\']*)["\']'
with open('branchmgr/__init__.py', 'r') as f:
    text = f.read()
    match = re.search(version_regex, text)

    if match:
        version = match.group(1)
    else:
        raise RuntimeError("No version number found!")

setup(
    name='branchmgr',
    version=version,
    description='A tool for managing GitHub branch permissions.',
    long_description=open('README.rst').read() + '\r\n\r\n' + open('HISTORY.rst').read(),
    author='Cory Benfield',
    author_email='cory@lukasa.co.uk',
    url='http://python-hyper.org',
    packages=['branchmgr'],
    package_data={'': ['LICENSE', 'README.rst']},
    package_dir={'branchmgr': 'branchmgr'},
    include_package_data=True,
    license='MIT License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    install_requires=['twisted[tls]', 'gidgethub', 'treq', 'click'],
    entry_points={
        'console_scripts': [
            'branchmgr = branchmgr.main:cli',
        ],
    }
)
