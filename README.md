# Zemanta Eins

Nachfrageseite-Plattform (en: **Zemanta One** - A Demand Side Platform.)

## Code Organization

Code is organized in two units:
* server: contains all the server side code, that is database and API built with Django 1.7.
* client: a web application built with AngularJS 1.2.x. This client connect to server via API.

### Server

Server consists of a single Django app named dash. This app contains all the models needed for it to work correctly.

## How To Setup

### Server

In prodution, we use MySQL database so it is best to install it for development as well.

All the command bellow assume that you are located in server subdirectory.

Create virtualenv and install requirements with pip:
```bash
pip install -r requirements.txt
```

Copy server/localsettings.py.temlate to server/localsettings.py and adjust them accordingly.

Create a database as specified in localsettings.py, eg. write something like this in mysql shell:
```
CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';
CREATE DATABASE databasename CHARACTER SET utf8 COLLATE utf8_general_ci;
GRANT ALL ON databasename.* TO 'username'@'localhost';
```

Initialize database:
```bash
python manage.py migrate
```
### Visualize models
```bash
python manage.py graph_models -a -g -o my_project_visualized.png
```
