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
