#!/usr/bin/env python3

""" Abstract the database API
"""


import sqlite3
import threading
import queue
import types


class Sqlite3:
    """Basic kernel for sqlite3 database"""

    def __init__(self, description):
        self.__db = sqlite3.connect(description)
        self.__thread = threading.current_thread().ident

    def execute(
        self,
        statement: str,
        replacements: any = None,
        fetch_all: bool = None,
        commit: bool = False,
    ) -> (int, [str], list, int):
        """Executes an sqlite3 statement
        replacements - dictionary (:name -> dict['name']) or list (? -> [0])
        fetch_all - None= no values to return, False = fetch one or none
        commit - tell the database to commit after executing
        """
        assert (
            self.__thread == threading.current_thread().ident
        ), f"Thread mismatch {self.__thread} bs {threading.current_thread().ident}"
        cursor = self.__db.cursor()
        cursor.execute(statement, tuple() if replacements is None else replacements)

        if commit:
            self.__db.commit()

        if fetch_all is not None:
            results = cursor.fetchall() if fetch_all else cursor.fetchone()
        else:
            results = None

        labels = (
            [] if cursor.description is None else [c[0] for c in cursor.description]
        )
        return cursor.lastrowid, labels, results, cursor.rowcount

    def close(self):
        """Close the database"""
        self.__db.close()


class Threadsafe(threading.Thread):
    """Wrapper to make a database kernel threadsafe"""

    def __init__(self, description, db_type):
        self.__description = description
        self.__type = db_type
        self.__messages = queue.Queue()
        threading.Thread.__init__(self, daemon=True)
        self.start()

    def run(self):
        """handle the messages"""
        database = self.__type(self.__description)

        while True:
            message = self.__messages.get()

            if message is None:
                break

            message[1].put(database.execute(**message[0]))

        database.close()

    def execute(
        self,
        statement: str,
        replacements: tuple = None,
        fetch_all: bool = None,
        commit: bool = False,
    ) -> (int, [str], list):
        """Pass an sqlite3 statement to the execution thread
        replacements - dictionary (:name -> dict['name']) or list (? -> [0])
        fetch_all - None= no values to return, False = fetch one or none
        commit - tell the database to commit after executing
        """
        response = queue.Queue()
        self.__messages.put(
            (
                {
                    "statement": statement,
                    "replacements": replacements,
                    "fetch_all": fetch_all,
                    "commit": commit,
                },
                response,
            )
        )
        return response.get()

    def close(self):
        """pass the close message to the execution thread and wait for completion"""
        self.__messages.put(None)
        self.join()


class Connection:
    def __init__(self, database):
        self.__db = database

    @staticmethod
    def __convert(description: [str], row: list, as_object: bool):
        if row is None:
            return None

        data = dict(zip(description, row))
        return types.SimpleNamespace(**data) if as_object else data

    def execute(
        self, sql_command: str, replacements: any, commit: bool = True
    ) -> (int, [str], list, int):
        return self.__db.execute(sql_command, replacements, commit=commit)

    def fetch_one_or_none(self, sql_command: str, **replacements) -> any:
        as_object = replacements.get("as_object", True)
        results = self.__db.execute(sql_command, replacements, fetch_all=False)
        return Connection.__convert(results[1], results[2], as_object)

    def fetch_all(self, sql_command: str, **replacements) -> [any]:
        as_objects = replacements.get("as_objects", True)
        results = self.__db.execute(sql_command, replacements, fetch_all=True)
        return [Connection.__convert(results[1], r, as_objects) for r in results[2]]

    def create_table(self, _table_name_: str, **description):
        if_not_exists = description.get("if_not_exists", True)
        description_string = ", ".join(f'"{n}" {v}' for n, v in description.items())
        exists_string = " IF NOT EXISTS" if if_not_exists else ""
        self.execute(
            f"""CREATE TABLE{exists_string} "{_table_name_}" ({description_string});""",
            {},
            commit=False,
        )

    def insert(self, _table_name_: str, **data) -> any:
        as_object = data.get("as_object", True)
        commit = data.get("commit", True)
        row_name = data.get("row_name", "id")
        columns = sorted(data)
        placeholders = ", ".join("?" for _ in range(0, len(data)))
        replacements = [data[c] for c in columns]
        column_string = ", ".join(f'"{c}"' for c in columns)
        results = self.execute(
            f"""INSERT INTO {_table_name_} ({column_string}) VALUES({placeholders});""",
            replacements,
            commit=commit,
        )
        assert results[3] > 0, "No rows were inserted {results}"

        if row_name is not None:
            data = dict(data)
            data[row_name] = results[0]

        return types.SimpleNamespace(**data) if as_object else data

    def get_one_or_none(self, _table_name_: str, *columns, **replacements) -> any:
        as_object = replacements.get("as_object", True)
        where = replacements.get("where", None)
        column_string = (
            "*" if len(columns) == 0 else ", ".join(f'"{c}"' for c in columns)
        )
        where_string = "" if where is None else f" WHERE {where}"
        return self.fetch_one_or_none(
            f"""SELECT {column_string} FROM {_table_name_}{where_string};""",
            **replacements,
            as_object=as_object,
        )

    def get_all(self, _table_name_: str, *columns, **replacements) -> [any]:
        as_objects = replacements.get("as_objects", True)
        where = replacements.get("where", None)
        column_string = (
            "*" if len(columns) == 0 else ", ".join(f'"{c}"' for c in columns)
        )
        where_string = "" if where is None else f" WHERE {where}"
        return self.fetch_all(
            f"""SELECT {column_string} FROM {_table_name_}{where_string};""",
            **replacements,
            as_objects=as_objects,
        )
        # group_by:list=None, order_clause=None
        # order_ascending=True, limit=None, offset=None

    def delete(self, _table_name_: str, where: str, **replacements) -> int:
        commit = replacements.get("commit", True)
        results = self.execute(
            f"""DELETE FROM {_table_name_} WHERE {where}""", replacements, commit=commit
        )
        return results[3]

    def close(self):
        self.__db.close()
