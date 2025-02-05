import click
from flask.cli import with_appcontext

from app import db
from scripts.dummy_db_data import preload_dummy_data, create_user, create_gym


@click.command("recreate-db")
@click.option("--tables", type=str)
@click.option("--data-source", type=str, default="testing")
@with_appcontext
def recreate_db_cmd(tables, data_source):
    db.drop_all()
    db.create_all()
    print("Initialised the database")

    if tables is not None:
        tables = tables.split(",")
    preload_dummy_data(db, tables, data_source)
    print("Preloaded dummy data in the database")


@click.command("create-user")
@click.option("--name", type=str)
@click.option("--email", type=str)
@click.option("--password", type=str)
@with_appcontext
def create_user_cmd(name, email, password):
    create_user(db, name, email, password)
    print(f"Created new user '{name}' ({email})")


@click.command("create-gym")
@click.option("--name", type=str)
@click.option("--bouldering/--no-bouldering", default=False)
@click.option("--sport/--no-sport", default=False)
@with_appcontext
def create_gym_cmd(name, bouldering, sport):
    create_gym(db, name, bouldering, sport)
    print(f"Created new gym '{name}'")
