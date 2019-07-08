import io
import os

import fabric.connection
import haikunator
import paramiko.rsakey
from django.conf import settings

from utils import s3helpers

DEMO_TIMEOUT_DAYS = 7


def request_demo():
    conn = _get_connection()
    instance_name = haikunator.Haikunator().haikunate()
    env = {"INSTANCE_NAME": instance_name}
    with conn.cd("~/99_demo_instances/"):
        conn.run("mkdir {instance}".format(instance=instance_name))
        with conn.cd(instance_name):
            conn.run("ln -s ~/demo/demo.yml && docker-compose -f demo.yml up -d", env=env)
    return instance_name, settings.DEMO_URL.format(instance_name=instance_name), settings.DEMO_PASSWORD


def terminate_demo(instance_name, connection=None):
    conn = connection or _get_connection()
    env = {"INSTANCE_NAME": instance_name}
    with conn.cd("~/99_demo_instances/"):
        conn.run(
            "docker-compose -f {instance_name}/demo.yml down --rmi local --remove-orphans && rm -fr {instance_name}".format(
                instance_name=instance_name
            ),
            env=env,
        )


def terminate_old_instances():
    conn = _get_connection()
    with conn.cd("~/99_demo_instances/"):
        instances = conn.run("find -mtime +{timeout} -type d".format(timeout=DEMO_TIMEOUT_DAYS)).stdout
        for instance in instances.splitlines():
            terminate_demo(instance, connection=conn)


def prepare_demo(snapshot_id=None):
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_DEMO)
    if not snapshot_id:
        snapshot_id = s3_helper.get("latest.txt").decode("utf-8").strip()
    build = s3_helper.get(os.path.join(snapshot_id, "build.txt")).decode("utf-8").strip().replace("/", ".")
    dump_url = s3_helper.generate_url(os.path.join(snapshot_id, "dump.tar"))
    conn = _get_connection()

    # create docker network if it does not exist
    conn.run("/usr/bin/docker network create -d bridge legacynet", warn=True)

    # prepare z1 container
    conn.run(
        " && ".join(
            [
                "$(aws --region us-east-1 ecr get-login --no-include-email)",
                "docker pull 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1:{build}",
                "docker tag 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1:{build} z1-bundle:{build}",
                "docker tag 569683728510.dkr.ecr.us-east-1.amazonaws.com/zemanta/z1:{build} z1-bundle:current",
            ]
        ).format(build=build)
    )

    # start postgres container
    postgres = conn.run(
        "/usr/bin/docker run -d "
        " --network legacynet "
        "-e POSTGRES_USER=one "
        "-e POSTGRES_PASSWORD=eins "
        "-e PGDATA=/data "
        "-e POSTGRES_DB=demo-one "
        "-l traefik.enable=false "
        "postgres:9.6"
    ).stdout.strip()
    postgres_ip = conn.run(
        "docker inspect %s -f '{{.NetworkSettings.Networks.legacynet.IPAddress}}'" % postgres
    ).stdout.strip()

    # start eins container and run prepare-demo.sh script in it
    conn.run(
        "/usr/bin/docker run "
        " --network legacynet "
        "--rm "
        "--add-host demodbhost:{postgres_ip} "
        '-e DUMP_URL="{dump_url}" '
        "-e CONF_ENV=demo "
        "--entrypoint=/bin/bash "
        "-e STATSD_PORT_8125_UDP_ADDR=localhost "
        "-e DB_PORT_5432_TCP_ADDR=demodbhost  "
        "-e DB_PORT_5432_TCP_PORT=5432 "
        "-e DB_ENV_POSTGRES_DB=demo-one "
        "z1-bundle:{build} "
        "/prepare-demo.sh".format(build=build, postgres_ip=postgres_ip, dump_url=dump_url)
    )

    # stop containers and commit/save & tag them
    conn.run("docker stop {postgres}".format(postgres=postgres))
    commited_postgres = conn.run("docker commit {postgres}".format(postgres=postgres)).stdout.strip()
    conn.run("docker rm -f -v {postgres}".format(postgres=postgres))
    conn.run("docker tag {cpostgres} demopostgres:current".format(cpostgres=commited_postgres))
    conn.run(
        "docker tag {cpostgres} demopostgres:{snapshot_id}".format(cpostgres=commited_postgres, snapshot_id=snapshot_id)
    )

    # update compose file
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_ARTIFACTS)
    branch, build_number = build.split(".")
    docker_compose_demo_url = s3_helper.generate_url(
        "{project_name}/{branch}/{build_number}/docker-compose.demo.yml".format(
            project_name="zemanta-eins", branch=branch, build_number=build_number
        )
    )
    conn.run('curl -L "{url}" > demo/demo.yml'.format(url=docker_compose_demo_url))


def _get_connection():
    return fabric.connection.Connection(
        host=settings.DEMO_NODE_HOSTNAME,
        user="ubuntu",
        connect_kwargs={"pkey": paramiko.rsakey.RSAKey.from_private_key(io.StringIO(settings.DEMO_NODE_SSH_KEY))},
        inline_ssh_env=True,
    )
