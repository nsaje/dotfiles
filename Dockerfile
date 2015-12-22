FROM python:2.7

RUN useradd -m -u 1000 ubuntu

# Install dependencies
RUN apt-get update && \
    apt-get install -y libmemcached-dev nano dropbear && \
    apt-get -y autoremove

RUN rm -fr /app ; mkdir -p /app && \
    mkdir -p /app/logs && \
    cd /app/

ADD docker/psql /usr/local/bin/psql
RUN chmod +x /usr/local/bin/psql

ADD docker/*.sh /
RUN chmod +x /*.sh

ADD docker/bash_logout /root/.bash_logout

ADD server/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && mv /requirements.txt /requirements.txt-installed

EXPOSE 8000

ENTRYPOINT ["/start-server.sh"]
