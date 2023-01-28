#!/usr/bin/env python3

""" The model of the data
"""

import enum
import hashlib
import datetime

import yaml

import financial_game.database
from financial_game.table import Identifier, String, Integer, Fixed, Enum
from financial_game.table import Date, Table, Money, ForeignKey


class InterestRate(Fixed):
    """interest rate"""

    def __init__(self, precision: int = 2, allow_null: bool = True):
        super().__init__(precision, allow_null)


class User(Table):
    """User info"""

    _db = None
    id = Identifier()
    name = String(50, allow_null=False)
    email = String(50, allow_null=False)
    password_hash = String(64, allow_null=False)
    sponsor_id = ForeignKey("User")

    @staticmethod
    def hash_password(text):
        """hash utf-8 text"""
        hasher = hashlib.new("sha256")
        hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()

    @staticmethod
    def create(email: str, password: str, name: str, sponsor=None, pw_hashed=False):
        """create a new user entry"""
        assert password is not None
        assert isinstance(sponsor, (int, User)) or sponsor is None
        user = User(
            email=email,
            password_hash=password if pw_hashed else User.hash_password(password),
            name=name,
            sponsor_id=sponsor.id if isinstance(sponsor, User) else sponsor,
            _normalize_=False,
        ).denormalize()
        created = User._db.insert(Table.name(User), **user)
        return User(**created)

    @staticmethod
    def fetch(user_id: int):
        """Get a user by its id"""
        found = User._db.get_one_or_none(
            Table.name(User),
            _where_="id = :user_id",
            user_id=user_id,
        )
        return None if found is None else User(**found)

    @staticmethod
    def lookup(email: str):
        """Get a user by email (case insensitive)"""
        found = User._db.get_one_or_none(
            Table.name(User), _where_="email LIKE :email", email=email
        )
        return None if found is None else User(**found)

    @staticmethod
    def every():
        """Get list of all users"""
        return [User(**u) for u in User._db.get_all(Table.name(User))]

    @staticmethod
    def total():
        """Count total users"""
        return User._db.get_one_or_none(Table.name(User), "COUNT(*)")["COUNT(*)"]

    def password_matches(self, password):
        """Verify that the user's password matches the given password"""
        return User.hash_password(password) == self.password_hash

    def sponsored(self):
        """Get the people this person has sponsored"""
        found = User._db.get_all(
            Table.name(User), _where_="sponsor_id = :user_id", user_id=self.id
        )
        return [User(**u) for u in found]

    def change(self, **_to_update_):
        """Change information about the user"""
        assert "id" not in _to_update_
        assert "password" not in _to_update_ or _to_update_["password"] is not None
        password = _to_update_.get("password", None)

        if password is not None:
            _to_update_["password_hash"] = User.hash_password(password)
            del _to_update_["password"]

        for field in _to_update_:
            _to_update_[field] = Table.denormalize_field(
                User, field, _to_update_[field]
            )

        User._db.change(
            Table.name(User),
            "user_id",
            _where_="id = :user_id",
            user_id=self.id,
            **_to_update_,
        )

        for field, value in _to_update_.items():
            self.__dict__[field] = Table.normalize_field(User, field, value)


class TypeOfBank(enum.Enum):
    """Types of bank objects"""

    BANK = 1  # bank


class Bank(Table):
    """bank info"""

    _db = None
    id = Identifier()
    name = String(50, allow_null=False)
    type = Enum(TypeOfBank, allow_null=False)
    url = String(2083)

    @staticmethod
    def create(name: str, url: str = None, bank_type=TypeOfBank.BANK):
        """Create a new bank"""
        assert name is not None
        bank = Bank(name=name, url=url, type=bank_type, _normalize_=False).denormalize()
        created = Bank._db.insert(Table.name(Bank), **bank)
        return Bank(**created)

    @staticmethod
    def fetch(bank_id: int):
        """Get a bank by its id"""
        found = Bank._db.get_one_or_none(
            Table.name(Bank), _where_="id = :bank_id", bank_id=bank_id
        )
        return None if found is None else Bank(**found)

    @staticmethod
    def every(bank_type=TypeOfBank.BANK):
        """Get list of all banks"""
        return [
            Bank(**u)
            for u in Bank._db.get_all(
                Table.name(Bank), _where_="type = :bank_type", bank_type=bank_type.name
            )
        ]

    @staticmethod
    def total(bank_type=TypeOfBank.BANK):
        """Count total banks"""
        return Bank._db.get_one_or_none(
            Table.name(Bank),
            "COUNT(*)",
            _where_="type = :bank_type",
            bank_type=bank_type.name,
        )["COUNT(*)"]

    def account_types(self):
        """get the types of accounts at the bank"""
        found = Bank._db.get_all(
            Table.name(AccountType), _where_="bank_id = :bank_id", bank_id=self.id
        )
        return [AccountType(**t) for t in found]


class TypeOfAccount(enum.Enum):
    """Types of account_type objects"""

    CRED = 1  # Credit Card
    CHCK = 2  # Checking
    SAVE = 3  # Savings
    MONM = 4  # Money Market
    BROK = 5  # Brokrage account


class AccountType(Table):
    """Bank account brand"""

    _db = None
    id = Identifier()
    name = String(50, allow_null=False)
    type = Enum(TypeOfAccount, allow_null=False)
    url = String(2083)
    bank_id = ForeignKey(Bank, allow_null=False)

    @staticmethod
    def create(bank, name: str, account_type: TypeOfAccount, url: str = None):
        """Create a new bank"""
        assert name is not None
        assert isinstance(bank, (int, Bank))
        account_type = AccountType(
            name=name,
            url=url,
            bank_id=bank.id if isinstance(bank, Bank) else bank,
            type=account_type,
            _normalize_=False,
        ).denormalize()
        created = AccountType._db.insert(Table.name(AccountType), **account_type)
        return AccountType(**created)

    @staticmethod
    def fetch(account_type_id: int):
        """Get an account type by its id"""
        found = AccountType._db.get_one_or_none(
            Table.name(AccountType),
            _where_="id = :account_type_id",
            account_type_id=account_type_id,
        )
        return None if found is None else AccountType(**found)

    def bank(self):
        """Get the bank this type is for"""
        found = AccountType._db.get_one_or_none(
            Table.name(Bank), _where_="id = :bank_id", bank_id=self.bank_id
        )
        return Bank(**found)


class AccountPurpose(enum.Enum):
    """Purposes for account objects"""

    MRGC = 1  # Emergency Fund
    SINK = 2  # Targeted / Sinking Fund
    NYOU = 3  # self development / invest in you
    BUDG = 4  # active budget funds
    RTIR = 5  # retirement account
    NVST = 6  # taxable investment


class Account(Table):
    """user's account"""

    _db = None
    id = Identifier()
    label = String(50, allow_null=False)
    hint = String(128)
    purpose = Enum(AccountPurpose)
    account_type_id = ForeignKey(AccountType, allow_null=False)
    user_id = ForeignKey(User, allow_null=False)

    @staticmethod
    def create(
        user, account_type, label: str, hint: str = None, purpose: AccountPurpose = None
    ):
        """create new account"""
        assert user is not None
        assert account_type is not None
        assert label is not None
        assert isinstance(account_type, (int, AccountType))
        assert isinstance(user, (int, User))
        account = Account(
            label=label,
            hint=hint,
            purpose=purpose,
            account_type_id=account_type.id
            if isinstance(account_type, AccountType)
            else account_type,
            user_id=user.id if isinstance(user, User) else user,
            _normalize_=False,
        ).denormalize()
        created = Account._db.insert(Table.name(Account), **account)
        return Account(**created)

    @staticmethod
    def fetch(account_id: int):
        """Get an account by its id"""
        found = Account._db.get_one_or_none(
            Table.name(Account),
            _where_="id = :account_id",
            account_id=account_id,
        )
        return None if found is None else Account(**found)

    def change(self, **_to_update_):
        """Change information about the account"""
        assert "id" not in _to_update_
        assert "user_id" not in _to_update_

        for field in _to_update_:
            _to_update_[field] = Table.denormalize_field(
                Account, field, _to_update_[field]
            )

        Account._db.change(
            Table.name(Account),
            "account_id",
            _where_="id = :account_id",
            account_id=self.id,
            **_to_update_,
        )

        for field, value in _to_update_.items():
            self.__dict__[field] = Table.normalize_field(Account, field, value)

    def account_type(self):
        """Get the account type"""
        return AccountType.fetch(self.account_type_id)

    def user(self):
        """Get the owner of the account"""
        return User.fetch(self.user_id)

    def statements(self):
        """Get the statements for the account"""
        found = Account._db.get_all(
            Table.name(Statement),
            _where_="account_id = :account_id",
            account_id=self.id,
        )
        return [Statement(**s) for s in found]


class Statement(Table):
    """bank account statement"""

    _db = None
    id = Identifier()
    account_id = ForeignKey(Account, allow_null=False)
    start_date = Date(allow_null=False)
    end_date = Date(allow_null=False)
    start_value = Money(allow_null=False)
    end_value = Money(allow_null=False)
    withdrawals = Money(allow_null=False)
    deposits = Money(allow_null=False)
    interest = Money(allow_null=False)
    fees = Money(allow_null=False)
    rate = InterestRate(allow_null=False)
    mileage = Integer()

    # pylint: disable=too-many-arguments
    @staticmethod
    def create(
        account,
        start_date: datetime.date,
        end_date: datetime.date,
        start_value: float,
        end_value: float,
        withdrawals: float,
        deposits: float,
        fees: float,
        interest: float,
        rate: float,
        mileage: int = None,
    ):
        """Create a bank account statement"""
        assert account is not None
        assert isinstance(account, (int, Account))
        assert start_date is not None
        assert end_date is not None
        assert start_value is not None
        assert end_value is not None
        assert withdrawals is not None
        assert deposits is not None
        assert fees is not None
        assert interest is not None
        assert rate is not None
        accounting_value = (
            start_value + deposits - withdrawals + interest - fees - end_value
        )
        assert abs(accounting_value) < 0.001, f"difference = {accounting_value:0.2f}"
        statement = Statement(
            account_id=account.id if isinstance(account, Account) else account,
            start_date=start_date,
            end_date=end_date,
            start_value=start_value,
            end_value=end_value,
            withdrawals=withdrawals,
            deposits=deposits,
            fees=fees,
            interest=interest,
            rate=rate,
            mileage=mileage,
            _normalize_=False,
        ).denormalize()
        created = Statement._db.insert(Table.name(Statement), **statement)
        return Statement(**created)

    @staticmethod
    def fetch(statement_id: int):
        """Get a statement by its id"""
        found = Statement._db.get_one_or_none(
            Table.name(Statement),
            _where_="id = :statement_id",
            statement_id=statement_id,
        )
        return None if found is None else Statement(**found)

    def change(self, **_to_update_):
        """Change information about the statement"""
        assert "id" not in _to_update_
        assert "account_id" not in _to_update_
        assert "account" not in _to_update_

        for field in _to_update_:
            _to_update_[field] = Table.denormalize_field(
                Statement, field, _to_update_[field]
            )

        Statement._db.change(
            Table.name(Statement),
            "statement_id",
            _where_="id = :statement_id",
            statement_id=self.id,
            **_to_update_,
        )

        for field, value in _to_update_.items():
            self.__dict__[field] = Table.normalize_field(Statement, field, value)

    def account(self):
        """Get the account for the statement"""
        return Account.fetch(self.account_id)


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
}


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


class BankApi:
    """Bank api"""

    def __init__(self, database):
        self.__db = database

    @staticmethod
    def patch(bank):
        """patch database entry for usability"""
        if bank is None:
            return None

        if isinstance(bank, list):
            return [BankApi.patch(b) for b in bank]

        bank.type = TypeOfBank[bank.type]
        return bank

    def create(
        self, name: str, url: str = None, bank_type: TypeOfBank = TypeOfBank.BANK
    ):
        """Create a new bank"""
        assert name is not None
        return BankApi.patch(
            self.__db.insert("bank", name=name, url=url, type=bank_type.name)
        )

    def get(self, bank_id: int):
        """Get a bank by its id"""
        return BankApi.patch(
            self.__db.get_one_or_none("bank", _where_="id = :bank_id", bank_id=bank_id)
        )

    def get_banks(self, bank_type: TypeOfBank = TypeOfBank.BANK):
        """Get all the banks of a given type"""
        return BankApi.patch(
            self.__db.get_all(
                "bank", _where_="type = :bank_type", bank_type=bank_type.name
            )
        )

    def count(self):
        """Count total banks"""
        return self.__db.get_one_or_none("bank", "COUNT(*)", _as_object_=False)[
            "COUNT(*)"
        ]

    def get_account_types(self, bank_id: int):
        """Get the types of accounts associated with a bank"""
        return Database.patch_account_type(
            self.__db.get_all(
                "account_type", _where_="bank_id = :bank_id", bank_id=bank_id
            )
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
        self.user = UserApi(self.__db)
        self.bank = BankApi(self.__db)

        if serialized is not None:
            try:
                with open(serialized, "r", encoding="utf-8") as script_file:
                    serialized_data = yaml.safe_load(script_file.read())

            except TypeError:
                serialized_data = serialized

            self.__deserialize(serialized_data)

    def __deserialize_users(self, serialized):
        assert "users" in serialized
        assert self.user.count() == 0, "database already exists, cannot deserialize"
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
            created[user["email"]] = self.user.create(
                user["email"],
                user.get("password_hash", user.get("password", None)),
                user["name"],
                sponsor_id,
                password_is_hashed="password_hash" in user,
            )

    def __deserialize_banks(self, serialized):
        assert "banks" in serialized
        assert self.bank.count() == 0, "database already exists, cannot deserialize"

        for bank_id in serialized["banks"]:
            bank = serialized["banks"][bank_id]
            assert bank["type"] is not None
            assert bank["type"] in dir(TypeOfBank)
            assert bank["name"] is not None
            new_bank = self.bank.create(
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
        users = self.user.get_users()
        banks = self.bank.get_banks()
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
                        for t in self.bank.get_account_types(b.id)
                    },
                }
                for b in banks
            },
        }

    # Mark: AccountType API

    @staticmethod
    def patch_account_type(account_type):
        """patch database objects for usability"""
        if account_type is None:
            return None

        if isinstance(account_type, list):
            return [Database.patch_account_type(a) for a in account_type]

        account_type.type = TypeOfAccount[account_type.type]
        return account_type

    def create_account_type(
        self, bank_id: int, name: str, account_type: TypeOfAccount, url: str = None
    ):
        """Create a bank account type"""
        assert name is not None
        return Database.patch_account_type(
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
        return Database.patch_account_type(
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
        return Database.patch_account_type(
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
