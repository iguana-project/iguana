################################################################################
# global variables
################################################################################
ARG BASE_IMAGE=python:3.8-alpine
ARG APP_DIR=/iguana
ARG FILES_DIR=/files
ARG USE_NGINX=false
ARG VARIANT=development

################################################################################
# Build stage
################################################################################
FROM $BASE_IMAGE AS builder

# variables
ARG APP_DIR
ARG VARIANT

# install dependencies
RUN apk add --no-cache \
    git \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    libffi-dev \
    build-base \
    postgresql-dev \
    mariadb-connector-c-dev \
    # needed to build Python cryptography
    cargo

# build the application
RUN mkdir $APP_DIR
ADD . $APP_DIR
WORKDIR $APP_DIR
RUN python ./src/make.py $VARIANT && \
    # remove the generated sqlite database file
    rm $APP_DIR/files/db.sqlite3


################################################################################
# Runtime stage
################################################################################
FROM $BASE_IMAGE

# build variables
ARG APP_DIR
ENV APP_DIR $APP_DIR
ARG FILES_DIR
ENV FILES_DIR $FILES_DIR
ARG USE_NGINX
ENV USE_NGINX $USE_NGINX
ARG VARIANT
ENV VARIANT $VARIANT
# runtime variables
ENV PUID=1000
ENV PGID=1000
ENV TZ=UTC
ENV LANG=en

# for better log output
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apk add --no-cache \
    # for user management in docker_entrypoint.py
    shadow \
    git \
    libjpeg \
    zlib \
    libmagic \
    freetype \
    libpq \
    # needed by compiled Python cryptography
    libgcc \
    logrotate \
    mariadb-connector-c

# install nginx if wanted for non development builds
RUN if [ "$USE_NGINX" == "true" ] && [ "$VARIANT" != "development" ]; then \
        apk add --no-cache nginx; \
    fi

# setup entrypoint
COPY ./docker/docker_entrypoint.py /usr/local/bin
RUN chmod a+x /usr/local/bin/docker_entrypoint.py && \
    ln -s /usr/local/bin/docker_entrypoint.py /  # Needed for backwards compatability

# create application directory
RUN mkdir $APP_DIR
COPY --from=builder $APP_DIR $APP_DIR

# copy config files that are not needed in development mode)
RUN if [ "$VARIANT" != "development" ]; then \
        if [ "$USE_NGINX" == "true" ]; then \
            cp $APP_DIR/docker/nginx_template.conf $APP_DIR/files/nginx.conf; \
            sed -i "s|{{APP_DIR}}|$APP_DIR|g" $APP_DIR/files/nginx.conf; \
            sed -i "s|{{FILES_DIR}}|$FILES_DIR|g" $APP_DIR/files/nginx.conf; \
        fi; \
        cp $APP_DIR/docker/logrotate.conf /etc/logrotate.conf; \
        for orig_file in $APP_DIR/docker/*.logrotate; do \
            [ -f "$orig_file" ] || continue; \
            dest_file=/etc/logrotate.d/$(basename $orig_file .logrotate); \
            cp $orig_file $dest_file; \
            sed -i "s|{{FILES_DIR}}|$FILES_DIR|g" $dest_file; \
        done; \
    fi

# the settings.json file is not required in development mode
RUN if [ "$VARIANT" == "development" ]; then \
        rm $APP_DIR/files/settings.json; \
    fi

# create files directory
RUN mkdir $FILES_DIR


ENV PYTHONPATH $APP_DIR/src
WORKDIR $APP_DIR
VOLUME ["$FILES_DIR"]
EXPOSE 8000/tcp
ENTRYPOINT ["docker_entrypoint.py"]
