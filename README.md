# django-mutant

## Overview

[Django](https://www.djangoproject.com/) provides a great ORM and with the power of [South](http://south.aeracode.org/) one can easily perform schema alteration.

However, some projects may require _runtime_ schema alteration and that's what _django-mutant_ provides.

The main concept was inspired by those projects:

- Will Hardy [dynamic-models](https://github.com/willhardy/dynamic-models) with [doc](http://dynamic-models.readthedocs.org/en/latest/index.html) and [talk](http://2011.djangocon.eu/talks/22/#talkvideo).
- And even more by [django-dynamo](http://pypi.python.org/pypi/django-dynamo)

## Direction of the project

The project is still in an early phase but a couple of complex things already works such as declaration of `RelatedField` (`ForeignKey`, `ManyToManyField`) between models and an easy way of declaring subclasses of `FieldDefinition` which allow any [`Field`](https://docs.djangoproject.com/en/dev/howto/custom-model-fields/) subclass to be be represented easily:

    class DateFieldDefinition(FieldDefinition):
        auto_now = fields.BooleanField(_(u'auto now'), default=False)
        auto_now_add = fields.BooleanField(_(u'auto_now_add'), default=False)
        
        class Meta:
            app_label = 'mutant'
            defined_field_class = fields.DateField
            defined_field_options = ('auto_now', 'auto_now_add',)
            defined_field_category = _(u'datetime')

This approach also allows projects such as [django-non-rel](https://github.com/django-nonrel/django-nonrel) to be truly useful since both your schema and your ORM wrapper around it are flexible.

## Get in touch and contribute

From now on I think the best way to contribute and get in touch is using github messaging system (issues and pull requests)

[![Build Status](https://secure.travis-ci.org/charettes/django-mutant.png)](http://travis-ci.org/charettes/django-mutant)

[Development version](https://github.com/charettes/django-mutant/tarball/master#egg=mutant-dev) can be installed from pip: `pip install django-mutant==dev`.