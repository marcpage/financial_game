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
    """A database connection"""

    def __init__(self, database):
        """Create the connection
        database - an instance of Sqlite3 or equivalent
        """
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
        """execute SQL command w/ the given replacements and optionally committing"""
        return self.__db.execute(sql_command, replacements, commit=commit)

    def fetch_one_or_none(self, _sql_command_: str, **_replacements_) -> any:
        """Return the first match or None if no matches
        _as_object_ - (True) If True return objects, False return dictionaries
        """
        as_object = _replacements_.get("_as_object_", True)
        results = self.__db.execute(_sql_command_, _replacements_, fetch_all=False)
        return Connection.__convert(results[1], results[2], as_object)

    def fetch_all(self, _sql_command_: str, **_replacements_) -> [any]:
        """Return all results from the query
        _as_object_ - (True) If True return objects, False return dictionaries
        """
        as_objects = _replacements_.get("_as_object_", True)
        results = self.__db.execute(_sql_command_, _replacements_, fetch_all=True)
        return [Connection.__convert(results[1], r, as_objects) for r in results[2]]

    def create_table(self, _table_name_: str, **_description_):
        """Create a table
        _table_name_ - the name of the table to create
        _description_ - pass in name of column mapped to SQL description
        _if_not_exists_ - (True) If True add the "IF NOT EXISTS" clause
        """
        if_not_exists = _description_.get("_if_not_exists_", True)
        description_string = ", ".join(f'"{n}" {v}' for n, v in _description_.items())
        exists_string = " IF NOT EXISTS" if if_not_exists else ""
        self.execute(
            f"""CREATE TABLE{exists_string} "{_table_name_}" ({description_string});""",
            {},
            commit=False,
        )

    def insert(self, _table_name_: str, **_data_) -> any:
        """Insert a new row in the table
        _table_name_ - the table to insert data into
        _data_ - map of column name to data to put in the table
        _as_object_ - (True) If True return an object, False return a dictionary
        """
        as_object = _data_.get("_as_object_", True)
        commit = _data_.get("commit", True)
        row_name = _data_.get("row_name", "id")
        columns = sorted(_data_)
        placeholders = ", ".join("?" for _ in range(0, len(_data_)))
        replacements = [_data_[c] for c in columns]
        column_string = ", ".join(f'"{c}"' for c in columns)
        results = self.execute(
            f"""INSERT INTO {_table_name_} ({column_string}) VALUES({placeholders});""",
            replacements,
            commit=commit,
        )
        assert results[3] > 0, "No rows were inserted {results}"

        if row_name is not None:
            _data_ = dict(_data_)
            _data_[row_name] = results[0]

        return types.SimpleNamespace(**_data_) if as_object else _data_

    def get_one_or_none(self, _table_name_: str, *_columns_, **_replacements_) -> any:
        """Get the first result or None if there are no results
        _table_name_ - The table to query
        _columns_ - list the names of any columns you want returned or none for all columns
        _replacements_ - :name in where will be replaced with name=value
        _as_object_ - (True) If True return an object, False return a dictionary
        """
        as_object = _replacements_.get("_as_object_", True)
        where = _replacements_.get("where", None)
        column_string = (
            "*" if len(_columns_) == 0 else ", ".join(f'"{c}"' for c in _columns_)
        )
        where_string = "" if where is None else f" WHERE {where}"
        return self.fetch_one_or_none(
            f"""SELECT {column_string} FROM {_table_name_}{where_string};""",
            **_replacements_,
            as_object=as_object,
        )

    def get_all(self, _table_name_: str, *_columns_, **_replacements_) -> [any]:
        """Get all the results that match
        _table_name_ - The table to query
        _columns_ - list the names of any columns you want returned or none for all columns
        _replacements_ - :name in where will be replaced with name=value
        _as_objects_ - (True) If True return objects, False return dictionaries
        """
        as_objects = _replacements_.get("_as_objects_", True)
        where = _replacements_.get("where", None)
        column_string = (
            "*" if len(_columns_) == 0 else ", ".join(f'"{c}"' for c in _columns_)
        )
        where_string = "" if where is None else f" WHERE {where}"
        return self.fetch_all(
            f"""SELECT {column_string} FROM {_table_name_}{where_string};""",
            **_replacements_,
            as_objects=as_objects,
        )
        # group_by:list=None, order_clause=None
        # order_ascending=True, limit=None, offset=None

    def delete(self, _table_name_: str, _where_: str, **_replacements_) -> int:
        """delete a row from the table
        _table_name_ - the table to delete the row from
        _where_ - The where clause
        _replacements_ - :name in where will be replaced with name=value
        """
        commit = _replacements_.get("commit", True)
        results = self.execute(
            f"""DELETE FROM {_table_name_} WHERE {_where_}""",
            _replacements_,
            commit=commit,
        )
        return results[3]

    def close(self):
        """Close out the database"""
        self.__db.close()
