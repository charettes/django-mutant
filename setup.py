#!/usr/bin/env python
from setuptools import setup, find_packages

from mutant import __version__

github_url = 'https://github.com/charettes/django-mutant'
long_desc = open('README.md').read()

setup(
    name='django-mutant',
    version='.'.join(str(v) for v in __version__),
    description='Dynamic model definition and alteration (evolving schemas)',
    long_description=open('README.md').read(),
    url=github_url,
    author='Simon Charette',
    author_email='charette.s@gmail.com',
    install_requires=(
        'django>=1.3,<=1.5',
        'south>=0.7.6',
        'django-orderable==1.2.1',
        'django-picklefield==0.2.0',
        'django-polymodels',
    ),
    dependency_links=(
        'https://github.com/tkaemming/django-orderable/tarball/master#egg=django-orderable-1.2.1',
    ),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT License',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
