#!/usr/bin/env python3

""" The model of the data
"""

import yaml

import financial_game.database
from financial_game.table import Table
from financial_game.model_user import User, Account, Statement
from financial_game.model_bank import Bank, TypeOfBank, AccountType, TypeOfAccount


class Database:
    """stored information"""

    tables = [User, Bank, AccountType, Account, Statement]

    def __init__(self, db_url, serialized=None):
        """create db
        db_url - a SqlAlchemy URL for the database
        serialized - optional dictionary or path to yaml file
        """
        self.__db = financial_game.database.Connection.connect(
            db_url, default_return_objects=False
        )
        description = Table.database_description(*Database.tables)
        self.__db.create_tables(**description)

        for table in Database.tables:
            table._db = self.__db

        if serialized is not None:
            try:
                with open(serialized, "r", encoding="utf-8") as script_file:
                    serialized_data = yaml.safe_load(script_file.read())

            except TypeError:
                serialized_data = serialized

            self.__deserialize(serialized_data)

    def __deserialize_users(self, serialized):
        assert "users" in serialized
        assert User.total() == 0, "database already exists, cannot deserialize"
        users = serialized["users"]
        created = {}

        for user_id in sorted(users):
            user = users[user_id]
            sponsor_id = user.get("sponsor_id", None)
            assert (
                sponsor_id is None or sponsor_id in users
            ), f"invalid sponsor_id: {sponsor_id}"
            sponsor_email = None if sponsor_id is None else users[sponsor_id]["email"]
            assert (
                sponsor_email is None or sponsor_email in created
            ), f"We haven't created {sponsor_email} yet"
            sponsor_id = None if sponsor_email is None else created[sponsor_email].id
            created[user["email"]] = User.create(
                user["email"],
                user.get("password_hash", user.get("password", None)),
                user["name"],
                sponsor_id,
                pw_hashed="password_hash" in user,
            )

    def __deserialize_banks(self, serialized):
        assert "banks" in serialized
        assert Bank.total() == 0, "database already exists, cannot deserialize"

        for bank_id in serialized["banks"]:
            bank = serialized["banks"][bank_id]
            assert bank["type"] is not None
            assert bank["type"] in dir(TypeOfBank)
            assert bank["name"] is not None
            new_bank = Bank.create(
                bank["name"], bank.get("url", None), TypeOfBank[bank["type"]]
            )
            assert new_bank.id is not None
            for type_id in bank.get("account_types", []):
                type_info = bank["account_types"][type_id]
                assert type_info["name"] is not None
                assert type_info["type"] is not None
                assert type_info["type"] in dir(TypeOfAccount)
                AccountType.create(
                    new_bank.id,
                    type_info["name"],
                    TypeOfAccount[type_info["type"]],
                    url=type_info.get("url", None),
                )

    def __deserialize(self, serialized):
        assert len(serialized) == 2
        self.__deserialize_users(serialized)
        self.__deserialize_banks(serialized)

    def close(self):
        """close down the connection to the database"""
        self.__db.close()

    def serialize(self):
        """Converts the database contents to a dictionary that can be deserialized"""
        users = User.every()
        banks = Bank.every()
        return {
            "users": {
                u.id: {
                    "name": u.name,
                    "email": u.email,
                    "password_hash": u.password_hash,
                    "sponsor_id": u.sponsor_id,
                }
                for u in users
            },
            "banks": {
                b.id: {
                    "name": b.name,
                    "url": b.url,
                    "type": b.type.name,
                    "account_types": {
                        t.id: {
                            "name": t.name,
                            "type": t.type.name,
                            "url": t.url,
                        }
                        for t in b.account_types()
                    },
                }
                for b in banks
            },
        }
