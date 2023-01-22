#!/usr/bin/env python3

""" The model of the data
"""

import enum
import time
import threading
import hashlib

import sqlalchemy
import sqlalchemy.ext.declarative

import yaml


Alchemy_Base = sqlalchemy.ext.declarative.declarative_base()


class User(Alchemy_Base):
    """Represents a user
    name - First name
    email - The email to contact the user
    password_hash - sha256 hash of the user's password
    """

    __tablename__ = "user"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(50))
    email = sqlalchemy.Column(sqlalchemy.String(50), unique=True)
    password_hash = sqlalchemy.Column(sqlalchemy.String(64))
    sponsor_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("user.id"))
    sponsored = sqlalchemy.orm.relationship(
        "User", backref=sqlalchemy.orm.backref("sponsor", remote_side=[id])
    )

    @staticmethod
    def hash_password(text):
        """hash utf-8 text"""
        hasher = hashlib.new("sha256")
        hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()

    def set_password(self, password):
        """Set the user password hash"""
        self.password_hash = User.hash_password(password)

    def password_matches(self, password):
        """does this match the password"""
        return User.hash_password(password) == self.password_hash

    def __repr__(self):
        """display string"""
        return (
            f'User(id={self.id} name="{self.name}" email="{self.email}" '
            + f'sponsor_id="{self.sponsor_id}" password_hash={self.password_hash})'
        )


class TypeOfBank(enum.Enum):
    """Types of Bank objects"""

    BANK = 1  # bank


class Bank(Alchemy_Base):  # pylint: disable=too-few-public-methods
    """Represents a bank or category of value
    name - name of the bank or category
    type - TypeOfBank
    url - login url
    """

    __tablename__ = "bank"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(50), unique=True)
    type = sqlalchemy.Column(sqlalchemy.Enum(TypeOfBank))
    url = sqlalchemy.Column(sqlalchemy.String(2083))
    account_types = sqlalchemy.orm.relationship("AccountType", backref="bank")

    def __repr__(self):
        """display string"""
        return (
            f'Bank(id={self.id} name="{self.name}" url="{self.url}" type="{self.type}")'
        )


class TypeOfAccount(enum.Enum):
    """Types of AccountType objects"""

    CRED = 1  # Credit Card
    CHCK = 2  # Checking
    SAVE = 3  # Savings
    MONM = 4  # Money Market
    BROK = 5  # Brokrage account


class AccountType(Alchemy_Base):  # pylint: disable=too-few-public-methods
    """Represents a type of bank account or category of value
    name - name of the type of account
    type - TypeOfAccount
    url - login url
    """

    __tablename__ = "account_type"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(50), unique=True)
    type = sqlalchemy.Column(sqlalchemy.Enum(TypeOfAccount))
    url = sqlalchemy.Column(sqlalchemy.String(2083))
    bank_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("bank.id"))

    def __repr__(self):
        """display string"""
        return f'AccountType(id={self.id} name="{self.name}" url="{self.url}")'


class Database:
    """stored information"""

    def __init__(self, db_url, serialized=None):
        """create db
        db_url - a SqlAlchemy URL for the database
        serialized - optional dictionary or path to yaml file
        """
        self.__db_url = db_url
        self.__sessions = {}
        self.__session_lock = threading.Lock()
        engine = sqlalchemy.create_engine(self.__db_url)
        self.__factory = sqlalchemy.orm.sessionmaker(bind=engine)
        Alchemy_Base.metadata.create_all(engine)
        self.__session_creator = sqlalchemy.orm.scoped_session(self.__factory)

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
                return_created=True,
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
                bank["name"], bank.get("url", None), bank["type"], return_created=True
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
                    type_info["type"],
                    url=type_info.get("url", None),
                )

    def __deserialize(self, serialized):
        assert len(serialized) == 2
        self.__deserialize_users(serialized)
        self.__deserialize_banks(serialized)

    def __session(self):
        thread_id = threading.current_thread().ident

        with self.__session_lock:
            if thread_id not in self.__sessions:
                self.__sessions[thread_id] = {
                    "session": self.__session_creator(),
                    "access": time.time(),
                }
            else:
                self.__sessions[thread_id]["access"] = time.time()
        return self.__sessions[thread_id]["session"]

    def __add(self, entry, refresh=False):
        self.__session().add(entry)
        self.__session().commit()

        if refresh:
            self.__session().refresh(entry)

        return entry

    def sessions(self):
        """Return the number seconds since last access of all active sessions"""
        now = time.time()
        with self.__session_lock:
            return [now - s["access"] for s in self.__sessions.values()]

    def flush(self):
        """flush all changes to the database"""
        self.__session().commit()

    def close(self):
        """close down the connection to the database"""
        self.__session().commit()
        self.__session().close()

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
                        for t in b.account_types
                    },
                }
                for b in banks
            },
        }

    # Mark: User API

    # pylint: disable=too-many-arguments
    def create_user(
        self,
        email,
        password,
        name,
        sponsor_id,
        return_created=False,
        password_is_hashed=False,
    ):
        """create a new employee entry"""
        assert password is not None
        created = self.__add(
            User(
                email=email,
                password_hash=password
                if password_is_hashed
                else User.hash_password(password),
                name=name,
                sponsor_id=sponsor_id,
            ),
            refresh=return_created,
        )
        return created if return_created else None

    def get_user(self, user_id):
        """Get a user by its id"""
        return (
            self.__session().query(User).filter(User.id == int(user_id)).one_or_none()
            if user_id is not None
            else None
        )

    def find_user(self, email):
        """Get a user by email (case insensitive)"""
        return (
            self.__session()
            .query(User)
            .filter(sqlalchemy.func.lower(User.email) == sqlalchemy.func.lower(email))
            .one_or_none()
        )

    def get_users(self):
        """Get list of all users"""
        return self.__session().query(User).all()

    def count_users(self):
        """Count total users"""
        return self.__session().query(sqlalchemy.func.count(User.id)).one_or_none()[0]

    # Mark: Bank API

    def create_bank(
        self, name, url=None, bank_type=TypeOfBank.BANK, return_created=False
    ):
        """Create a new bank"""
        assert name is not None
        created = self.__add(
            Bank(name=name, url=url, type=bank_type), refresh=return_created
        )
        return created if return_created else None

    def get_bank(self, bank_id):
        """Get a bank by its id"""
        return (
            self.__session().query(Bank).filter(Bank.id == int(bank_id)).one_or_none()
            if bank_id is not None
            else None
        )

    def get_banks(self, bank_type=TypeOfBank.BANK):
        """Get all the banks of a given type"""
        return self.__session().query(Bank).filter(Bank.type == bank_type).all()

    def count_banks(self):
        """Count total banks"""
        return self.__session().query(sqlalchemy.func.count(Bank.id)).one_or_none()[0]

    # Mark: AccountType API

    def create_account_type(
        self, bank_id, name, account_type, url=None, return_created=False
    ):
        """Create a bank account type"""
        assert name is not None
        created = self.__add(
            AccountType(name=name, url=url, bank_id=bank_id, type=account_type),
            refresh=return_created,
        )
        return created if return_created else None
