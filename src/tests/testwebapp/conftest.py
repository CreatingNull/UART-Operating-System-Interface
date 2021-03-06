"""Configure the general test fixtures for testing the web-app."""
from configparser import ConfigParser
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from uosinterface.webapp import create_app
from uosinterface.webapp.database import Base
from uosinterface.webapp.database import KeyTypes
from uosinterface.webapp.database.models import APIPrivilege
from uosinterface.webapp.database.models import Privilege
from uosinterface.webapp.database.models import User
from uosinterface.webapp.database.models import UserKey
from uosinterface.webapp.database.models import UserPrivilege

# pylint: disable=redefined-outer-name
# This is because wrapped pytest fixtures share the namespace by default.

test_user = {
    "name": "JaneDoe",
    "passwd": "jane.test",
    "email_address": "jane.doe@nulltek.xyz",
}
test_privilege = {"id": 9999, "name": "tester"}


@pytest.fixture(scope="package")
def client(database: sessionmaker):
    """Web-app fixture to use for test coverage."""
    parser = ConfigParser()
    parser["Flask Config"] = {
        "TESTING": "True",
        "SECRET_KEY": "Testing",
        "DATABASE": {"SESSION": database},
    }
    base_dir = Path(__file__).resolve().parents[3]
    static_dir = base_dir.joinpath("src/uosinterface/webapp/static/")
    app = create_app(parser, base_dir, static_dir)
    with app.test_client() as client_instance:
        yield client_instance


@pytest.fixture(scope="package")
def database():
    """In memory blank test database from the declarative model."""
    engine = create_engine("sqlite:///:memory:", future=True)
    session_maker = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )
    Base.metadata.create_all(engine)  # create our model
    __populate_test_data(session_maker())
    yield session_maker
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(database: sessionmaker):
    """Creates a session for use against the test database."""
    with database.begin():
        with database() as session:
            yield session
            session.rollback()  # cleanup the state of the test database during teardown


@pytest.fixture(scope="function")
def db_user(db_session: Session):
    """Returns the test user object for reference in tests."""
    yield db_session.query(User).filter(User.name == test_user["name"]).first()


@pytest.fixture(scope="function")
def db_privilege(db_session: Session):
    """Returns the test user object for reference in tests."""
    yield db_session.query(Privilege).filter(
        Privilege.name == test_privilege["name"]
    ).first()


def __populate_test_data(db_session: Session):
    """Populates a test dataset across all tables."""
    # Add an test privilege.
    db_session.add(Privilege(**test_privilege))
    # Populate a test user.
    db_session.add(User(**test_user))
    db_session.flush()
    user_id = (
        db_session.query(User.id)
        .filter(User.name == test_user["name"])
        .scalar_subquery()
    )
    privilege_id = (
        db_session.query(Privilege.id)
        .filter(Privilege.name == test_privilege["name"])
        .scalar_subquery()
    )
    # Populate a relationship between jane and tester.
    db_session.add(UserPrivilege(user_id=user_id, privilege_id=privilege_id))
    # Add an api key for the user.
    db_session.add(UserKey(key_length=64, user_id=user_id, key_type=KeyTypes.API))
    db_session.flush()
    # Populate a relationship between jane's API key and tester.
    db_session.add(
        APIPrivilege(
            key_id=db_session.query(UserKey.id)
            .filter(UserKey.user_id == user_id)
            .scalar_subquery(),
            privilege_id=privilege_id,
        )
    )
    db_session.commit()
