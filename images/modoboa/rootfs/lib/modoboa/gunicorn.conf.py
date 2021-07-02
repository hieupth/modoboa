backlog = 2048
bind = "unix:/run/gunicorn/modoboa.sock"
daemon = False
debug = False
workers = 2
forwarded_allow_ips = "*"
loglevel = "info"
