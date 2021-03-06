"""Package contains callable methods for launching the server."""
import secrets
from logging import DEBUG
from logging import getLogger as Log
from pathlib import Path

from flask import _app_ctx_stack  # Protected variable access here is by convention.
from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from uosinterface import UOSDatabaseError
from uosinterface.util import configure_logs
from uosinterface.webapp.api import routing as api_routing
from uosinterface.webapp.auth import default_user
from uosinterface.webapp.auth import PrivilegeNames
from uosinterface.webapp.auth import routing as auth_routing
from uosinterface.webapp.dashboard import routing as dashboard_routing
from uosinterface.webapp.database import Base
from uosinterface.webapp.database import engine
from uosinterface.webapp.database import session_maker
from uosinterface.webapp.database.interface import add_user
from uosinterface.webapp.database.interface import add_user_privilege
from uosinterface.webapp.database.interface import get_user
from uosinterface.webapp.database.interface import init_privilege
from uosinterface.webapp.database.models import Privilege
from uosinterface.webapp.database.models import User
from uosinterface.webapp.database.models import UserKey
from uosinterface.webapp.database.models import UserPrivilege

login_manager = LoginManager()
csrf = CSRFProtect()


def register_blueprints(app):
    """Registers the routing for included web-app packages."""
    blueprint_packages = [api_routing, dashboard_routing, auth_routing]
    for blueprint_module in blueprint_packages:
        if hasattr(blueprint_module, "blueprint"):
            app.register_blueprint(blueprint_module.blueprint)


def register_logs(level, base_path: Path):
    """Initialises the logging functionality for the web-app package."""
    configure_logs(__name__, level=level, base_path=base_path)


def register_database(app):
    """Initialise the database and login manager the web-app package."""
    # pylint: disable = unused-variable
    # This is required for false reporting on functions triggered via callback.

    app.config["DATABASE"] = {
        "ENGINE": engine,
        # Unique requests should get unique sessions.
        # The same request should get the same session.
        "SESSION": scoped_session(
            session_maker, scopefunc=_app_ctx_stack.__ident_func__
        ),
    }
    # Adds the flask login user manager functionality.
    login_manager.init_app(app)

    @app.before_first_request
    def initialise_database(exception=None):
        Log(__name__).debug("Initialising database, %s", exception.__str__())
        Base.metadata.create_all(app.config["DATABASE"]["ENGINE"])
        # populate default data.
        with app.config["DATABASE"]["SESSION"]() as db_session:
            try:
                # Add in any program privileges.
                for privilege_name in list(PrivilegeNames):
                    init_privilege(
                        db_session, privilege_name.value, privilege_name.name
                    )
                # If there is no admin in the database, add the default admin.
                if not (
                    db_session.query(UserPrivilege)
                    .join(Privilege)
                    .filter(Privilege.name == PrivilegeNames.ADMIN.name)
                    .first()
                ):
                    db_session.add(User(**default_user))
                    add_user_privilege(
                        db_session,
                        user_value=default_user["name"],
                        user_field=User.name,
                        privilege=PrivilegeNames.ADMIN.name,
                        privilege_field=Privilege.name,
                    )
            except (SQLAlchemyError, UOSDatabaseError) as sql_exception:
                Log(__name__).error(
                    "Failed to populate defaults into database %s.",
                    sql_exception.__str__(),
                )
                db_session.rollback()
            else:
                db_session.commit()

    @app.teardown_appcontext
    def shutdown_database(exception=None):
        Log(__name__).debug("Shutting down database engine, %s", exception.__str__())
        app.config["DATABASE"]["ENGINE"].dispose()

    @login_manager.user_loader
    def load_user(user_id):
        with app.config["DATABASE"]["SESSION"]() as db_session:
            user = get_user(session=db_session, user_value=user_id)
        return user

    @login_manager.request_loader
    def request_loader(request):
        """Auth handling using the api_key header."""
        api_key = request.args.get("api_key")
        if api_key:
            with app.config["DATABASE"]["SESSION"]() as db_session:
                return get_user(db_session, user_value=api_key, user_field=UserKey.key)
        return None  # no auth


def create_app(testing: bool, base_path: Path, static_path: Path):
    """Creates the flask app and registers all addons."""
    app = Flask(
        __name__,
        static_folder=static_path.__str__(),
        template_folder=static_path.joinpath(Path("templates/")).__str__(),
    )
    csrf.init_app(app)
    app.config["TESTING"] = testing
    app.config["SECRET_KEY"] = secrets.token_urlsafe(32)
    register_database(app)
    register_blueprints(app)
    register_logs(DEBUG, base_path=base_path)
    Log(__name__).debug("Static resolved to %s", static_path.__str__())
    return app
