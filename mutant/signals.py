from django.dispatch import Signal

mutable_class_prepared = Signal(providing_args=['class', 'definition'])
