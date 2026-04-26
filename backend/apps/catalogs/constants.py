'''
Shared constants for catalog endpoints.
Centralised here so both service and view import from one place.
_MAX_MULTI (max OR-values per filter param) lives in filters.py because it
is specific to filter construction, not pagination.
'''

MAX_PAGE_SIZE: int = 100
DEFAULT_PAGE_SIZE: int = 20
