# querypp

[![Build Status](https://travis-ci.org/bmintz/querypp.svg?branch=master)](https://travis-ci.org/bmintz/querypp)
[![Coverage Status](https://coveralls.io/repos/github/bmintz/querypp/badge.svg?branch=master)](https://coveralls.io/github/bmintz/querypp?branch=master)

querypp preprocesses SQL queries[1] in order to "parameterize" them. It also includes a loader which loads many queries
from a file, delimited by `-- :name query_name` lines.

[1] Although it is trivially adapted to other languages with line comments,
    as the only SQL-specific assumption is the comment syntax.

Take an example:

```
SELECT *
FROM users
-- :param profiles
LEFT JOIN profiles USING (user_id)
-- :param login_history
LEFT JOIN login_history USING (profile_id)
-- :endparam
-- :endparam
-- :param user_id WHERE user_id = $1
```

A Query object can be called:
  - with no parameters to return the entire query
  - with one or more parameters to return the query with only those parameters.

In this case, `q('profiles', 'user_id')` would return the query with the `login_history` JOIN removed.

## Motivation

After moving all my SQL queries to separate files (using the load_sql function),
I noticed that I was duplicating some of them except for one extra clause.
I created this to allow me to deduplicate such queries.

## License

Public domain, see [COPYING](/COPYING)
