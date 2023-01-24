#!/usr/bin/env python3

""" The model of the data
"""

import enum
import hashlib

import yaml

import financial_game.database


TABLES = {
    "user": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50)",
        "email": "VARCHAR(50) UNIQUE",
        "password_hash": "VARCHAR(64)",
        "sponsor_id": "INTEGER",
    },
    "bank": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50) UNIQUE",
        "type": "VARCHAR(4)",  # TypeOfBank
        "url": "VARCHAR(2083)",
    },
    "account_type": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50)",
        "type": "VARCHAR(4)",  # TypeOfAccount
        "url": "VARCHAR(2083)",
        "bank_id": "INTEGER",
    },
}


class TypeOfBank(enum.Enum):
    """Types of Bank objects"""

    BANK = 1  # bank


class TypeOfAccount(enum.Enum):
    """Types of AccountType objects"""

    CRED = 1  # Credit Card
    CHCK = 2  # Checking
    SAVE = 3  # Savings
    MONM = 4  # Money Market
    BROK = 5  # Brokrage account


class Database:
    """stored information"""

    @staticmethod
    def hash_password(text):
        """hash utf-8 text"""
        hasher = hashlib.new("sha256")
        hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()

    @staticmethod
    def password_matches(user, password):
        """Verify that the user's password matches the given password"""
        return Database.hash_password(password) == user.password_hash

    def __init__(self, db_url, serialized=None):
        """create db
        db_url - a SqlAlchemy URL for the database
        serialized - optional dictionary or path to yaml file
        """
        self.__db = financial_game.database.Connection.connect(db_url)
        self.__db.create_tables(**TABLES)

        if serialized is not None:
            try:
                with open(serialized, "r", encoding="utf-8") as script_file:
                    serialized_data = yaml.safe_load(script_file.read())

            except TypeError:
                serialized_data = serialized

            self.__deserialize(serialized_data)

    def __deserialize_users(self, serialized):
        assert "users" in serialized
        assert self.count_users() == 0, "database already exists, cannot deserialize"
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
            created[user["email"]] = self.create_user(
                user["email"],
                user.get("password_hash", user.get("password", None)),
                user["name"],
                sponsor_id,
                password_is_hashed="password_hash" in user,
            )

    def __deserialize_banks(self, serialized):
        assert "banks" in serialized
        assert self.count_banks() == 0, "database already exists, cannot deserialize"

        for bank_id in serialized["banks"]:
            bank = serialized["banks"][bank_id]
            assert bank["type"] is not None
            assert bank["type"] in dir(TypeOfBank)
            assert bank["name"] is not None
            new_bank = self.create_bank(
                bank["name"], bank.get("url", None), TypeOfBank[bank["type"]]
            )
            assert new_bank.id is not None
            for type_id in bank.get("account_types", []):
                type_info = bank["account_types"][type_id]
                assert type_info["name"] is not None
                assert type_info["type"] is not None
                assert type_info["type"] in dir(TypeOfAccount)
                self.create_account_type(
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
        users = self.get_users()
        banks = self.get_banks()
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
                        for t in self.get_bank_account_types(b.id)
                    },
                }
                for b in banks
            },
        }

    # Mark: User API

    # pylint: disable=too-many-arguments
    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        sponsor_id: int,
        password_is_hashed=False,
    ):
        """create a new employee entry"""
        assert password is not None
        return self.__db.insert(
            "user",
            email=email,
            password_hash=password
            if password_is_hashed
            else Database.hash_password(password),
            name=name,
            sponsor_id=sponsor_id,
        )

    def get_user(self, user_id: int):
        """Get a user by its id"""
        return self.__db.get_one_or_none(
            "user", _where_="id = :user_id", user_id=user_id
        )

    def find_user(self, email: str):
        """Get a user by email (case insensitive)"""
        return self.__db.get_one_or_none(
            "user", _where_="email LIKE :email", email=email
        )

    def get_users(self):
        """Get list of all users"""
        return self.__db.get_all("user")

    def get_user_sponsored(self, user_id: int):
        """Get the people this person has sponsored"""
        return self.__db.get_all(
            "user", _where_="sponsor_id = :user_id", user_id=user_id
        )

    def count_users(self):
        """Count total users"""
        return self.__db.get_one_or_none("user", "COUNT(*)", _as_object_=False)[
            "COUNT(*)"
        ]

    def change_user_info(self, user_id: int, **_to_update_):
        """Change information about the user"""
        self.__db.change(
            "user", "user_id", _where_="id = :user_id", user_id=user_id, **_to_update_
        )

    # Mark: Bank API

    @staticmethod
    def __patch_bank(bank):
        if bank is None:
            return None

        if isinstance(bank, list):
            return [Database.__patch_bank(b) for b in bank]

        bank.type = TypeOfBank[bank.type]
        return bank

    def create_bank(
        self, name: str, url: str = None, bank_type: TypeOfBank = TypeOfBank.BANK
    ):
        """Create a new bank"""
        assert name is not None
        return Database.__patch_bank(
            self.__db.insert("bank", name=name, url=url, type=bank_type.name)
        )

    def get_bank(self, bank_id: int):
        """Get a bank by its id"""
        return Database.__patch_bank(
            self.__db.get_one_or_none("bank", _where_="id = :bank_id", bank_id=bank_id)
        )

    def get_banks(self, bank_type: TypeOfBank = TypeOfBank.BANK):
        """Get all the banks of a given type"""
        return Database.__patch_bank(
            self.__db.get_all(
                "bank", _where_="type = :bank_type", bank_type=bank_type.name
            )
        )

    def count_banks(self):
        """Count total banks"""
        return self.__db.get_one_or_none("bank", "COUNT(*)", _as_object_=False)[
            "COUNT(*)"
        ]

    def get_bank_account_types(self, bank_id: int):
        """Get the types of accounts associated with a bank"""
        return Database.__patch_account_type(
            self.__db.get_all(
                "account_type", _where_="bank_id = :bank_id", bank_id=bank_id
            )
        )

    # Mark: AccountType API

    @staticmethod
    def __patch_account_type(account_type):
        if account_type is None:
            return None

        if isinstance(account_type, list):
            return [Database.__patch_account_type(a) for a in account_type]

        account_type.type = TypeOfAccount[account_type.type]
        return account_type

    def create_account_type(
        self, bank_id: int, name: str, account_type: TypeOfAccount, url: str = None
    ):
        """Create a bank account type"""
        assert name is not None
        return Database.__patch_account_type(
            self.__db.insert(
                "account_type",
                name=name,
                url=url,
                bank_id=bank_id,
                type=account_type.name,
            )
        )

    def get_account_type(self, account_type_id: int):
        """Get a account type by its id"""
        return Database.__patch_account_type(
            self.__db.get_one_or_none(
                "account_type",
                _where_="id = :account_type_id",
                account_type_id=account_type_id,
            )
        )
