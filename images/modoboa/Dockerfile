FROM python:3.9-alpine3.14

# Update base system
RUN apk update \
 && apk upgrade \
 && apk add --no-cache ca-certificates sudo supervisor \
 && update-ca-certificates \

# Install additional modoboa dependencies
 && apk add --no-cache --virtual .modoboa-deps \
    libffi \
    libjpeg \
    libxml2 \
    libxslt \
    librrd \
    libpq \
    rrdtool \

# Install modoboa build dependencies
 && apk add --no-cache --virtual .build-deps \
	coreutils \
	gcc \
	g++ \
	libffi-dev \
	libjpeg-turbo-dev \
	libxml2-dev \
	libxslt-dev \
    mariadb-dev \
    postgresql-dev \
    rrdtool-dev \

# Install modoboa, a web server and possible database dependencies
 && pip install --no-cache-dir --no-binary=all gunicorn mysqlclient psycopg2 modoboa \
 
# Remove build dependencies
 && apk del .build-deps

# User configuration
ENV MODOBOA_UID=992 MODOBOA_GID=992

COPY rootfs /

# Persistant data volume
VOLUME /data

# gunicorn WSGI HTTP Server
EXPOSE 8080

ENTRYPOINT ["/init"]
CMD ["start"]