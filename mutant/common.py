from itertools import groupby
from operator import itemgetter

group_item_getter = itemgetter('group')
def choices_from_dict(choices):
    for grp, choices in groupby(choices, key=group_item_getter):
        if grp is None:
            for choice in choices:
                yield (choice['value'], choice['label'])
        else:
            yield (grp, tuple((choice['value'], choice['label'])
                                for choice in choices))
