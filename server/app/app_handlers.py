import json

from flask import request, current_app, abort, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, current_user
from werkzeug.exceptions import HTTPException


def register_handlers(app, jwt):
    @app.before_request
    def check_auth_required():
        if app.config["DISABLE_AUTH"]:
            return

        if not request.endpoint:
            return

        view = current_app.view_functions[request.endpoint]
        if not getattr(view, "jwt_auth_required", True):
            return

        verify_jwt_in_request()
        verify_request_data()
        verify_user_identity()


    @app.errorhandler(Exception)
    def http_error_handler(error):
        if isinstance(error, HTTPException):
            code = error.code
            msg = error.description
        else:
            code = 500
            msg = str(error)

            current_app.logger.exception(error)

        return jsonify(msg=msg), code


    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id


    @jwt.user_loader_callback_loader
    def user_lookup_callback(identity):
        from app.models import Users
        return Users.query.filter_by(id=identity).one_or_none()


def no_jwt_required(fn):
    fn.jwt_auth_required = False
    return fn


def verify_request_data():
    if not ("json" in request.form or request.is_json):
        abort(400, "request data must be in json or contain json")


def verify_user_identity():
    if "json" in request.form:
        json_data = json.loads(request.form["json"])
    else:
        json_data = request.json

    user_id = json_data.get("user_id")

    if user_id is None:
        abort(400, "'user_id' is missing from the request data")

    if get_jwt_identity() != int(user_id):
        abort(403, "user is not authorized to access the resource")

    if current_app.config["ENABLE_USER_VERIFICATION"] and (not current_user.verified):
        abort(403, "user is unverified")
