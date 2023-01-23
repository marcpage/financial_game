#!/usr/bin/env python3


import tempfile
import os
import threading
import queue

import financial_game.database
from financial_game.database import Sqlite3,Threadsafe

RECORDS_TO_CREATE = 1000
THREADS_TO_TEST = 50

def add_items(db, table, in_queue, out_queue):
    while True:
        try:
            work = in_queue.get(timeout=0.100)
            db.insert(table, **work)

        except queue.Empty:
            break

    out_queue.put(db.get_all(table))


def test_Threadsafe():
    with tempfile.TemporaryDirectory() as workspace:
        db_path = os.path.join(workspace, "test.sqlite3")
        db = financial_game.database.Connection(Threadsafe(db_path, Sqlite3))
        db.create_table("user",
            id="INTEGER PRIMARY KEY",
            name="VARCHAR(50)",
            email="VARCHAR(50)",
            password_hash="VARCHAR(64)",
            sponsor_id="INTEGER")
        user_queue = queue.Queue()
        users_queue = queue.Queue()
        threads = [threading.Thread(target=add_items,
                                    args=(db, 'user', user_queue, users_queue),
                                    daemon=True)
                    for _ in range(0, THREADS_TO_TEST)]

        for thread in threads:
            thread.start()

        for i in range(0, RECORDS_TO_CREATE):
            user_queue.put({
                'name': f"user #{i}",
                'email': f"user{i}@company.org",
                'password_hash': "3bce676cf7e5489dd539b077eb38888a1c9d42b23f88bc5c1f2af863f14ab23c"})

        for thread in threads:
            thread.join()

        iterations = 0

        while True:
            try:
                results = users_queue.get(timeout=0.100)
                assert len(results) == RECORDS_TO_CREATE
                assert len(set(u.email for u in results)) == RECORDS_TO_CREATE
                iterations += 1

            except queue.Empty:
                break

        assert iterations == THREADS_TO_TEST
        db.close()


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
    test_Threadsafe()
