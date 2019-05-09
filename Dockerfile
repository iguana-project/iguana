# global variables
ARG BASE_IMAGE=python:3.5-alpine
ARG BUILD_DIR=/build

ARG APP_DIR
ENV APP_DIR ${APP_DIR:-/iguana}
ARG FILES_DIR
ENV FILES_DIR ${FILES_DIR:-/files}
ARG USE_NGINX
ENV USE_NGINX ${USE_NGINX:-false}
ARG VARIANT
ENV VARIANT ${VARIANT:-development}


FROM $BASE_IMAGE AS builder

# variables
ARG BUILD_DIR

# install dependencies
RUN apk update && \
	apk add sassc git jpeg-dev zlib-dev build-base

# build the application
RUN mkdir $BUILD_DIR
ADD . $BUILD_DIR
WORKDIR $BUILD_DIR
RUN python ./src/make.py $VARIANT


FROM $BASE_IMAGE

# variables
ENV PUID=1000
ENV PGID=1000
ENV TZ=UTC
ENV LANG=en
ARG BUILD_DIR

# for better log output
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apk update && \
	apk add git libjpeg zlib libmagic && \

	# install nginx if wanted for non development builds
	if [ "$USE_NGINX" == "true" ] && [ "$VARIANT" != "development"]; then \
	   apk add nginx; \
	fi

# setup entrypoint
COPY ./docker/docker_entrypoint.py /usr/local/bin
RUN chmod a+x /usr/local/bin/docker_entrypoint.py && \
	ln -s /usr/local/bin/docker_entrypoint.py /  # Needed for backwards compatability

# create application directory
RUN mkdir $APP_DIR
COPY --from=builder $BUILD_DIR $APP_DIR

# copy nginx template config (not needed in development mode)
RUN if [ "$VARIANT" != "development"] && [ "$USE_NGINX" == "true" ]; then \
        cp $APP_DIR/docker/nginx_temlate.conf $APP_DIR/files/nginx.conf; \
        sed -i "s|{{APP_DIR}}|$APP_DIR|g" $APP_DIR/files/nginx.conf; \
        sed -i "s|{{FILES_DIR}}|$FILES_DIR|g" $APP_DIR/files/nginx.conf; \
    fi

# the settings.json file is not required in development mode
RUN if [ "$VARIANT" == "development"]; then \
        mv $APP_DIR/files/settings.json $APP_DIR/files/settings.json.not_required; \
    fi

# create files directory
RUN mkdir $FILES_DIR


ENV PYTHONPATH $APP_DIR/src
WORKDIR $APP_DIR
VOLUME ["$FILES_DIR"]
ENTRYPOINT ["docker_entrypoint.py $VARIANT"]
EXPOSE 8000/tcp
