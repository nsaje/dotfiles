FROM python:2.7

RUN useradd -m -u 1000 ubuntu

# Install dependencies
RUN apt-get update && \
    apt-get install -y libmemcached-dev nano dropbear openssh-server && \
    apt-get install -y --no-install-recommends postgresql-client && \
    apt-get -y autoremove && \
    mkdir /var/run/sshd

RUN rm -fr /app ; mkdir -p /app && \
    mkdir -p /app/logs && \
    cd /app/

ADD docker/*.sh /
RUN chmod +x /*.sh

ADD docker/bash_logout /root/.bash_logout

ADD server/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && mv /requirements.txt /requirements.txt-installed

EXPOSE 8000

ENTRYPOINT ["/start-server.sh"]
