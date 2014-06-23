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
