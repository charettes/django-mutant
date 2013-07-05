#!/usr/bin/env python
import os
import re
from setuptools import find_packages, setup

from mutant import __version__


MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

LINK_REQUIREMENT = re.compile(
    r'^https://.+#egg=(?P<package>.+)-(?P<version>\d(?:\.\d)*)$'
)


install_requires = ['django>=1.5']
dependency_links = []

for requirement in (l.strip() for l in open(os.path.join(MODULE_PATH, 'requirements/base.txt'))):
    match = LINK_REQUIREMENT.match(requirement)
    if match:
        install_requires.append("%(package)s==%(version)s" % match.groupdict())
        dependency_links.append(match.group())
    else:
        install_requires.append(requirement)


setup(
    name='django-mutant',
    version='.'.join(str(v) for v in __version__),
    description='Dynamic model definition and alteration (evolving schemas)',
    long_description=open(os.path.join(MODULE_PATH, 'README.md')).read(),
    url='https://github.com/charettes/django-mutant',
    author='Simon Charette',
    author_email='charette.s@gmail.com',
    install_requires=install_requires,
    dependency_links=dependency_links,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT License',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
