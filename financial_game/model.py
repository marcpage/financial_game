#!/usr/bin/env python3

""" The model of the data
"""

import time
import threading
import hashlib

import sqlalchemy
import sqlalchemy.ext.declarative


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
    email = sqlalchemy.Column(sqlalchemy.String(50))
    password_hash = sqlalchemy.Column(sqlalchemy.String(64))

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
        return f'User(id={self.id} name="{self.name}" email="{self.email}")'


class Database:
    """stored information"""

    def __init__(self, db_url):
        """create db"""
        self.__db_url = db_url
        self.__sessions = {}
        self.__session_lock = threading.Lock()
        engine = sqlalchemy.create_engine(self.__db_url)
        self.__factory = sqlalchemy.orm.sessionmaker(bind=engine)
        Alchemy_Base.metadata.create_all(engine)
        self.__session_creator = sqlalchemy.orm.scoped_session(self.__factory)

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

    def __add(self, entry):
        self.__session().add(entry)
        self.__session().commit()
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

    # Mark: User API

    def create_user(self, email, password, name):
        """create a new employee entry"""
        found = self.find_user(email)
        return (
            self.__add(
                User(
                    email=email,
                    password_hash=User.hash_password(password),
                    name=name,
                )
            )
            if found is None
            else found
        )

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
