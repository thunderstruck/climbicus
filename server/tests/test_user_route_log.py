from datetime import datetime
from unittest import mock
from unittest.mock import Mock

import pytz

from app.models import Routes, UserRouteLog
from flask import json


def test_view_logbook(client, auth_headers_user1):
    data = {
        "user_id": 1,
        "gym_id": 1,
    }
    resp = client.get("/user_route_log/", data=json.dumps(data), content_type="application/json", headers=auth_headers_user1)
    assert resp.status_code == 200

    expected_logbook = {
        "1": {"completed": True, "created_at": "2012-03-03T10:10:10+00:00", "gym_id": 1, "id": 1, "num_attempts": None,
              "route_id": 1, "user_id": 1},
        "2": {"completed": False, "created_at": "2012-03-04T10:10:10+00:00", "gym_id": 1, "id": 2, "num_attempts": 1,
              "route_id": 3, "user_id": 1},
        "3": {"completed": True, "created_at": "2012-03-02T10:10:10+00:00", "gym_id": 1, "id": 3, "num_attempts": 10,
              "route_id": 1, "user_id": 1},
    }

    assert expected_logbook == resp.json


def test_view_logbook_one_route(client, auth_headers_user1):
    data = {
        "user_id": 1,
        "gym_id": 1,
    }
    resp = client.get("/user_route_log/1", data=json.dumps(data), content_type="application/json", headers=auth_headers_user1)
    assert resp.status_code == 200

    expected_logbook = {
        "1": {"completed": True, "created_at": "2012-03-03T10:10:10+00:00", "gym_id": 1, "id": 1, "num_attempts": None,
              "route_id": 1, "user_id": 1},
        "3": {"completed": True, "created_at": "2012-03-02T10:10:10+00:00", "gym_id": 1, "id": 3, "num_attempts": 10,
              "route_id": 1, "user_id": 1},
        "4": {"completed": True, "created_at": "2012-03-02T10:10:10+00:00", "gym_id": 1, "id": 4, "num_attempts": 10,
              "route_id": 1, "user_id": 2},
    }

    assert expected_logbook == resp.json


@mock.patch("datetime.datetime", Mock(utcnow=lambda: datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)))
def test_add_to_logbook(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "completed": True,
        "num_attempts": None,
        "route_id": 1,
        "gym_id": 1,
    }
    resp = client.post("/user_route_log/", data=json.dumps(data), content_type="application/json", headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json
    assert resp.json["msg"] == "Route status added to log"
    assert resp.json["user_route_log"] == {"completed": True, "created_at": "2019-03-04T10:10:10+00:00",
                                           "gym_id": 1, "id": 8, "num_attempts": None, "route_id": 1,
                                           "user_id": 1}

    with app.app_context():
        user_route_log = UserRouteLog.query.filter_by(id=8).one()
        assert user_route_log.completed == True
        assert user_route_log.num_attempts is None
        assert user_route_log.user_id == 1
        assert user_route_log.gym_id == 1
        assert user_route_log.route_id == 1
        assert user_route_log.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)


def test_delete_entry(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "user_route_log_id": 1,
    }
    # check it exists first
    with app.app_context():
        user_route_log = UserRouteLog.query.filter_by(id=1).one_or_none()
    assert user_route_log is not None

    resp = client.delete("/user_route_log/1", data=json.dumps(data), content_type="application/json",
                         headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json
    assert resp.json["msg"] == "user_route_log entry was successfully deleted"

    with app.app_context():
        user_route_log = UserRouteLog.query.filter_by(id=1).one_or_none()
    assert user_route_log is None


def test_delete_entry_with_invalid_id(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "user_route_log_id": 1000,
    }
    resp = client.delete("/user_route_log/1000", data=json.dumps(data), content_type="application/json",
                         headers=auth_headers_user1)

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.json["msg"] == "invalid user_route_log_id"


def test_update_count_ascents(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "completed": True,
        "num_attempts": 2,
        "route_id": 1,
        "gym_id": 1,
    }

    # verify 'before' state of averages
    with app.app_context():
        route_entry = Routes.query.filter_by(id=1).one()
        assert route_entry.avg_difficulty_name is None
        assert route_entry.avg_quality is None
        assert route_entry.count_ascents == 0
        assert route_entry.user_id == 1
        assert route_entry.gym_id == 1
        assert route_entry.area_id == 1
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)

    resp = client.post("/user_route_log/", data=json.dumps(data), content_type="application/json",
                       headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json

    with app.app_context():
        route_entry = Routes.query.filter_by(id=1).one()
        assert route_entry.avg_difficulty_name is None
        assert route_entry.avg_quality is None
        assert route_entry.count_ascents == 2
        assert route_entry.user_id == 1
        assert route_entry.gym_id == 1
        assert route_entry.area_id == 1
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)


def test_update_count_ascents_with_null_attempts(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "completed": True,
        "num_attempts": None,
        "route_id": 1,
        "gym_id": 1,
    }

    # verify 'before' state of averages
    with app.app_context():
        route_entry = Routes.query.filter_by(id=1).one()
        assert route_entry.avg_difficulty_name is None
        assert route_entry.avg_quality is None
        assert route_entry.count_ascents == 0
        assert route_entry.user_id == 1
        assert route_entry.gym_id == 1
        assert route_entry.area_id == 1
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)

    resp = client.post("/user_route_log/", data=json.dumps(data), content_type="application/json",
                       headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json

    with app.app_context():
        route_entry = Routes.query.filter_by(id=1).one()
        assert route_entry.avg_difficulty_name is None
        assert route_entry.avg_quality is None
        assert route_entry.count_ascents == 1
        assert route_entry.user_id == 1
        assert route_entry.gym_id == 1
        assert route_entry.area_id == 1
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)


def test_delete_entry_update_count_ascents(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "user_route_log_id": 5,
    }
    # check it exists first
    with app.app_context():
        user_route_log = UserRouteLog.query.filter_by(id=5).one_or_none()
    assert user_route_log is not None

    # verify 'before' state of route
    with app.app_context():
        route_entry = Routes.query.filter_by(id=user_route_log.route_id).one()
        assert route_entry.avg_difficulty_name == "fair"
        assert route_entry.avg_quality == 2.0
        assert route_entry.count_ascents == 10
        assert route_entry.user_id == 2
        assert route_entry.gym_id == 2
        assert route_entry.area_id == 2
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)

    resp = client.delete("/user_route_log/5", data=json.dumps(data), content_type="application/json",
                         headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json
    assert resp.json["msg"] == "user_route_log entry was successfully deleted"

    with app.app_context():
        route_entry = Routes.query.filter_by(id=user_route_log.route_id).one()
        assert route_entry.avg_difficulty_name == "fair"
        assert route_entry.avg_quality == 2.0
        assert route_entry.count_ascents == 8
        assert route_entry.user_id == 2
        assert route_entry.gym_id == 2
        assert route_entry.area_id == 2
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)


def test_delete_entry_update_count_ascents_with_null_attempts(client, app, auth_headers_user1):
    data = {
        "user_id": 1,
        "user_route_log_id": 6,
    }
    # check it exists first
    with app.app_context():
        user_route_log = UserRouteLog.query.filter_by(id=6).one_or_none()
    assert user_route_log is not None

    # verify 'before' state of route
    with app.app_context():
        route_entry = Routes.query.filter_by(id=user_route_log.route_id).one()
        assert route_entry.avg_difficulty_name == "fair"
        assert route_entry.avg_quality == 2.0
        assert route_entry.count_ascents == 10
        assert route_entry.user_id == 2
        assert route_entry.gym_id == 2
        assert route_entry.area_id == 2
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)

    resp = client.delete("/user_route_log/6", data=json.dumps(data), content_type="application/json",
                         headers=auth_headers_user1)

    assert resp.status_code == 200
    assert resp.is_json
    assert resp.json["msg"] == "user_route_log entry was successfully deleted"

    with app.app_context():
        route_entry = Routes.query.filter_by(id=user_route_log.route_id).one()
        assert route_entry.avg_difficulty_name == "fair"
        assert route_entry.avg_quality == 2.0
        assert route_entry.count_ascents == 9
        assert route_entry.user_id == 2
        assert route_entry.gym_id == 2
        assert route_entry.area_id == 2
        assert route_entry.created_at == datetime(2019, 3, 4, 10, 10, 10, tzinfo=pytz.UTC)
