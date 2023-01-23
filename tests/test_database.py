#!/usr/bin/env python3


import tempfile
import os

import financial_game.database
from financial_game.database import Sqlite3,Threadsafe


def test_Sqlite3():
    with tempfile.TemporaryDirectory() as workspace:
        db_path = os.path.join(workspace, "test.sqlite3")
        db = financial_game.database.Connection(Sqlite3(db_path))
        db.create_table("user",
            id="INTEGER PRIMARY KEY",
            name="VARCHAR(50)",
            email="VARCHAR(50)",
            password_hash="VARCHAR(64)",
            sponsor_id="INTEGER")

        john = db.insert('user',
            name="John",
            email="john.appleseed@apple.com",
            password_hash="3bce676cf7e5489dd539b077eb38888a1c9d42b23f88bc5c1f2af863f14ab23c",
            sponsor_id=None)
        assert john.id is not None
        assert john.name == "John"
        assert john.email == "john.appleseed@apple.com"
        assert john.password_hash == "3bce676cf7e5489dd539b077eb38888a1c9d42b23f88bc5c1f2af863f14ab23c"
        assert john.sponsor_id == None

        jane = db.insert('user',
            name="Jane",
            email="Jane.Doe@apple.com",
            password_hash="624fa374a759deff04da9e9d99b7e7f9937d9410401c421c38ca78973b98293a",
            sponsor_id=john.id)
        assert jane.id is not None
        assert jane.name == "Jane"
        assert jane.email == "Jane.Doe@apple.com"
        assert jane.password_hash == "624fa374a759deff04da9e9d99b7e7f9937d9410401c421c38ca78973b98293a"
        assert jane.sponsor_id == john.id

        everything = db.get_all('user')
        assert len(everything) == 2, everything

        db.close()

        db = financial_game.database.Connection(Sqlite3(db_path))
        db.create_table("user",
            id="INTEGER PRIMARY KEY",
            name="VARCHAR(50)",
            email="VARCHAR(50)",
            password_hash="VARCHAR(64)",
            sponsor_id="INTEGER")

        everything = db.get_all('user')
        assert len(everything) == 2, everything
        john = db.get_one_or_none('user', email="John.Appleseed@Apple.com", where="email LIKE :email")
        assert john.id is not None
        assert john.name == "John"
        assert john.email == "john.appleseed@apple.com"
        assert john.password_hash == "3bce676cf7e5489dd539b077eb38888a1c9d42b23f88bc5c1f2af863f14ab23c"
        assert john.sponsor_id == None

        jane = db.get_one_or_none('user', email="jane.doe@apple.com", where="email LIKE :email")
        assert jane.id is not None
        assert jane.name == "Jane"
        assert jane.email == "Jane.Doe@apple.com"
        assert jane.password_hash == "624fa374a759deff04da9e9d99b7e7f9937d9410401c421c38ca78973b98293a"
        assert jane.sponsor_id == john.id

        db.delete('user', 'id = :id', id=jane.id)
        no_jane = db.get_one_or_none('user', email="jane.doe@apple.com", where="email LIKE :email")
        assert no_jane is None, no_jane


if __name__ == "__main__":
    test_Sqlite3()
