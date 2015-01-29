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

In prodution, we use PostgreSQL 9.3 database so it is best to install it for development as well.

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

### Visualize models
```bash
python manage.py graph_models -a -g -o my_project_visualized.png
```

### Client

We use Grunt for building the app and Bower for management of third-party components. Third-party components are part of the repository and are to be committed while node modules used with Grunt are only develoment dependencies and are not to be committed.

All the commands bellow assume that you are located in client subdirectory.

Make sure that you have node.js, npm, grunt and grunt-cli installed.

Install local development node modules:
```bash
npm install
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

## Testing

### Client

#### Unit testing

We use Jasmine as testing framework and Karma as test runner. Before running tests, make sure you have karma installed. Karma is integrated with Grunt, so tests can be run with:
```bash
grunt test
```

This will run tests in local Chrome browser.

Tests can also be run in SauceLabs cloud. First, copy the sauce.json template:
```bash
cp test/sauce.json.template test/sauce.json
```

and change it as needed. Then run:
```bash
grunt test --sauce
```

In this case tests are executed in 7 browsers, defined in test/karma.conf-sauce.js.

Karma can also auto-watch files and run test on every change:
```bash
karma start test/karma.conf.js
```

#### End-to-end testing

Integration testing is done using <a href="https://github.com/angular/protractor">Protractor</a>. 

To setup, first copy the protractor.localconf.js template:
```bash
cp test/protractor.localconf.json.template test/protractor.localconf.json
```

and modify as needed.

You will also need to load protractor fixtures into your database. You can do this by changing directory to server/ and running:
```bash
python manage.py loaddata protractor
```

To test, first ensure that your dev server is running. Then run:
```bash
grunt e2e
```

The test suite will be run in your local Chrome browser.

##### Running tests on SauceLabs

You can also test on multiple browsers using SauceLabs cloud. To do this, first set up your sauce.json file as described in the Unit Testing section if you haven't done that yet.

Next, create a secure tunnel to the SauceLabs cloud by following the instructions at https://saucelabs.com/connect.

After you are done, you can run your tests using
```bash
grunt e2e --sauce
```

##### Google Analytics Postclick Data Import

Clients send us daily reports by landing pages from their Google Analytics. We import the postclick and conversion metrics into ONE's reports. The general process is described in the sequence diagram below

![Image](docs/ga_import_sequence.png)

## Alerting

In the following section, we will review the most important metrics and responses to alerts, attached to them.

##### Demo Data
Demo is an important sales tool to convince clients to test or even buy our services. That is way it is important, 
that data is refreshed. 

[Is there recent data for demo?](https://metrics.librato.com/metrics/demo.total_recent_impressions?duration=604800)

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






