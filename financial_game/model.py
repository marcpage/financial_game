#!/usr/bin/env python3

""" The model of the data
"""


import datetime

import yaml

import financial_game.database
from financial_game.table import Table
from financial_game.model_user import User, Account, Statement, AccountPurpose
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

    def __deserialize_statements(self, accounts_created):
        for serailized_account, created_account in accounts_created:
            for statement_id in sorted(serailized_account.get("statements", [])):
                statement = serailized_account["statements"][statement_id]
                assert statement["start_date"] is not None
                assert statement["end_date"] is not None
                assert statement["start_value"] is not None
                assert statement["end_value"] is not None
                assert statement["withdrawals"] is not None
                assert statement["deposits"] is not None
                assert statement["interest"] is not None
                assert statement["fees"] is not None
                assert statement["rate"] is not None
                Statement.create(
                    created_account,
                    datetime.datetime.strptime(
                        statement["start_date"], "%Y-%m-%d"
                    ).date(),
                    datetime.datetime.strptime(
                        statement["end_date"], "%Y-%m-%d"
                    ).date(),
                    statement["start_value"],
                    statement["end_value"],
                    statement["withdrawals"],
                    statement["deposits"],
                    statement["fees"],
                    statement["interest"],
                    statement["rate"],
                    statement["mileage"],
                )

    def __deserialize_users(self, serialized, account_type_mappings):
        assert "users" in serialized
        assert User.total() == 0, "database already exists, cannot deserialize"
        users = serialized["users"]
        users_created = {}
        accounts_created = []

        for user_id in sorted(users):
            user = users[user_id]
            sponsor_id = user.get("sponsor_id", None)
            assert (
                sponsor_id is None or sponsor_id in users
            ), f"invalid sponsor_id: {sponsor_id}"
            sponsor_email = None if sponsor_id is None else users[sponsor_id]["email"]
            assert (
                sponsor_email is None or sponsor_email in users_created
            ), f"We haven't created {sponsor_email} yet"
            sponsor_id = (
                None if sponsor_email is None else users_created[sponsor_email].id
            )
            users_created[user["email"]] = User.create(
                user["email"],
                user.get("password_hash", user.get("password", None)),
                user["name"],
                sponsor_id,
                pw_hashed="password_hash" in user,
            )

        for user_id in sorted(users):
            for account_id in sorted(users[user_id].get("accounts", [])):
                account = users[user_id]["accounts"][account_id]
                assert account["label"] is not None
                assert account["account_type"] in account_type_mappings
                user = users_created[users[user_id]["email"]]
                account_type = account_type_mappings[account["account_type"]]
                created = Account.create(
                    user,
                    account_type,
                    account["label"],
                    account.get("hint", None),
                    None
                    if account["purpose"] is None
                    else AccountPurpose[account["purpose"]],
                )
                accounts_created.append((account, created))

        self.__deserialize_statements(accounts_created)

    def __deserialize_banks(self, serialized):
        assert "banks" in serialized
        assert Bank.total() == 0, "database already exists, cannot deserialize"
        account_type_mappings = {}

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
                created = AccountType.create(
                    new_bank.id,
                    type_info["name"],
                    TypeOfAccount[type_info["type"]],
                    url=type_info.get("url", None),
                )
                account_type_mappings[type_id] = created.id

        return account_type_mappings

    def __deserialize(self, serialized):
        assert len(serialized) == 2
        account_type_mappings = self.__deserialize_banks(serialized)
        self.__deserialize_users(serialized, account_type_mappings)

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
                    "accounts": {
                        a.id: {
                            "label": a.label,
                            "hint": a.hint,
                            "purpose": None if a.purpose is None else a.purpose.name,
                            "account_type": a.account_type_id,
                            "statements": {
                                s.id: {
                                    "start_date": s.start_date.strftime("%Y-%m-%d"),
                                    "end_date": s.end_date.strftime("%Y-%m-%d"),
                                    "start_value": s.start_value,
                                    "end_value": s.end_value,
                                    "withdrawals": s.withdrawals,
                                    "deposits": s.deposits,
                                    "interest": s.interest,
                                    "fees": s.fees,
                                    "rate": s.rate,
                                    "mileage": s.mileage,
                                }
                                for s in a.statements()
                            },
                        }
                        for a in u.accounts()
                    },
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
