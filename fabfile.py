import contextlib
from datetime import datetime
import httplib
import os

from fabric.api import abort, env, execute, cd, lcd, local, run, task, prefix, put, parallel, serial
import fabric.colors
import fabric.utils

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


APPS = ('server', 'client')

STAGING_SERVERS = {
    'stadium01': 'one@stadium01.zemanta.com'
}

PRODUCTION_SERVERS = {
    'knot01': 'one@knot01.zemanta.com'
}

GIT_REPOSITORY = 'git@github.com:Zemanta/zemanta-eins.git'
DEFAULT_BRANCH = 'master'


env.forward_agent = True
if env.ssh_config_path and os.path.isfile(os.path.expanduser(env.ssh_config_path)):
    env.use_ssh_config = True


@contextlib.contextmanager
def virtualenv():
    venv_prefix = '. /etc/bash_completion.d/virtualenvwrapper && workon %s' % env.venv_name
    with prefix(venv_prefix):
        yield


# SETTINGS
@task
def staging(*args):
    if args[0] == 'all':
        env.hosts = STAGING_SERVERS.values()
    elif set(args) < set(STAGING_SERVERS.keys()):
        env.hosts = [STAGING_SERVERS[host] for host in set(args)]
    else:
        abort("Unknown hosts!")


@task
def production(*args):
    if args[0] == 'all':
        env.hosts = PRODUCTION_SERVERS.values()
    elif set(args) < set(PRODUCTION_SERVERS.keys()):
        env.hosts = [PRODUCTION_SERVERS[host] for host in set(args)]
    else:
        abort("Unknown hosts!")


@task
def deploy(*args):
    apps = []
    if args[0] == 'all':
        apps = APPS
    elif set(args) <= set(APPS):
        apps = args
    else:
        abort("Unknown apps!")

    params = {}
    clone_code(params)

    for app in apps:
        print header("\n\n\t~~~~~~~~~~~~ Deploying %s@%s ~~~~~~~~~~~~" % (app, env.host))

        print task("Prepare [%s@%s]" % (app, env.host))
        pack(app, params)

        execute(real_deploy, app, params)

        # invalidate_cdn_cache(app)


@task
def migrate(*args):
    apps = []
    if args[0] == 'all':
        apps = APPS
    elif set(args) < set(APPS):
        apps = args
    else:
        abort("Unknown apps!")

    params = {}
    clone_code(params)

    env.hosts = [env.hosts[0]]

    for app in apps:
        print header("\n\n\t~~~~~~~~~~~~ Migrating %s@%s ~~~~~~~~~~~~" % (app, env.host))

        print task("Prepare [%s@%s]" % (app, env.host))
        pack(app, params)

        execute(real_migrate, app, params)


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

    env.venv_name = venv_name


def unpack(app, params):
    app_folder = "~/apps/%s-%s-%s" % (app, params['timestamp'], params['commit_hash'])
    tar_name = '~/apps/%s-%s' % (app, params['timestamp'])
    put(params['tmp_filename'], 'apps/')
    run("mkdir -p %s/%s" % (app_folder, app))
    run("tar -xf %s.tar -C  %s/%s/;" % (tar_name, app_folder, app))
    run("cp ~/apps/config/%s-localsettings.py %s/%s/%s/localsettings.py" % (app, app_folder, app, app))

    params['app_folder'] = app_folder


@serial
def install_dependencies(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    print dest_folder
    with cd(dest_folder), virtualenv():
        run('pip install -U pip==1.4.1')
        run('pip install -r requirements.txt')


@serial
def unittests(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv():
        run('python manage.py test')


def manage_static(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv():
        run('python manage.py collectstatic --noinput')


def is_db_migrated(app, params):
    unmigrated_count = None

    dest_folder = os.path.join(params['app_folder'], app)

    with cd(dest_folder), virtualenv():
        unmigrated_count = run('python manage.py migrate --list | grep "\[ \]" | wc -l')

    return int(unmigrated_count) == 0


def switch(app, params):
    with cd('~/.virtualenvs'):
        virtualenv_folder = os.path.join('~/.virtualenvs', env.venv_name)
        run("ln -Tsf %s %s" % (virtualenv_folder, app))

    with cd("~/apps/"):
        run("ln -Tsf %s %s" % (params['app_folder'], app))

    print task("Restart service")
    run("supervisorctl restart %s" % app)


def tag_deploy(app, params):
    with cd(params['app_folder']):
        tag_name = '%s-%s-%s' % (app, params['timestamp'], params['commit_hash'])
        run('git tag %s' % tag_name)
        run('git push origin %s' % tag_name)


def run_migrate(app, params):
    dest_folder = os.path.join(params['app_folder'], app)
    with cd(dest_folder), virtualenv():
        run('python manage.py migrate')


@parallel
def real_deploy(app, params):
    print task("Create virtualenv [%s@%s]" % (app, env.host))
    create_virtualenv(app, params)

    print task("Unpack [%s@%s]" % (app, env.host))
    unpack(app, params)

    print task('Install dependencies [%s@%s]' % (app, env.host))
    install_dependencies(app, params)

    print task('Manage static files [%s@%s]' % (app, env.host))
    manage_static(app, params)

    print task("Unit test [%s@%s]" % (app, env.host))
    unittests(app, params)

    if not is_db_migrated(app, params):
        fabric.utils.abort(error(
            'Database is not migrated. Migrate it before deploying again by running fabric migrate task.'
        ))

    print task("Switching to new code [%s@%s]" % (app, env.host))
    switch(app, params)

    # print task('Tagging successful deploy [%s@%s]' (app, env.hosts))
    # tag_deploy(app, params)

    print ok("%s successfully deployed at %s" % (app.capitalize(), env.host))


def real_migrate(app, params):
    print task("Create virtualenv [%s@%s]" % (app, env.host))
    create_virtualenv(app, params)

    print task("Unpack [%s@%s]" % (app, env.host))
    unpack(app, params)

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
