import contextlib
from datetime import datetime
import httplib
import os

from fabric.api import abort, env, execute, cd, lcd, local, run, task, prefix, put, parallel, serial
from fabric.contrib.files import exists
import fabric.colors
import fabric.utils

import yaml

# Taken from ratel and modified.

# Example usage:
# List valid options:
# > fab -l
#
# Deployment can be done like this:
# > fab environment:hosts deploy:application
# with the following possible values:
# - environment: 'staging' or 'production'
# - hosts: 'all' or the names of desired hosts separated by comma
# - application: 'server' or 'client'
#
# Examples:
# > fab staging:all deploy:server
# > fab production:all deploy:client
# > fab staging:ovh01,ovh02 deploy:client


APPS = {'server': 'django', 'client': 'angular'}

STAGING_USER = 'one'
PRODUCTION_USER = STAGING_USER

STAGING_SERVERS = {
    'stadium01': 'stadium01.zemanta.com',
}
PRODUCTION_SERVERS = {
    'knot01': 'knot01.zemanta.com',
    'knot02': 'knot02.zemanta.com',
}

GIT_REPOSITORY = 'git@github.com:Zemanta/zemanta-eins.git'
DEFAULT_BRANCH = 'master'


selected_hosts = []


env.forward_agent = True
if env.ssh_config_path and os.path.isfile(os.path.expanduser(env.ssh_config_path)):
    env.use_ssh_config = True


@contextlib.contextmanager
def virtualenv(params):
    venv_prefix = '. /etc/bash_completion.d/virtualenvwrapper && workon %s' % params['venv_name']
    with prefix(venv_prefix):
        yield


# SETTINGS
@task
def staging(*args):
    global selected_hosts

    env.user = STAGING_USER
    if args[0] == 'all':
        selected_hosts = STAGING_SERVERS.values()
    elif set(args) < set(STAGING_SERVERS.keys()):
        selected_hosts = [STAGING_SERVERS[host] for host in set(args)]
    else:
        abort("Unknown hosts!")


@task
def production(*args):
    global selected_hosts

    env.user = PRODUCTION_USER
    if args[0] == 'all':
        selected_hosts = PRODUCTION_SERVERS.values()
    elif set(args) < set(PRODUCTION_SERVERS.keys()):
        selected_hosts = [PRODUCTION_SERVERS[host] for host in set(args)]
    else:
        abort("Unknown hosts!")


@task
def deploy(*args):
    env.hosts = selected_hosts

    apps = []
    if args[0] == 'all':
        apps = APPS
    elif set(args) <= set(APPS.keys()):
        apps = {k: v for k, v in APPS.iteritems() if k in args}
    else:
        abort("Unknown apps!")

    params = {}
    clone_code(params)

    all_apps_params = {}

    # First deploy without switching on all the servers.
    for app, app_type in apps.iteritems():
        print header("\n\n\t~~~~~~~~~~~~ Deploying %s@%s ~~~~~~~~~~~~" % (app, env.host))
        print task("Prepare [%s@%s]" % (app, env.host))
        if app_type == 'angular':
            build_angular_app(app, params)

        pack(app, params)

        if app_type == 'django':
            all_apps_params[app] = execute(deploy_django_app, app, params).values()[0]
        elif app_type == 'angular':
            all_apps_params[app] = execute(deploy_angular_app, app, params).values()[0]

    # If everything is ok so far, switch apps.
    for app, app_type in apps.iteritems():
        print task("Switching to new code [%s@%s]" % (app, env.host))

        if app_type == 'django':
            execute(switch_django_app, app, all_apps_params[app])
        elif app_type == 'angular':
            execute(switch_angular_app, app, all_apps_params[app])

    # Install new cron jobs.
    print task("Creating cron jobs [%s@%s]" % (app, env.host))
    execute(deploy_cron_jobs, params)


@task
def migrate(*args):
    env.hosts = selected_hosts

    apps = []
    if args[0] == 'all':
        apps = APPS
    elif set(args) <= set(APPS.keys()):
        apps = {k: v for k, v in APPS.iteritems() if k in args}
    else:
        abort("Unknown apps!")

    params = {}
    clone_code(params)

    env.hosts = [env.hosts[0]]

    for app, app_type in apps.iteritems():
        if app_type != 'django':
            continue

        print header("\n\n\t~~~~~~~~~~~~ Migrating %s@%s ~~~~~~~~~~~~" % (app, env.host))

        print task("Prepare [%s@%s]" % (app, env.host))
        pack(app, params)

        execute(real_migrate, app, params)


@task
def revert(*args):
    env.hosts = selected_hosts

    apps = []
    if args[0] == 'all':
        apps = APPS
    elif set(args) <= set(APPS.keys()):
        apps = {k: v for k, v in APPS.iteritems() if k in args}
    else:
        abort("Unknown apps!")

    for app, app_type in apps.iteritems():
        print header("\n\n\t~~~~~~~~~~~~ Reverting %s@%s ~~~~~~~~~~~~" % (app, env.host))
        print task("Revert [%s@%s]" % (app, env.host))
        if app_type == 'django':
            execute(switchback_django_app, app)
        elif app_type == 'angular':
            execute(switchback_angular_app, app)


# COMMON STUFF
def clone_code(params):
    timestamp = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
    repo_name = os.path.basename(GIT_REPOSITORY)
    project_name = os.path.splitext(repo_name)[0]

    tmp_folder = "/tmp/deploy-%s-%s" % (project_name, timestamp)
    os.makedirs(tmp_folder)

    with lcd(tmp_folder):
        tmp_folder_git = os.path.join(tmp_folder, repo_name)

        local('git clone --branch %s --depth 1 %s %s' % (DEFAULT_BRANCH, GIT_REPOSITORY, tmp_folder_git))

        commit_hash = local("git ls-remote %s %s" % (
            GIT_REPOSITORY, DEFAULT_BRANCH), True).strip().split()[0][:8]

        params['timestamp'] = timestamp
        params['commit_hash'] = commit_hash
        params['tmp_folder'] = tmp_folder
        params['tmp_folder_git'] = tmp_folder_git


def build_angular_app(app, params):
    dest_folder = os.path.join(params['tmp_folder_git'], app)
    with lcd(dest_folder):
        local('npm install')
        local('grunt')
        local('rm -rf node_modules')


def pack(app, params):
    tmp_folder = params['tmp_folder']
    timestamp = params['timestamp']
    tmp_folder_git = params['tmp_folder_git']

    with lcd(params['tmp_folder']):
        tmp_filename = os.path.join(tmp_folder, "%s-%s.tar" % (app, timestamp))

        app_folder = os.path.join(tmp_folder_git, app)
        local("tar -C %s -f %s -r ." % (app_folder, tmp_filename))

        params['tmp_filename'] = tmp_filename


def create_virtualenv(app, params):
    venv_name = '%s-%s-%s' % (app, params['timestamp'], params['commit_hash'])
    run('. /etc/bash_completion.d/virtualenvwrapper && mkvirtualenv %s' % venv_name)

    params['venv_name'] = venv_name


def unpack(app, params):
    app_folder = "~/apps/%s-%s-%s" % (app, params['timestamp'], params['commit_hash'])
    tar_name = '~/apps/%s-%s' % (app, params['timestamp'])
    put(params['tmp_filename'], 'apps/')
    run("mkdir -p %s/%s" % (app_folder, app))
    run("tar -xf %s.tar -C  %s/%s/;" % (tar_name, app_folder, app))

    params['app_folder'] = app_folder


def copy_django_settings(app, params):
    run("cp ~/apps/config/%s-localsettings.py %s/%s/%s/localsettings.py" % (
        app, params['app_folder'], app, app))


@serial
def install_dependencies(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv(params):
        run('pip install -U pip==1.4.1')
        run('pip install -r requirements.txt')


@serial
def unittests(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv(params):
        run('python manage.py test')


def manage_static(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv(params):
        run('python manage.py collectstatic --noinput')


def is_db_migrated(app, params):
    unmigrated_count = None

    dest_folder = os.path.join(params['app_folder'], app)

    with cd(dest_folder), virtualenv(params):
        unmigrated_count = run('python manage.py migrate --list | grep "\[ \]" | wc -l')

    return int(unmigrated_count) == 0


@parallel
def switch_django_app(app, params):
    with cd('~/.virtualenvs'):
        virtualenv_folder = os.path.join('~/.virtualenvs', params['venv_name'])

        # remember which was previous virtualenv release
        if exists(app):
            run("cp -a ~/.virtualenvs/{app} {virtualenv_folder}/previous".format(app=app, virtualenv_folder=virtualenv_folder))
        run("ln -Tsf %s %s" % (virtualenv_folder, app))

    with cd("~/apps/"):
        # remember which was previous app release
        if exists(app):
            run("cp -a {app} {folder}/previous".format(folder=params['app_folder'], app=app))

        run("ln -Tsf %s %s" % (params['app_folder'], app))

    print task("Restart service")
    run("supervisorctl restart %s" % app)


@parallel
def switch_angular_app(app, params):
    with cd("~/apps/"):
        # remember which was previous app release
        test_output = run('test -L {0}'.format(app), quiet=True)
        if test_output.succeeded:
            run("cp -a {app} {folder}/previous".format(folder=params['app_folder'], app=app))

        run("ln -Tsf %s %s" % (params['app_folder'], app))


@parallel
def switchback_django_app(app):
    with cd('~/.virtualenvs'):
        run("cp -a {app}/previous {app}-reverting".format(app=app))
        run("rm -f {app} && mv {app}-reverting {app}".format(app=app))
    with cd("~/apps/"):
        run("cp -a {app}/previous {app}-reverting".format(app=app))
        run("rm -f {app} && mv {app}-reverting {app}".format(app=app))

    print task("Restart service")
    run("supervisorctl restart %s" % app)


@parallel
def switchback_angular_app(app):
    with cd("~/apps/"):
        run("cp -a {app}/previous {app}-reverting".format(app=app))
        run("rm -f {app} && mv {app}-reverting {app}".format(app=app))


def tag_deploy(app, params):
    with cd(params['app_folder']):
        tag_name = '%s-%s-%s' % (app, params['timestamp'], params['commit_hash'])
        run('git tag %s' % tag_name)
        run('git push origin %s' % tag_name)


def run_migrate(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv(params):
        run('python manage.py migrate')


@parallel
def deploy_django_app(app, params):
    print task("Create virtualenv [%s@%s]" % (app, env.host))
    create_virtualenv(app, params)

    print task("Unpack [%s@%s]" % (app, env.host))
    unpack(app, params)
    copy_django_settings(app, params)

    print task('Install dependencies [%s@%s]' % (app, env.host))
    install_dependencies(app, params)

    if not is_db_migrated(app, params):
        fabric.utils.abort(error(
            'Database is not migrated. Migrate it before deploying again by running fabric migrate task.'
        ))

    print task('Manage static files [%s@%s]' % (app, env.host))
    manage_static(app, params)

    print task("Unit test [%s@%s]" % (app, env.host))
    unittests(app, params)

    print ok("%s successfully deployed at %s" % (app.capitalize(), env.host))

    return params


@parallel
def deploy_angular_app(app, params):
    print task("Unpack [%s@%s]" % (app, env.host))
    unpack(app, params)

    print ok("%s successfully deployed at %s" % (app.capitalize(), env.host))

    return params


@parallel
def deploy_cron_jobs(params):
    # with cd(params['app_folder']):
    cron_yaml_path = os.path.join(params['tmp_folder_git'], 'cron.yaml')
    with open(cron_yaml_path, 'r') as f:
        cron_yaml = yaml.load(f)
        jobs = [x['job'] for x in cron_yaml['cron'] if env.host in x.get('hosts', env.hosts)]
        temp_file = '/tmp/cron_jobs-{0}-{1}'.format(
            params['timestamp'], params['commit_hash'])
        echo_cmd = 'echo \'{0}\' > {1}'.format('\n'.join(jobs), temp_file)
        run(echo_cmd)
        run('crontab {0}'.format(temp_file))


def real_migrate(app, params):
    print task("Create virtualenv [%s@%s]" % (app, env.host))
    create_virtualenv(app, params)

    print task("Unpack [%s@%s]" % (app, env.host))
    unpack(app, params)
    copy_django_settings(app, params)

    print task('Install dependencies [%s@%s]' % (app, env.host))
    install_dependencies(app, params)

    print task("Unit test [%s@%s]" % (app, env.host))
    unittests(app, params)

    print task("Migrate [%s@%s]" % (app, env.host))
    run_migrate(app, params)

    print ok("%s successfully migrated %s" % (app.capitalize(), env.host))


def invalidate_cdn_cache(app):
    print task('Invalidate CDN cache')

    headers = {
        'Authorization': 'TOK:cd4f2739-9508-4212-ac6c-91ce4dcf1e21',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn = httplib.HTTPSConnection('api.edgecast.com')
    try:
        conn.request(
            'PUT',
            '/v2/mcc/customers/BAB2/edge/purge',
            body='{"MediaPath":"http://shcdn.zemanta.com/*", "MediaType":8}',
            headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            print error("An error occurred while invalidating CDN")
        print response.status
        print response.read()
    finally:
        conn.close()


# PRINT STUFF
def header(txt):
    return fabric.colors.yellow(txt, True)


def task(txt):
    return fabric.colors.cyan("\t== %s ==" % txt, True)


def ok(txt):
    return fabric.colors.green(txt, True)


def error(txt):
    return fabric.colors.red(txt, True)
