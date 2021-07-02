FROM alpine:3.14

# Use stricter shell configuration during build
SHELL ["/bin/sh", "-eu", "-c"]

# Update base system
RUN apk update
RUN apk upgrade

# Install pre-requirements
RUN apk add --no-cache ca-certificates
RUN update-ca-certificates

# Disable Dovecot TLS during installation to prevent key from being pregenerated
RUN mkdir -p /etc/dovecot && echo "ssl = no" > /etc/dovecot/local.conf

# Install all alpine dovecot packages (except documentation and development files)
RUN apk add --no-cache \
	dovecot \
	dovecot-gssapi \
	dovecot-ldap \
	dovecot-lmtpd \
	dovecot-mysql \
	dovecot-pgsql \
	dovecot-pigeonhole-plugin \
	dovecot-pigeonhole-plugin-ldap \
	dovecot-pop3d \
	dovecot-sqlite \
	dovecot-submissiond
	

# Re-enable the default Dovecot TLS configuration
RUN rm /etc/dovecot/local.conf

# Add wrapper script that will generate the TLS configuration on startup
ADD rootfs /

# Set logging to STDOUT/STDERR
RUN sed -i -e 's,#log_path = syslog,log_path = /dev/stderr,' \
           -e 's,#info_log_path =,info_log_path = /dev/stdout,' \
           -e 's,#debug_log_path =,debug_log_path = /dev/stdout,' \
	/etc/dovecot/conf.d/10-logging.conf
# Set default passdb to passwd and create the referenced 'users' file
RUN sed -i -e 's,!include auth-system.conf.ext,!include auth-passwdfile.conf.ext,' \
           -e 's,#!include auth-passwdfile.conf.ext,#!include auth-system.conf.ext,' \
	/etc/dovecot/conf.d/10-auth.conf
RUN install -m 640 -o dovecot -g mail /dev/null /etc/dovecot/users
# Set default mail location to "/var/lib/mail"
RUN sed -i -e 's,#mail_location =,mail_location = /var/lib/mail/%n,' \
	/etc/dovecot/conf.d/10-mail.conf

# Remove left-over temporary files
RUN find /var/cache/apk /tmp -mindepth 1 -delete

# Mail storage directory, TLS key directory & Dovecot socket directory
VOLUME /var/lib/mail /etc/ssl/dovecot /run/dovecot

#   24: LMTP
#  110: POP3 (StartTLS)
#  143: IMAP4 (StartTLS)
#  993: IMAP (SSL, deprecated)
#  995: POP3 (SSL, deprecated)
# 4190: ManageSieve (StartTLS)
EXPOSE 24 110 143 993 995 4190

# Add command-line databse client binaries for last-login tracking
RUN apk add --no-cache --virtual .database-cli \
	postgresql-client \
	mariadb-client \
	sqlite

# Remove left-over temporary files
RUN find /var/cache/apk /tmp -mindepth 1 -delete

CMD ["/usr/local/bin/dovecot-wrapper"]