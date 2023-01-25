#!/usr/bin/env python3

""" The model of the data
"""

import enum
import hashlib
import datetime

import yaml

import financial_game.database


TABLES = {
    "user": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50) NOT NULL",
        "email": "VARCHAR(50) UNIQUE NOT NULL",
        "password_hash": "VARCHAR(64) NOT NULL",
        "sponsor_id": "INTEGER",
    },
    "bank": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50) UNIQUE NOT NULL",
        "type": "VARCHAR(4) NOT NULL",  # TypeOfBank
        "url": "VARCHAR(2083)",
    },
    "account_type": {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(50) NOT NULL",
        "type": "VARCHAR(4) NOT NULL",  # TypeOfAccount
        "url": "VARCHAR(2083)",
        "bank_id": "INTEGER NOT NULL",
    },
    "account": {
        "id": "INTEGER PRIMARY KEY",
        "label": "VARCHAR(50) NOT NULL",
        "hint": "VARCHAR(128)",
        "purpose": "VARCHAR(4)",  # AccountPurpose
        "account_type_id": "INTEGER NOT NULL",
        "user_id": "INTEGER NOT NULL",
    },
    "account_statement": {
        "id": "INTEGER PRIMARY KEY",
        "start_date": "TEXT NOT NULL",  # YYYY-MM-DD HH:MM:SS.SSS
        "end_date": "TEXT NOT NULL",  # YYYY-MM-DD HH:MM:SS.SSS
        "start_value": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "end_value": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "withdrawals": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "deposits": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "interest": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "fees": "INTEGER NOT NULL",  # in cents (x 100 = $)
        "rate": "INTEGER NOT NULL",  # 1 = 0.01%, 100 = 1% 1000 = 10%
        "mileage": "INTEGER",  # used for vehicles
    },
    "related_account": {
        "account_id": "INTEGER",
        "related_account_id": "INTEGER",
    },
}


class TypeOfBank(enum.Enum):
    """Types of bank objects"""

    BANK = 1  # bank


class TypeOfAccount(enum.Enum):
    """Types of account_type objects"""

    CRED = 1  # Credit Card
    CHCK = 2  # Checking
    SAVE = 3  # Savings
    MONM = 4  # Money Market
    BROK = 5  # Brokrage account


class AccountPurpose(enum.Enum):
    """Purposes for account objects"""

    MRGC = 1  # Emergency Fund
    SINK = 2  # Targeted / Sinking Fund
    NYOU = 3  # self development / invest in you
    BUDG = 4  # active budget funds
    RTIR = 5  # retirement account
    NVST = 6  # taxable investment


class UserApi:
    """User API"""

    def __init__(self, database):
        self.__db = database

    # pylint: disable=too-many-arguments
    def create(
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

    def get(self, user_id: int):
        """Get a user by its id"""
        return self.__db.get_one_or_none(
            "user", _where_="id = :user_id", user_id=user_id
        )

    def find(self, email: str):
        """Get a user by email (case insensitive)"""
        return self.__db.get_one_or_none(
            "user", _where_="email LIKE :email", email=email
        )

    def get_users(self):
        """Get list of all users"""
        return self.__db.get_all("user")

    def get_sponsored(self, user_id: int):
        """Get the people this person has sponsored"""
        return self.__db.get_all(
            "user", _where_="sponsor_id = :user_id", user_id=user_id
        )

    def count(self):
        """Count total users"""
        return self.__db.get_one_or_none("user", "COUNT(*)", _as_object_=False)[
            "COUNT(*)"
        ]

    def change_info(self, user_id: int, **_to_update_):
        """Change information about the user"""
        assert "id" not in _to_update_
        # TODO: If password in _to_update_ then -> password_hash  # pylint: disable=fixme
        self.__db.change(
            "user", "user_id", _where_="id = :user_id", user_id=user_id, **_to_update_
        )


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
        assert self.user().count() == 0, "database already exists, cannot deserialize"
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
            created[user["email"]] = self.user().create(
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
        users = self.user().get_users()
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

    def user(self):
        """Return the user API"""
        return UserApi(self.__db)

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

    # Mark: Account API

    @staticmethod
    def __patch_account(account):
        if account is None:
            return None

        if isinstance(account, list):
            return [Database.__patch_account(a) for a in account]

        account.purpose = (
            None if account.purpose is None else AccountPurpose[account.purpose]
        )
        return account

    # pylint: disable=too-many-arguments
    def create_account(
        self,
        user_id: int,
        account_type_id: int,
        label: str,
        hint: str = None,
        purpose: AccountPurpose = None,
    ):
        """Create a bank account"""
        assert user_id is not None
        assert account_type_id is not None
        assert label is not None
        return Database.__patch_account(
            self.__db.insert(
                "account",
                label=label,
                hint=hint,
                purpose=None if purpose is None else purpose.name,
                account_type_id=account_type_id,
                user_id=user_id,
            )
        )

    def change_account(self, account_id: int, **_to_update_):
        """Change information about the account"""
        assert "id" not in _to_update_
        assert "user_id" not in _to_update_
        # TODO: patch up purpose  # pylint: disable=fixme
        self.__db.change(
            "account",
            "account_id",
            _where_="id = :account_id",
            account_id=account_id,
            **_to_update_,
        )

    def get_account(self, account_id: int):
        """Get a account by its id"""
        return Database.__patch_account_type(
            self.__db.get_one_or_none(
                "account", _where_="id = :account_id", account_id=account_id
            )
        )

    # Mark: AccountStatement API

    @staticmethod
    def __parse_date(date: str) -> datetime.date:
        return datetime.datetime.strptime(date, "%Y-%m-%d").date()

    @staticmethod
    def __patch_account_statement(account_statement):
        if account_statement is None:
            return None

        if isinstance(account_statement, list):
            return [Database.__patch_account_statement(a) for a in account_statement]

        account_statement.start_date = (
            None
            if account_statement.start_date is None
            else Database.__parse_date(account_statement.start_date)
        )
        account_statement.end_date = (
            None
            if account_statement.end_date is None
            else Database.__parse_date(account_statement.end_date)
        )
        account_statement.start_value = account_statement.start_value / 100.0
        account_statement.end_value = account_statement.end_value / 100.0
        account_statement.withdrawals = account_statement.withdrawals / 100.0
        account_statement.deposits = account_statement.deposits / 100.0
        account_statement.interest = account_statement.interest / 100.0
        account_statement.rate = account_statement.rate / 100.0
        return account_statement

    # pylint: disable=too-many-arguments
    def create_account_statement(
        self,
        account_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        start_value: float,
        end_value: float,
        withdrawals: float,
        deposits: float,
        interest: float,
        rate: float,
        mileage: int = None,
    ):
        """Create a bank account"""
        assert account_id is not None
        assert start_date is not None
        assert end_date is not None
        assert start_value is not None
        assert end_value is not None
        assert withdrawals is not None
        assert deposits is not None
        assert interest is not None
        assert rate is not None
        return Database.__patch_account_statement(
            self.__db.insert(
                "account_statement",
                account_id=account_id,
                start_date=start_date.strftime("%Y-%m-%d %H:%M:%S.0"),
                end_date=end_date.strftime("%Y-%m-%d %H:%M:%S.0"),
                start_value=int(start_value * 100),
                end_value=int(end_value * 100),
                withdrawals=int(withdrawals * 100),
                deposits=int(deposits * 100),
                interest=int(interest * 100),
                rate=int(rate * 100),
                mileage=mileage,
            )
        )

    def get_account_statements(self, account_id: int):
        """Get statements for a given account"""
        return Database.__patch_account_statement(
            self.__db.get_all(
                "account_statement",
                _where_="account_id = :account_id",
                account_id=account_id,
            )
        )

    def change_account_statement(self, account_statement_id: int, **_to_update_):
        """Change information about the account"""
        assert "id" not in _to_update_
        assert "user_id" not in _to_update_
        # TODO: patch up start_date, end_date, start_value,  # pylint: disable=fixme
        #       deposits, interest, fees, rate, withrawals, end_value
        self.__db.change(
            "account_statement",
            "account_statement_id",
            _where_="id = :account_statement_id",
            account_statement_id=account_statement_id,
            **_to_update_,
        )
