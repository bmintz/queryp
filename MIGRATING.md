# Migrating from querypp to jinja2


## In your templates

```diff
--- :query foo
+-- :macro foo()
 a
 b
--- :qblock x
+-- :if 'x' in varargs
    c
--- :endqblock
--- :endquery
+-- :endif
+-- :endmacro
```

## In your python code

```diff
- querypp.Environment(base_dir)
+ jinja2.Environment(loader=jinja2.FileSystemLoader(str(base_dir)), line_statement_prefix='-- :')
```

```diff
-my_queries = environment.get_template('queries.sql')
+my_queries = environment.get_template('queries.sql').module
```
