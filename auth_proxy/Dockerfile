FROM python:3.11 as app

COPY app.py /opt/
COPY requirements.txt /opt/

RUN set -ex \
	&& apt-get update \
	&& apt-get install --yes \
	# - common -
	curl \
	python3-dev

RUN pip3 install -r /opt/requirements.txt

WORKDIR /opt

EXPOSE 9000

COPY scripts/docker-entrypoint.sh /
RUN chmod u+x /docker-entrypoint.sh

CMD ["sh", "-c", "$STARTUP_COMMAND"]
