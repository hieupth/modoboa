FROM alpine:3.14

# Use stricter shell configuration during build
SHELL ["/bin/sh", "-eu", "-c"]

# Update base system
RUN apk update
RUN apk upgrade

# Install pre-requirements
RUN apk add --no-cache ca-certificates inetutils-syslogd runit
RUN update-ca-certificates

# Install all alpine postfix packages (except documentation and development files) + the SPF policyd
RUN apk add --no-cache \
	postfix \
	postfix-pgsql \
	postfix-sqlite \
	postfix-mysql \
	postfix-pcre \
	postfix-ldap \
	policyd-spf-fs

# Register the SPF policyd daemon as a postfix service (but don't enable actual validation)
RUN : \
 && echo "#"                                                               >> "/etc/postfix/master.cf" \
 && echo "# Policy daemon for SPF"                                         >> "/etc/postfix/master.cf" \
 && echo "spf-policy  unix  -       n       n       -       -       spawn" >> "/etc/postfix/master.cf" \
 && echo "      user=nobody argv=/usr/bin/policyd-spf-fs --debug=1"        >> "/etc/postfix/master.cf" \
# Enable the SMTP submission port by default
 && sed -i -e 's,#submission inet,submission inet,' \
        /etc/postfix/master.cf

# Remove left-over temporary files
RUN find /var/cache/apk /tmp -mindepth 1 -delete

# Add init script that will generate the TLS configuration on startup
ENV SVDIR=/etc/runit/services
ADD rootfs /

#   25: SMTP (Server2Server)
#  465: SMTP (SSL, deprecated)
#  587: SMTP (StartTLS)
EXPOSE 25 465 587

STOPSIGNAL SIGINT
CMD ["/sbin/runit"]