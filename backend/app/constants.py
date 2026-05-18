"""Compile-time mirrors of `settings`. Routers that want a plain constant
import these names; settings remains the single source of truth.
"""

from app.settings import settings

MAX_CONTACTS_PER_GROUP = settings.group_max_contacts
DEFAULT_MIN_DELAY_S = settings.min_delay_s
DEFAULT_MAX_DELAY_S = settings.max_delay_s
MAX_DELAY_S = 300
