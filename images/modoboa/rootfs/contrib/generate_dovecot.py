#!/usr/bin/python3
import contextlib
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
	'mysql.connector.django':   'mysql',
	'django.db.backends.sqlite3': 'sqlite'
}

if DATABASE_INFO['ENGINE'] in DATABASE_ENGINES:
	DATABASE_BACKEND = DATABASE_ENGINES[DATABASE_INFO['ENGINE']]
else:
	print("Unknown database engine: {0}".format(DATABASE_INFO['ENGINE']), file=sys.stderr)
	sys.exit(1)


format_shell_string   = lambda s: "'{0}'".format(s.replace("\'", "\'\"\'\"\'"))
format_dovecot_string = lambda s: "'{0}'".format(s.replace("\'", "\\\'"))

if DATABASE_BACKEND != "sqlite":
	dovecot_connect_string = "connect ="
	for itemname, fieldname in (("HOST", "host"), ("PORT", "port"), ("USER", "user"), ("PASSWORD", "password"), ("NAME", "dbname")):
		if itemname in DATABASE_INFO and len(DATABASE_INFO[itemname]) > 0:
			dovecot_connect_string += " {0}={1}".format(fieldname, format_dovecot_string(DATABASE_INFO[itemname]))
else:
	dovecot_connect_string = "connect = {0}".format(format_dovect_string(DATABASE_INFO.get("NAME", "")))


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
with write_to_file(os.path.join(TARGET_DIR, "dovecot-sql.conf.ext")) as fileobj:
	print("driver = {0}".format(DATABASE_BACKEND))
	print()
	
	print(dovecot_connect_string)
	print()
	
	print("default_pass_scheme = CRYPT")
	print()
	
	if DATABASE_BACKEND == "pgsql":
		print("password_query = SELECT email AS user, password \\")
		print("\tFROM core_user u \\")
		print("\tINNER JOIN admin_mailbox mb ON u.id=mb.user_id \\")
		print("\tINNER JOIN admin_domain dom ON mb.domain_id=dom.id \\")
		print("\tWHERE u.email='%Lu' AND u.is_active AND dom.enabled")
		print()
		#'/var/lib/mail/%Ld/%Ln' AS home, 'mail' as uid, 'mail' as gid,
		print("user_query = SELECT '*:bytes=' || mb.quota || 'M' AS quota_rule \\")
		print("\tFROM admin_mailbox mb \\")
		print("\tINNER JOIN admin_domain dom ON mb.domain_id=dom.id \\")
		print("\tWHERE mb.address='%Ln' AND dom.name='%Ld'")
	
	elif DATABASE_BACKEND == "mysql":
		print("password_query = SELECT email AS user, password \\")
		print("\tFROM core_user \\")
		print("\tWHERE email='%Lu' AND is_active=1")
		print()
		
		print("user_query = SELECT concat('*:bytes=', mb.quota, 'M') AS quota_rule \\")
		print("\tFROM admin_mailbox mb \\")
		print("\tINNER JOIN admin_domain dom ON mb.domain_id=dom.id \\")
		print("\tWHERE mb.address='%Ln' AND dom.name='%Ld'")
	
	elif DATABASE_BACKEND == "sqlite":
		print("password_query = SELECT email AS user, password \\")
		print("\tFROM core_user u \\")
		print("\tINNER JOIN admin_mailbox mb ON u.id=mb.user_id \\")
		print("\tINNER JOIN admin_domain dom ON mb.domain_id=dom.id \\")
		print("\tWHERE u.email='%Lu' AND u.is_active=1 AND dom.enabled=1")
		print()
		
		print("user_query = SELECT ('*:bytes=' || mb.quota || 'M') AS quota_rule \\")
		print("\tFROM admin_mailbox mb \\")
		print("\tINNER JOIN admin_domain dom ON mb.domain_id=dom.id \\")
		print("\tWHERE mb.address='%Ln' AND dom.name='%Ld'")
	
	print()
	print("iterate_query = SELECT email AS user FROM core_user")
	


# Quota configuration
with write_to_file(os.path.join(TARGET_DIR, "dovecot-dict-sql.conf")) as fileobj:
	print("dict {")
	print("\tquota = {0}:/shared/modoboa/dovecot/dovecot-dict-sql.conf.ext".format(DATABASE_BACKEND))
	print("}")

with write_to_file(os.path.join(TARGET_DIR, "dovecot-dict-sql.conf.ext")) as fileobj:
	print(dovecot_connect_string)
	
	print("""
map {
	pattern = priv/quota/storage
	table = admin_quota
	username_field = username
	value_field = bytes
}

map {
	pattern = priv/quota/messages
	table = admin_quota
	username_field = username
	value_field = messages
}
""")


# Last-login tracking script
with write_to_file(os.path.join(TARGET_DIR, "post-login.sh")) as fileobj:
	print("#!/bin/sh")
	print("export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
	
	# Write database connection parameters
	print("DBHOST={0}".format(format_shell_string(DATABASE_INFO.get("HOST", ""))))
	print("DBPORT={0}".format(format_shell_string(DATABASE_INFO.get("PORT", ""))))
	print("DBUSER={0}".format(format_shell_string(DATABASE_INFO.get("USER", ""))))
	print("DBPASS={0}".format(format_shell_string(DATABASE_INFO.get("PASSWORD", ""))))
	print("DBNAME={0}".format(format_shell_string(DATABASE_INFO.get("NAME", ""))))
	
	print()
	# Write database update command
	if DATABASE_BACKEND == 'pgsql':
		print("echo \"${DBPASS}\" "
			+ "| psql --host=\"${DBHOST}\" --port=\"${DBPORT}\" --password --quiet "
			+ "\"${DBNAME}\" \"${DBUSER}\" "
			+ "-c \"UPDATE core_user SET last_login=now() WHERE username='${USER}'\"")
	elif DATABASE_BACKEND == 'mysql':
		print("echo \"${DBPASS}\" "
			+ "| mysql --host=\"${DBHOST}\" --port=\"${DBPORT}\" --user=\"${DBUSER}\" "
			+ "--password --silent \"${DBNAME}\" "
			+ "-e \"UPDATE core_user SET last_login=now() WHERE username='${USER}'\"")
	elif DATABASE_BACKEND == 'sqlite':
		print("sqlite3 \"${DBNAME}\" \"UPDATE core_user SET last_login=now() WHERE username='${USER}'\"")
	
	# Run real login command
	print()
	print("exec \"$@\"")
os.chmod(os.path.join(TARGET_DIR, "post-login.sh"), 0o755)

