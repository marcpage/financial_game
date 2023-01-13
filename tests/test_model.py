#!/usr/bin/env python3

import tempfile

import financial_game.model


def test_user():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        db.create_user("john.appleseed@apple.com", "Setec astronomy", "John")
        db.create_user("Jane.Doe@apple.com", "too many secrets", "Jane")

        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        assert db.count_users() == 2, "users = {db.count_users()}"
        db.flush()
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.find_user("john.appleseed@apple.com")
        john_id = john.id
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert john.name == "John"
        assert john.password_matches("Setec astronomy")
        assert not john.password_matches("setec astronomy")
        assert not john.password_matches("too many secrets")
        assert '"John"' in repr(john)
        john.set_password("setec astronomy")

        jane = db.find_user("jane.doe@apple.com")
        jane_id = jane.id
        assert jane.name == "Jane"
        assert jane.password_matches("too many secrets")
        assert not jane.password_matches("Setec astronomy")
        assert not jane.password_matches("too many Secrets")
        assert '"Jane"' in repr(jane)

        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        db.flush()
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.get_user(john_id)
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert john.name == "John"
        assert john.password_matches("setec astronomy")
        assert not john.password_matches("Setec astronomy")

        jane = db.get_user(jane_id)
        assert jane.name == "Jane"
        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        db.flush()
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        users = db.get_users()
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert len(users) == 2
        user_names = [u.name for u in users]
        assert 'John' in user_names
        assert 'Jane' in user_names


if __name__ == "__main__":
    test_user()
