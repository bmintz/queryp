# querypp

querypp is a SQL query[1] templating system based on [jinja2](https://palletsprojects.com/p/jinja/).

[1]: Although it is trivially adapted to other languages, as the only SQL-specific assumption is the line comment
syntax.

Take an example:

```
-- :query users
SELECT *
FROM users
-- :qblock profiles
	LEFT JOIN profiles USING (user_id)
	-- :block login_history
		LEFT JOIN login_history USING (profile_id)
	-- :endqblock
-- :endqblock
-- :qblock user_id WHERE user_id = $1
-- :endquery
```

A Query template can be called:
  - with no block names to return the query without any blocks
  - with one or more block names to return the query with only those block names.

In this case, `q('profiles', 'user_id')` would return the query with the `login_history` JOIN removed.

Additionally, any [jinja2 templating features](https://jinja.readthedocs.io/en/2.10.x/templates/),
such as variables and macro functions, can be used, using either the line syntax (e.g. `-- :include 'foo.sql'`)
or the block syntax (e.g. `{% if x == 1 %}`).

## Usage

```
env = querypp.QueryEnvironment('sql/')
queries = env.get_template('queries.sql')  # opens sql/queries.sql
db.execute(queries.users('login_history', 'user_id'), user_id)
```

## Motivation

After moving all my SQL queries to separate files,
I noticed that I was duplicating some of them except for one extra clause.
I created this to allow me to deduplicate such queries.

## License

Public domain, see [COPYING](https://github.com/bmintz/querypp/blob/master/COPYING)
