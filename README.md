# Student News Application - Django Capstone

A News Application built with Django and Django REST Framework.

## Main features

- Reader, Editor and Journalist roles.
- Django groups and permissions created by `setup_groups`.
- Reader subscriptions to publishers and journalists.
- Journalist article creation, independently or for affiliated publishers.
- Editors review publisher articles they oversee and any independent articles.
- Publisher newsletters containing only approved articles from that publisher.
- Independent journalist newsletters containing only that journalist's approved independent articles.
- Email notification after article approval.
- X post on article approval.
- REST API using Django REST framework and token authentication.

## Setup

1. Create a virtual environment:

python -m venv venv

2. Activate it and install requirements:

pip install -r requirements.txt

3. Run migrations:

python manage.py makemigrations
python manage.py migrate

4. Create an admin user:

python manage.py createsuperuser

5. Start the server:

python manage.py runserver

Open `http://127.0.0.1:8000/`.

## MariaDB

CREATE DATABASE news_db;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'news_password';
GRANT ALL PRIVILEGES ON news_db.\* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;

## Roles

`setup_groups` creates:

- **Reader** - view articles, newsletters and publishers.
- **Editor** - view, update and delete articles/newsletters and manage publisher data.
- **Journalist** - create, view, update and delete articles/newsletters and view publishers.

Registration assigns the user to the group matching their selected role.

## API

Token endpoint:

POST /api/token/

API endpoints:

GET /api/articles/
GET /api/articles/subscribed/
GET /api/articles/<id>/
POST /api/articles/
PUT /api/articles/<id>/
DELETE /api/articles/<id>/

Additional simple endpoints:

GET /api/publishers/
GET /api/users/
GET /api/newsletters/
POST /api/newsletters/

Send the token as:

Authorization: Token <token>

## Tests

Run:

python manage.py test news

The tests cover authentication, role access, subscribed articles, article creation/update/delete, newsletters and the approval notification logic.

## Email and X integration

Emails appear in the terminal.

The X integration uses Python `requests`.

## Planning diagrams

The `Planning` folder contains four draw.io files:

- `UseCaseDiagram.drawio`
- `ClassDiagram.drawio`
- `SequenceDiagram.drawio`
- `RESTAPISequenceDiagram.drawio`
