#!/usr/bin/env python3

""" The User model data
"""


import hashlib
import enum
import datetime


from financial_game.table import Table, Identifier, String, ForeignKey
from financial_game.table import Enum, Fixed, Money, Integer, Date
from financial_game.model_bank import AccountType


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

    def accounts(self):
        """Gets all the user's accounts"""
        found = User._db.get_all(
            Table.name(Account), _where_="user_id = :user_id", user_id=self.id
        )
        return [Account(**u) for u in found]


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


class InterestRate(Fixed):
    """interest rate"""

    def __init__(self, precision: int = 2, allow_null: bool = True):
        super().__init__(precision, allow_null)


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
