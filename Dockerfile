FROM debian

# todo add after apt-get stuffs: rm -rf /var/lib/apt/lists/*
# todo reduce fs layers number

RUN apt-get update && \
    apt-get -y install \
        python3 \
        python3-venv \
        python3-pip \
        uwsgi \
        uwsgi-plugin-python3 \
        ffmpeg \
        supervisor \
        nginx \
        curl

# main program copy
COPY ytfeed_wsgi.py ytproxy_wsgi.py ffproxy_wsgi.py setup.py /app/

COPY ytfeed /app/ytfeed
COPY ytproxy /app/ytproxy
COPY ffproxy /app/ffproxy

WORKDIR /app

RUN python3 -m venv .env

RUN python3 -m venv .env && \
        . .env/bin/activate && \
        pip install wheel && \
        pip install .

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/uwsgi.ini docker/ytfeed.conf docker/ytfeed_wait.sh /app/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80

ENTRYPOINT [ "supervisord" ]