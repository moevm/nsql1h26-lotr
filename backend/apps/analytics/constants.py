# Number of most liked pages shown
MOST_LIKED_LIMIT = 10

# Number of most commented pages shown
MOST_COMMENTED_LIMIT = 10

# Default number of neighbor nodes returned when `limit` is not specified.
NEIGHBORS_DEFAULT_LIMIT = 100

# Hard upper bound on `limit`.  Prevents accidentally returning the whole graph.
NEIGHBORS_MAX_LIMIT = 1000

# Only depths 1 and 2 are allowed.  Depth=3+ on a dense wiki graph would
# produce huge, hard-to-visualise result sets and expensive Cypher traversals.
NEIGHBORS_ALLOWED_DEPTHS: frozenset[int] = frozenset({1, 2})

# Default max traversal depth when `max_depth` is not specified.
SHORTEST_PATH_DEFAULT_MAX_DEPTH = 10

# Hard upper bound on `max_depth` per OpenAPI spec.
SHORTEST_PATH_MAX_ALLOWED_DEPTH = 15

# Minimum depth — paths of length 0 (from == to) are rejected at validation.
SHORTEST_PATH_MIN_DEPTH = 1
