FROM python:2.7

# Install dependencies
RUN apt-get update && \
    apt-get install -y libmemcached-dev

RUN rm -fr /app ; mkdir -p /app && \
    mkdir -p /app/logs && \
    cd /app/


ADD docker/*.sh /
RUN chmod +x /*.sh

ADD server/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && mv /requirements.txt /requirements.txt-installed

EXPOSE 8000

ENTRYPOINT ["/start-server.sh"]
