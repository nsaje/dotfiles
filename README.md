# Zemanta Eins

Nachfrageseite-Plattform (en: **Zemanta One** - A Demand Side Platform.)


## Code Organization

Code is organized in two units:
* server: contains all the server side code, that is database and API built with Django 1.7.
* client: a web application built with AngularJS 1.2.x. This client connect to server via API.

### Server

Server consists of the following Django apps:
* zemauth: custom authentication app which allows for authentication with an e-mail and Google. It defines its own User model which is used in the project instead of django.contrib.auth.models.User. When referencing it as a relationship in your own models, use settings.AUTH_USER_MODEL instead.
* dash: this app contains all the models and APIs for the dashboard.

### Client

Client is a web client built on top of AngularJS. It uses Server API to communicate with backend.

## How To Setup

### Server

#### Development databases

For development, you can use the development databases running on AWS.
Howto and connection details are specified in the [Z1 Staging Data repo](https://github.com/Zemanta/z1-staging-data/blob/master/README.md)

#### Local databases

In production, we use PostgreSQL 9.3 database so it is best to install it for development as well.

All the commands bellow assume that you are located in server subdirectory.

Create virtualenv and install requirements with pip:
```bash
pip install -r requirements.txt
```

You can also install development requirements with additional tools useful during development:
```bash
pip install -r requirements_dev.txt
```

Copy server/localsettings.py.temlate to server/localsettings.py and adjust them accordingly.

Create a database as specified in localsettings.py, eg. write something like this in postgresql shell:
```
CREATE USER user_name WITH ENCRYPTED PASSWORD 'password';
ALTER USER user_name CREATEDB;
CREATE DATABASE database_name;
GRANT ALL PRIVILEGES ON DATABASE database_name TO user_name;
```

Check /etc/postgresql/9.3/main/pg_hba.conf and change line "local all all peer" to "local all all md5".

Restart PostgreSQL:
```bash
sudo /etc/init.d/postgresql restart
```

Initialize database:
```bash
python manage.py migrate
```

Create an Amazon Redshift database and fill out the credentials in `localsettings.py` for your `STATS_DB_NAME` database. You can use credentials specified for [end-to-end tests](https://sites.google.com/a/zemanta.com/root/engineering/amazon-redshift-e2e-credentials) to login into Redshift (you can use `psql`) and create a new database and user which you will use for development. Passwords should be 8-64 characters in length and should contain one uppercase, one lowercase letter and one number, [more here](http://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_USER.html).

```sql
CREATE USER user_name WITH PASSWORD 'password';
CREATE DATABASE database_name WITH OWNER user_name;
```

Apply the schema to the newly created Amazon Redshift database:
```bash
python manage.py redshift_migrate
```

There are Redshift unit tests but they aren't run automatically. You can run them with:

```bash
python manage.py test --redshift
```

### Setting up "eins" and "einsstatic" Docker containers on OSX

This setup is meant for designers to quickly setup development environment and start editing CSS and sending consequent LESS fixes on GitHub.

#### Docker installation

- Install [Docker Toolbox](https://docs.docker.com/mac/step_one/).

- Login to [Docker Hub](https://hub.docker.com/) (create account if needed):

```bash
docker login
```

- Run "Docker Quickstart Terminal" app. This will setup default VM in VirtualBox.

#### "eins" and "einsstatic" Docker containers setup

**NOTE: all of the following terminal commands should be executed from the zemanta-eins root directory.**

Make sure default VM is running and correct environmental variables are exported:

```bash
docker-machine start default
eval $(docker-machine env default)
```

Setup VirtualBox portforwarding:

```bash
VBoxManage controlvm default natpf1 "einsstatic,tcp,127.0.0.1,9999,,9999"
```

Above command will forward requests to http://localhost:9999 from host's port 9999 to default VM's port 9999. This is needed for serving static content.

Copy localsettings.py.circle-ci to localsettings.py:

```bash
cp server/server/localsettings.py.circle-ci server/server/localsettings.py
```

Edit DATABASES setting in **localsettings.py** to look similar to this: (and **insert actual connection details found on [Z1 Staging Data repo](https://github.com/Zemanta/z1-staging-data/blob/master/README.md).**)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': 0
    },
    STATS_DB_NAME: {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': 0
    }
}
```

Run "eins" and "einsstatic" containers for the first time: (be patient, a lot of data has to be downloaded)

```bash
docker-compose -f docker-compose.yml.eins-einsstatic up -d
```

Now you can use the "Kitematic" app to start/stop "eins" and "einsstatic" containers. **Important: default VM needs to be running.** If not sure, run this:

```bash
docker-machine start default
eval $(docker-machine env default)
```

#### Accessing z1
To find the URL to access z1 from the host, run ```docker-machine ip```. Enter returned IP in your browser's address bar, followed by port number 8000 (e.g. http://192.168.99.100:8000/).

Now you have a functioning development environment. Static files are being watched and recompiled on changes automatically.


### Visualize models
```bash
python manage.py graph_models -a -g -o my_project_visualized.png
```

### Client

We use Grunt for building the app and Bower for management of third-party components. Third-party components are part of the repository and are to be committed while node modules used with Grunt are only develoment dependencies and are not to be committed.

All the commands bellow assume that you are located in client subdirectory.

Make sure that you have node.js, npm, bower, grunt and grunt-cli installed.

Install local development node modules:
```bash
npm install
bower install --dev
```

Now you have grunt and all the development dependencies installed so you can run grunt in order to build it:
```bash
grunt
```

Built client app will be placed in dist directory.

You can also run grunt watch to build it automatically while working on it:
```bash
grunt watch
```

For development, you can run grunt dev which also runs server on port 9999 and is reloaded after each change to source file:
```bash
grunt dev
```
### Debug toolbar

The debug toolbar will help you profile your code and templates, find slow and duplicated queries, find if cache is hit or miss etc. If you're interested
in using it, you can do so by:

1. installing development requirements `pip install -r requirements_dev.txt` and then
2. enabling the toolbar in `localsettings.py`:

    ```
    ENABLE_DEBUG_TOOLBAR = True
    ```

3. After that debug toolbar will be shown as a part of developemnt z1 client app. This toolbar is not meant for one page apps (it doesn't refresh for ajax requests)
and thus we need to install a [debug toolbar panel chrome extension](https://chrome.google.com/webstore/detail/django-debug-panel/nbiajhhibgfgkjegbnflpdccejocmbbn) that will
show the panel in a separate developemnt tools tab for every request we make. If the one behind the given link doesn't work for you
try with [this fork](https://github.com/perython/chrome-django-panel/tree/master) - it solves display problems and at the time I was writting this it wasn't yet merged
into the master panel.

_NOTE_: In case you're not running your development django server on localhost, add `INTERNAL_IPS` to your settings, where you list your server IPs. For example:

```
INTERNAL_IPS = ['127.0.0.1', '192.168.10.1', '10.0.2.2']
```

![Image](docs/debug_toolbar.png)


## Linting

We have [pep8](https://pypi.python.org/pypi/pep8) and [eslint](http://eslint.org/docs/rules/) set up on circle CI. Meaning, that the build will break, if you will commit unconventional code.

We suggest using a pep8 + eslint in your code editor alongside running `./lint_check.sh` on your code before commiting to this repository. Git pre-commit hooks are great too on your local machine dev setup.


## Documentation

Documentation for the REST API is built on CI and deployed to dev.zemanta.com by deploykitty whenever Z1 is deployed.
When modifying or changing its theme, you can run a preview server with `./server/restapi/docs/build.sh --server`.


## Testing

### Client

#### Unit testing

We use Jasmine as testing framework and Karma as test runner. Before running tests, make sure you have karma installed. Karma is integrated with Grunt, so tests can be run with:
```bash
grunt test
```

This will run tests in local Chrome browser.

Karma can also auto-watch files and run test on every change:
```bash
npm run watch-test
```

### Server

In the case you are using staging or other database for running Z1 locally running unit tests can become
very slow. You can provide additional entries in your DATABASES dictionary with prefix 'testing\_'. When
running tests these configuration entries will have the prefix 'testing\_' removed and will replace existing
entries in LOGGING setting.

And example config for using staging when running with ./manage.py runserver and local database for unit testing.

```python
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'dev',
		'HOST': 'staging-host.com',
		'USER': 'staging',
		'PASSWORD': '...',
		'PORT': 5432
	},
	'testing_default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'z1',
		'USER': 'z1',
		'PASSWORD': '...',
		'PORT': 5440
	}
}
```

You can also speed up the test suite by using `--parallel` flag. In order to
reap the most benefits, you can also use `--keepdb` flag to avoid setting up
test databases on every test run. When using `--keepdb`, the
`--skip-transaction-tests` should also be used. It was created as a workaround
for transaction tests truncating tables after they run. Since a part of app data
is loaded into the databases using data migrations, it will be missing on the
next run if the flag is not used. The flag will likely be obsolete when
https://code.djangoproject.com/ticket/25251 is closed.

The final command would then look like
```bash
./manage.py test --keepdb --parallel --skip-transaction-tests
```

### REST API Acceptance testing

REST API is using [dredd](https://github.com/apiaryio/dredd) for acceptance testing.
Dredd parses the api_blueprint.md file and executes the payloads against a test server.

It checks the returned JSON for conformity. **ATTENTION**: It doesn't check the content
of the JSON, just the schema! E.g. the JSON must contain all fields etc -
[more on what it checks](http://www.relishapp.com/apiary/gavel/docs/expectations/body-json-example)).
This means that the documentation and the fixtures don't have to match 100%.

### Test ride your pull request in production

**WARNING** Using this you can change production data through code that has not been reviewed yet. Use with care.

The following script enables you to test run your backend changes from a pull request on production data. Front-end
builds are not yet supported as builds that are not from master branch do not get uploaded to s3.

1. Use `runssh` to get a container with the build of you pull request `runssh z1 ANY {your build number}`.
2. Ssh into the container and set the following settings in `server/localsettings.py`:
   ```
   SECURE_SSL_REDIRECT = False

   # put here the current build of the master branch (its used to get static files from s3 which were not uploaded for your pull request)
   # this line should be located before the `if BUILD_NUMBER:` statement
   BUILD_NUMBER = '123245'
   ```
3. Save and run server `./manage.py runserver`.
4. Go to your local terminal and tunnel the connection to your localhost:
   ```
   # format: {kitty ssh command} -L {your local port}:localhost:8000 -N

   ssh -p 37076 root@ec2-54-152-214-179.compute-1.amazonaws.com -L 9871:localhost:8000 -N
   ```
5. Visit `localhost:{your local port}` and you should be running your PR backend on production data.

## Alerting

In the following section, we will review the most important metrics and responses to alerts, attached to them.

##### Demo Data
Demo is an important sales tool to convince clients to test or even buy our services. That is way it is important,
that data is refreshed.

[Is there recent data for demo?](https://metrics.librato.com/metrics/demo.total_recent_impressions?duration=604800)
[Has data refreshed successfully?](https://metrics.librato.com/metrics/reports.refresh_demo_data_successful?duration=604800)
[Were there errors during demo data refreshing?](https://metrics.librato.com/metrics/reports.refresh_demo_data_failed?duration=604800)

##### Tasks
Zemanta One keeps track of the actions, that need to be performed by Zemanta Zwei. These tasks constist of adjusting CPC bids, to daily budgets, and getting newest reports, etc. The important metric here is the number of failed tasks that occur through time.

[Number of failed manual tasks](https://metrics.librato.com/metrics/n_cmd_failed?duration=86400)

It's important that data and actions are in sync with external systems. This is why we need to track, how many hours passed from last sync. (If the delay is high, it could mean problems in backend (zwei) or error in payloads sent via eins)

[Last successful sync](https://metrics.librato.com/metrics/actionlog.hours_since_last_sync?duration=86400)

There is also an alert, which prevents for automatic action to stay in waiting state for more than 24 hours (from it's creation till the hourly sync)

[Oldest automatic action waiting](https://metrics.librato.com/metrics/actionlog.hours_oldest_auto_cmd_waiting)

Zemanta zwei has its own queue, filled with tasks from zemanta one. The queues should not get too full, since this means delay in reporting, which directly effects end user.

[Number of messages](https://metrics.librato.com/metrics/AWS.SQS.ApproximateNumberOfMessagesVisible?duration=10800)

##### Data consistency
We are aggregating lots of data (impressions, visits, conversions) via external systems. It is important, that what we aggregate and report to the end user consistently. Composite difference in preaggregation graph, shows the difference between aggregated and reported values. This means, that graphs should have the value of 0.

[Data consistency dashboard](https://metrics.librato.com/dashboards/46795)

##### New Relic
New Relic supports alerting based on APDEX (Apdex is an industry standard to measure users' satisfaction with the response time of an application or service) and ERROR RATE. Alerts are fired, when APDEX < 0.5
ERROR RATE > 13.6%

[New Relic](https://rpm.newrelic.com/accounts/719319/applications/4618367)


## Implementing fetures in DEMO

Demo consists of a group of decorators (`client/one/js/demo.js`), defaults (`client/one/js/constants/demo.js`) and services:
- HTTP get request cache (`client/one/js/services/zem_demo_cache_service.js`) - keys are server URL-s
- ad groups state object (`client/one/js/services/zem_demo_ad_groups_service.js`) - support for persistant ad group information
- sources state object (`client/one/js/services/zem_demo_sources_service.js`) - support for persistant content ad source list
- content ads state object (`client/one/js/services/zem_demo_content_ads_service.js`) - support for persistant contnt ad actions (pause, resume ... )

For most of the features cache is enough. For example:
- creating a campaign or updating an existing campaign: cache[`/api/campaigns/ID/settings/`] <- campaign_data

Media sources, ad groups and content ads are a bit more complicated because data needs to be propagated to many different client pages.
State objects apply changes to different tables. Example: content ads table shows enabled media sources for each ad - sources state object applies enabled and paused media sources to content content ads.

Each of these services has its api methods exposed and should be self-explanatory.

### API service decorators
First thing you want to do is to *fake/append to/change* a server request using cache and/or state objects.

Example: campaign list from accounts perspective
```js
$delegate.accountCampaignsTable.get = (function (backup) {
    return function demo() {
		return backup.apply(null, arguments).then(function (data) {
			data.is_sync_recent = true;
			angular.forEach(newCampaigns, function (_, campaignId) {
				var cached = zemDemoCacheService.get('/api/campaigns/' + campaignId + '/settings/');
				data.rows.push(defaults.campaignsTableRow(cached.settings.name, campaignId));
			});
			return data;
		});
	};
}($delegate.accountCampaignsTable.get));
```
Notes:
- only the decorator has to have a backup of the unmocked api method
- every mocked method is named *demo* because we wish to distinguish between mocked and original methods in tests

And to make this possible, we also need to completely mock the PUT requests:
```js
$delegate.accountCampaigns.create = function demo(id) {
    var deferred = $q.defer(),
        settings = defaults.newCampaignSettings(zemDemoCacheService.generateId('campaign')),
        campaign = angular.extend({}, {
            accountManagers: defaults.accountManagers,
            salesReps: defaults.accountManagers,
            history: [{
                changedBy: 'test.account@zemanta.si',
                changesText: 'Created settings',
                showOldSettings: false,
                datetime: (new Date()).toISOString()
            }], canArchive: false,  canRestore: false,
            settings: settings
        });
    newCampaigns[settings.id] = 1;
    demoInUse = true;
    zemDemoCacheService.set('/api/campaigns/' + settings.id + '/settings/', campaign);
    deferred.resolve(settings);
    return deferred.promise;
};
```

Because we want demo to work a little bit differently, there is some demo code hidden in controllers and other services. You can find it by greping for `$window.isDemo`.

### Pingdom transaction monitor

Always check if your changes affect demo transaction monitors. Be careful when changing demo defaults.
Current monitors:
- *demo campaign/adgroup management*: creating campaign, adgroup, uploading content ads
  - causes: errors in demo code
  - solution: run e2e tests again and find the bug in the code
- *demo defaults*: checking default ad group name, default media sources
  - causes: updated demo defaults
  - solution: check for changes in `client/one/js/constants/demo.js` and update the transaction monitor accordingly
- *demo navigation*: navigation with left sidebat and tabs between existing and created campaigns/adgroups
  - causes: production data changes
  - solution: update the transaction monitor with new demo campaigns and adgroups
If any monitor fails in the *first four steps*, there was a problem with login (usually database timeouts etc.).


## Database migrations - adding field with a default value to a high-throughput table

In PostgreSQL, adding a field with a default value causes the default value to be written to every existing row [1].
Since PostgreSQL updates rows by copying them and then modifying them, this is a slow operation. In addition to that,
these writes are done inside an exclusive table lock (acquired by the ALTER TABLE statement), which causes downtime
in high-throughput applications.

To combat that, adding field with a default value should be done in multiple steps. Below is a Django-specific procedure.


1. **Create a nullable field without a default and create a migration.** This will only add a field to a table and won't
   cause any writes to happen, so it is very fast.

```python
    my_new_field = models.CharField(max_length=127, blank=True, null=True)
```

```bash
    ./manage.py makemigrations
```

2. **Assign a default to a field and create a migration.** This will not write the default to existing rows, but will cause
   Django to start writing the default value into new rows (django doesn't keep defaults in the RDBMS but in its ORM).

```python
    my_new_field = models.CharField(max_length=127, blank=True, null=True, default='mydefault')
```

```bash
    ./manage.py makemigrations
```

3. **Run migrations and deploy.** Migrating and deploying at this stage ensures that all the server processes are aware of
   the field and are writing default values into it. **It is important to have two migration files here (one from each
   of the 1 & 2 steps), otherwise Django will merge the two steps and use the performance-impacting approach.**

4. **Set field to NOT NULL**. This will update all the rows, but will do so using an UPDATE WHERE statement, which uses
   row-level locks instead of table-level, so it will not impact performance (at least not nearly as much). If/when we start
   having issues with this approach, we'll have to perform this step in batches [2][3].

```python
    my_new_field = models.CharField(max_length=127, blank=True, null=False, default='mydefault')
```

```bash
    ./manage.py makemigrations
```

5. **Run migrations and deploy.**

[1] http://www.databasesoup.com/2013/11/alter-table-and-downtime-part-i.html

[2] http://pankrat.github.io/2015/django-migrations-without-downtimes/

[3] https://docs.djangoproject.com/en/1.10/howto/writing-migrations/#non-atomic-migrations
