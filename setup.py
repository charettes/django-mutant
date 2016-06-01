#!/usr/bin/env python
import os
from setuptools import find_packages, setup

from mutant import __version__

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-mutant',
    version=__version__,
    description='Dynamic model definition and alteration (evolving schemas)',
    long_description=open(os.path.join(MODULE_PATH, 'README.rst')).read(),
    url='https://github.com/charettes/django-mutant',
    author='Simon Charette',
    author_email='charette.s@gmail.com',
    install_requires=[
        'django>=1.8',
        'django-picklefield>=0.3.2',
        'django-polymodels>=1.4.6a1',
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        '': ['locale/*/LC_MESSAGES/*'],
    },
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
