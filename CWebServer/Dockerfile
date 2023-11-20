FROM python:alpine

COPY requirements.txt /app/requirements.txt

# https://www.digitalocean.com/community/tutorials/how-to-build-a-django-and-gunicorn-application-with-docker#adding-instructions-to-set-up-the-application
RUN set -ex \
    && apk add --no-cache --virtual .build-deps build-base \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && runDeps="$(scanelf --needed --nobanner --recursive /env \
    | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
    | sort -u \
    | xargs -r apk info --installed \
    | sort -u)" \
    && apk add --virtual rundeps $runDeps \
    && apk del .build-deps

WORKDIR /app

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

EXPOSE 8000
COPY . .

# This must be comma-separated
CMD [ "gunicorn", "webserver:create_app()", "--bind=0.0.0.0:8000" ]