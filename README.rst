#############
django-mutant
#############

Dynamic model definition and alteration (evolving schemas).

.. image:: https://travis-ci.org/charettes/django-mutant.png?branch=master
    :target: http://travis-ci.org/charettes/django-mutant

.. image:: https://coveralls.io/repos/charettes/django-mutant/badge.png?branch=master
   :target: https://coveralls.io/r/charettes/django-mutant

********
Overview
********

`Django`_ provides a great ORM and with the power of `South`_ one can easily perform schema alteration.

However, some projects may require *runtime* schema alteration and that's what `django-mutant`_ ought to provide.

The main concept was inspired by those projects:

- Will Hardy `dynamic-models`_'s `documentation`_ and `talk`_.
- And by `django-dynamo`_.

.. _`Django`: https://www.djangoproject.com/
.. _`South`: http://south.aeracode.org/
.. _`django-mutant`: https://github.com/charettes/django-mutant
.. _`dynamic-models`: https://github.com/willhardy/dynamic-models
.. _`documentation`: http://dynamic-models.readthedocs.org/en/latest/index.html
.. _`talk`: http://2011.djangocon.eu/talks/22/#talkvideo
.. _`django-dynamo`: https://bitbucket.org/schacki/django-dynamo

************
Installation
************

::

    pip install django-mutant

Make sure ``'django.contrib.contenttypes'`` and ``'mutant'`` are in
your ``INSTALLED_APPS``

::

    INSTALLED_APPS += ('django.contrib.contenttypes', 'mutant')


**********************************************
Migrating to django-mutant 0.2 and Django 1.7+
**********************************************

If you used ``mutant`` with Django < 1.7 and are willing to migrate forward
you'll have to run the following steps in order to make sure you database
schema is synchronized with Django's migration state.

1. Fake the initial ``mutant`` migration.
2. For every ``mutant.contrib`` application you installed make sure to fake
   their initial migration and run their following migration. For example,
   if you had the ``mutant.contrib.boolean`` application installed you want to
   run ``manage.py migrate boolean --fake 0001 && manage.py migrate boolean``


**********
Resources
**********
- `DjangoCon Europe 2013 talk`_ about mutant and other dynamic model alternatives given by Juergen Schackmann.
- `A getting started guide`_ with mutant guide by @integricho.

.. _DjangoCon Europe 2013 talk: https://www.youtube.com/watch?v=67wcGdk4aCc
.. _A getting started guide: http://integricho.github.io/2013/07/22/mutant-introduction/

************************
Direction of the project
************************
`django-mutant`_ is actually using `South`_ under the hood to provide schema migrations. Since the `schema editor code is being merged`_ into the main `Django`_ code base the next major version of mutant will rely on it instead thus dropping the external dependency on `South`.

.. _`schema editor code is being merged`: http://www.kickstarter.com/projects/andrewgodwin/schema-migrations-for-django

***************************
Get in touch and contribute
***************************

From now on I think the best way to contribute and get in touch is using github messaging system (issues and pull requests).
