from itertools import groupby
from operator import itemgetter

group_item_getter = itemgetter('group')
label_item_getter = itemgetter('label')
def choices_from_dict(choices):
    choices = sorted(choices, key=group_item_getter)
    for grp, choices in groupby(choices, key=group_item_getter):
        choices = sorted(choices, key=label_item_getter)
        if grp is None:
            for choice in choices:
                yield (choice['value'], choice['label'])
        else:
            yield (grp, tuple((choice['value'], choice['label'])
                                for choice in choices))
