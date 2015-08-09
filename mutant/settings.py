from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS

STATE_HANDLER = getattr(
    settings, 'MUTANT_STATE_HANDLER',
    'mutant.state.handlers.memory.MemoryStateHandler'
)

STATE_CACHE_ALIAS = getattr(
    settings, 'MUTANT_STATE_CACHE_ALIAS', DEFAULT_CACHE_ALIAS
)

STATE_PUBSUB = getattr(
    settings, 'MUTANT_STATE_PUBSUB', (
        'mutant.state.handlers.pubsub.engines.Redis', {}
    )
)
