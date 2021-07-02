#!/usr/bin/python3
import contextlib
import urllib.parse
import os
import sys
TARGET_DIR = sys.argv[1]

# Requires working directory to be set correctly
import instance.settings
DATABASE_INFO    = instance.settings.DATABASES["default"]
DATABASE_BACKEND = None
DATABASE_ENGINES = {
	'django.db.backends.postgresql':          'pgsql',
	'django.db.backends.postgresql_psycopg2': 'pgsql',
	'django.db.backends.pgsql_psycopg2':      'pgsql',
	'django.db.backends.mysql': 'mysql',
	'mysql.connector.django':   'mysql'
}

if DATABASE_INFO['ENGINE'] in DATABASE_ENGINES:
	DATABASE_BACKEND = DATABASE_ENGINES[DATABASE_INFO['ENGINE']]
else:
	print("Unknown database engine: {0}".format(DATABASE_INFO['ENGINE']), file=sys.stderr)
	sys.exit(1)

import django.conf
import django.db

django.conf.settings.configure(**vars(instance.settings))

# Set up OpenDKIM database view
with django.db.connection.cursor() as cursor:
	try:
		if DATABASE_BACKEND == "pgsql":
			cursor.execute("""
				CREATE OR REPLACE VIEW dkim AS (
					SELECT
						id,
						name as domain_name,
						dkim_private_key_path AS private_key_path,
						dkim_key_selector AS selector
					FROM
						admin_domain
					WHERE
						enable_dkim
				);
			""")
		elif DATABASE_BACKEND == "mysql":
			cursor.execute("""
				CREATE OR REPLACE VIEW dkim AS (
					SELECT
						id,
						name as domain_name,
						dkim_private_key_path AS private_key_path,
						dkim_key_selector AS selector
					FROM
						admin_domain
					WHERE
						enable_dkim=1
				);
			""")
	except django.db.utils.ProgrammingError:
		pass  # We weren't authorized to do this

escaped_database_info = dict(map(lambda i: (i[0], urllib.parse.quote(i[1], safe="") if isinstance(i[1], str) else i[1]), DATABASE_INFO.items()))

opendkim_dsn_string = "dsn:{0}://{1[USER]}:{1[PASSWORD]}@{1[HOST]}/{1[NAME]}".format(DATABASE_BACKEND, escaped_database_info)


@contextlib.contextmanager
def write_to_file(filepath):
	fileobj = open(str(filepath), "w")
	try:
		sys.stdout = fileobj
		
		yield fileobj
	finally:
		sys.stdout = sys.__stdout__


os.makedirs(TARGET_DIR, exist_ok=True)



# Authentication configuration
with write_to_file(os.path.join(TARGET_DIR, "opendkim.conf")) as fileobj:
	print("# AUTOMATICALLY GENERATED #")
	print("# Do not edit!")
	print()
	print("KeyTable     {0}/table=dkim?keycol=id?datacol=domain_name,selector,private_key_path".format(opendkim_dsn_string))
	print("SigningTable {0}/table=dkim?keycol=domain_name?datacol=id".format(opendkim_dsn_string))
