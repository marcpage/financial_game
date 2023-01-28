#!/usr/bin/env python3

import tempfile
import os
from datetime import date

import financial_game.model
from financial_game.model import TypeOfAccount, TypeOfBank, User, Bank, AccountType, Account, AccountPurpose, Statement
from financial_game.table import Table
import financial_game.database


TEST_YAML_PATH = os.path.join(os.path.split(__file__)[0], "model.yaml")


def test_user():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.user.create("john.appleseed@apple.com", "Setec astronomy", "John", None)
        assert john.id is not None
        db.user.create("Jane.Doe@apple.com", "too many secrets", "Jane", john.id)

        assert db.user.count() == 2, f"users = {db.user.count()}"
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.user.find("john.appleseed@apple.com")
        john_id = john.id
        assert db.user.count() == 2, "users = {db.user.count()}"
        assert john.name == "John"
        assert financial_game.model.Database.password_matches(john, "Setec astronomy")
        assert not financial_game.model.Database.password_matches(john, "setec astronomy")
        assert not financial_game.model.Database.password_matches(john, "too many secrets")
        db.user.change_info(john.id, password_hash=financial_game.model.Database.hash_password("setec astronomy"))

        jane = db.user.find("jane.doe@apple.com")
        jane_id = jane.id
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id, f"Jane sponsor = {jane.sponsor_id} john = {john.id}"
        assert financial_game.model.Database.password_matches(jane, "too many secrets")
        assert not financial_game.model.Database.password_matches(jane, "Setec astronomy")
        assert not financial_game.model.Database.password_matches(jane, "too many Secrets")
        assert jane.sponsor_id == john.id
        assert len(db.user.get_sponsored(jane.id)) == 0
        john_sponsored = db.user.get_sponsored(john.id)
        assert len(john_sponsored) == 1
        assert john_sponsored[0].id == jane.id

        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.user.get(john_id)
        assert db.user.count() == 2, "users = {db.user.count()}"
        assert john.name == "John"
        assert financial_game.model.Database.password_matches(john, "setec astronomy")
        assert not financial_game.model.Database.password_matches(john, "Setec astronomy")

        jane = db.user.get(jane_id)
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id
        assert len(db.user.get_sponsored(jane.id)) == 0
        john_sponsored = db.user.get_sponsored(john.id)
        assert len(john_sponsored) == 1
        assert john_sponsored[0].id == jane.id
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        users = db.user.get_users()
        assert db.user.count() == 2, "users = {db.user.count()}"
        assert len(users) == 2
        user_names = [u.name for u in users]
        assert 'John' in user_names
        assert 'Jane' in user_names

        db.close()


def test_bank():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_id = boa.id
        assert boa.id is not None, boa
        assert boa.name == "Bank of America", boa
        assert boa.url == "https://www.bankofamerica.com/", boa
        assert boa.type == TypeOfBank.BANK, boa

        chase = db.bank.create("Chase", "https://www.chase.com/")
        chase_id = chase.id
        assert chase.id is not None, chase
        assert chase.name == "Chase", chase
        assert chase.url == "https://www.chase.com/", chase
        assert chase.type == TypeOfBank.BANK, chase

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.bank.get(boa_id)
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK

        chase = db.bank.get(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        banks = db.bank.get_banks()
        assert set(b.type for b in banks) == {TypeOfBank.BANK}, f"banks = {banks}"
        assert "Chase" in [b.name for b in banks], f"banks = {banks}"
        assert "Bank of America" in [b.name for b in banks], f"banks = {banks}"
        assert "https://www.bankofamerica.com/" in [b.url for b in banks], f"banks = {banks}"
        assert "https://www.chase.com/" in [b.url for b in banks], f"banks = {banks}"

        assert db.bank.get(0xDEADBEEF) is None

        db.close()


def test_account_type():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_id = boa.id
        assert boa.id is not None, boa

        boa_cc = db.create_account_type(boa.id, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_cc_id = boa_cc.id
        assert boa_cc.id is not None
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_cc.type == TypeOfAccount.CRED
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa_id

        boa_check = db.create_account_type(boa.id, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        boa_check_id = boa_check.id
        assert boa_check.id is not None
        assert boa_check.name == "Advantage Banking"
        assert boa_check.type == TypeOfAccount.CHCK
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_check.bank_id == boa_id

        chase = db.bank.create("Chase", "https://www.chase.com/")
        chase_id = chase.id
        assert chase.id is not None

        chase_cc = db.create_account_type(chase.id, "Amazon Rewards", TypeOfAccount.CRED)
        chase_cc_id = chase_cc.id
        assert chase_cc.id is not None
        assert chase_cc.name == "Amazon Rewards"
        assert chase_cc.type == TypeOfAccount.CRED
        assert chase_cc.url is None
        assert chase_cc.bank_id == chase_id

        chase_savings = db.create_account_type(chase.id, "Chase Savings", TypeOfAccount.SAVE)
        chase_savings_id = chase_savings.id
        assert chase_savings.id is not None
        assert chase_savings.name == "Chase Savings"
        assert chase_savings.type == TypeOfAccount.SAVE
        assert chase_savings.url is None
        assert chase_savings.bank_id == chase_id

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.bank.get(boa_id)
        boa_account_types = db.bank.get_account_types(boa.id)
        assert len(boa_account_types) == 2
        boa_cc = [t for t in boa_account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa_account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa_account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa.id
        assert boa_check.bank_id == boa.id

        chase = db.bank.get(chase_id)
        chase_account_types = db.bank.get_account_types(chase.id)
        assert len(chase_account_types) == 2
        chase_cc = [t for t in chase_account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase_account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase_account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank_id == chase.id
        assert chase_cc.bank_id == chase.id

        chase_cc = db.get_account_type(chase_cc_id)
        assert chase_cc.id is not None
        assert chase_cc.name == "Amazon Rewards"
        assert chase_cc.type == TypeOfAccount.CRED, chase_cc
        assert chase_cc.url is None
        assert chase_cc.bank_id == chase_id

        chase_savings = db.get_account_type(chase_savings_id)
        assert chase_savings.id is not None
        assert chase_savings.name == "Chase Savings"
        assert chase_savings.type == TypeOfAccount.SAVE
        assert chase_savings.url is None
        assert chase_savings.bank_id == chase_id

        boa_cc = db.get_account_type(boa_cc_id)
        assert boa_cc.bank_id == boa.id
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_cc.url is None

        boa_check = db.get_account_type(boa_check_id)
        assert boa_check.bank_id == boa.id
        assert boa_check.name == "Advantage Banking"
        assert boa_check.url == "https://www.bankofamerica.com/checking"

        assert db.get_account_type(0xDEADBEEF) is None

        db.close()


def test_serialize():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.user.create("john.appleseed@apple.com", "Setec astronomy", "John", None)
        assert john.id is not None
        db.user.create("Jane.Doe@apple.com", "too many secrets", "Jane", john.id)
        boa = db.bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_cc = db.create_account_type(boa.id, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_check = db.create_account_type(boa.id, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        chase = db.bank.create("Chase", "https://www.chase.com/")
        chase_cc = db.create_account_type(chase.id, "Amazon Rewards", TypeOfAccount.CRED)
        chase_savings = db.create_account_type(chase.id, "Chase Savings", TypeOfAccount.SAVE)

        assert db.user.count() == 2, "users = {db.user.count()}"
        assert db.bank.count() == 2
        serialized = db.serialize()
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test2.sqlite3", serialized)

        john = db.user.find("john.appleseed@apple.com")
        assert db.user.count() == 2, "users = {db.user.count()}"
        assert john.name == "John"
        assert not financial_game.model.Database.password_matches(john, "setec astronomy")
        assert financial_game.model.Database.password_matches(john, "Setec astronomy")

        jane = db.user.find("jane.doe@apple.com")
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id, f"Jane sponsor = {jane.sponsor_id} john = {john.id}"
        assert jane.sponsor_id == john.id
        assert len(db.user.get_sponsored(jane.id)) == 0
        assert len(db.user.get_sponsored(john.id)) == 1
        assert db.user.get_sponsored(john.id)[0].id == jane.id

        banks = db.bank.get_banks()
        assert set(b.type for b in banks) == {TypeOfBank.BANK}
        assert "Chase" in [b.name for b in banks]
        assert "Bank of America" in [b.name for b in banks]
        assert "https://www.bankofamerica.com/" in [b.url for b in banks]
        assert "https://www.chase.com/" in [b.url for b in banks]
        boa_id = [b.id for b in banks if b.name == "Bank of America"][0]
        chase_id = [b.id for b in banks if b.name == "Chase"][0]

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test2.sqlite3")

        boa = db.bank.get(boa_id)
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK
        boa_account_types = db.bank.get_account_types(boa.id)
        boa_cc = [t for t in boa_account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa_account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa_account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa.id
        assert boa_check.bank_id == boa.id

        chase = db.bank.get(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK
        chase_account_types = db.bank.get_account_types(chase.id)
        chase_cc = [t for t in chase_account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase_account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase_account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank_id == chase.id
        assert chase_cc.bank_id == chase.id

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test3.sqlite3", TEST_YAML_PATH)

        users = db.user.get_users()
        assert db.user.count() == 2, "users = {db.user.count()}"
        assert len(users) == 2
        user_names = [u.name for u in users]
        assert 'John' in user_names
        assert 'Jane' in user_names
        banks = db.bank.get_banks()

        boa = [b for b in banks if b.name == "Bank of America"][0]
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK
        boa_account_types = db.bank.get_account_types(boa.id)
        boa_cc = [t for t in boa_account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa_account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa_account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa.id
        assert boa_check.bank_id == boa.id

        chase = [b for b in banks if b.name == "Chase"][0]
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK
        chase_account_types = db.bank.get_account_types(chase.id)
        chase_cc = [t for t in chase_account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase_account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase_account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank_id == chase.id
        assert chase_cc.bank_id == chase.id


def test_user_class():
    with tempfile.TemporaryDirectory() as workspace:
        db_url = "sqlite:///" + workspace + "test.sqlite3"
        User._db = financial_game.database.Connection.connect(db_url, False)
        User._db.create_tables(**Table.database_description(User))

        john = User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        assert john.id is not None
        User.create("Jane.Doe@apple.com", "too many secrets", "Jane", john)

        assert User.total() == 2, f"users = {db.user.total()}"
        User._db.close()

        User._db = financial_game.database.Connection.connect(db_url, False)

        john = User.lookup("john.appleseed@apple.com")
        john_id = john.id
        assert User.total() == 2, "users = {User.total()}"
        assert john.name == "John", john
        assert john.password_matches("Setec astronomy")
        assert not john.password_matches("setec astronomy")
        assert not john.password_matches("too many secrets")
        john.change(password_hash=User.hash_password("setec astronomy"))

        jane = User.lookup("jane.doe@apple.com")
        jane_id = jane.id
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id, f"Jane sponsor = {jane.sponsor_id} john = {john.id}"
        assert jane.password_matches("too many secrets")
        assert not jane.password_matches("Setec astronomy")
        assert not jane.password_matches("too many Secrets")
        assert jane.sponsor_id == john.id
        assert len(jane.sponsored()) == 0
        john_sponsored = john.sponsored()
        assert len(john_sponsored) == 1
        assert john_sponsored[0].id == jane.id

        User._db.close()

        User._db = financial_game.database.Connection.connect(db_url, False)

        john = User.fetch(john_id)
        assert User.total() == 2, "users = {User.total()}"
        assert john.name == "John"
        assert john.password_matches("setec astronomy")
        assert not john.password_matches("Setec astronomy")

        jane = User.fetch(jane_id)
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id
        assert len(jane.sponsored()) == 0
        john_sponsored = john.sponsored()
        assert len(john_sponsored) == 1
        assert john_sponsored[0].id == jane.id
        jane.change(password="Too Many Secrets")
        assert jane.password_matches("Too Many Secrets")
        assert not jane.password_matches("too many secrets")
        jane = User.fetch(jane_id)
        assert jane.password_matches("Too Many Secrets")
        assert not jane.password_matches("too many secrets")
        User._db.close()

        User._db = financial_game.database.Connection.connect(db_url, False)

        jane = User.fetch(jane_id)
        assert jane.password_matches("Too Many Secrets")
        assert not jane.password_matches("too many secrets")

        users = User.every()
        assert User.total() == 2, "users = {User.total()}"
        assert len(users) == 2
        user_names = [u.name for u in users]
        assert 'John' in user_names
        assert 'Jane' in user_names

        User._db.close()


def test_bank_class():
    with tempfile.TemporaryDirectory() as workspace:
        db_url = "sqlite:///" + workspace + "test.sqlite3"
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        Bank._db.create_tables(**Table.database_description(Bank))

        boa = Bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_id = boa.id
        assert boa.id is not None, boa
        assert boa.name == "Bank of America", boa
        assert boa.url == "https://www.bankofamerica.com/", boa
        assert boa.type == TypeOfBank.BANK, boa
        assert Bank.total() == 1

        chase = Bank.create("Chase", "https://www.chase.com/")
        chase_id = chase.id
        assert chase.id is not None, chase
        assert chase.name == "Chase", chase
        assert chase.url == "https://www.chase.com/", chase
        assert chase.type == TypeOfBank.BANK, chase
        assert Bank.total() == 2

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)

        assert Bank.total() == 2
        boa = Bank.fetch(boa_id)
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK

        chase = Bank.fetch(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)

        banks = Bank.every()
        assert set(b.type for b in banks) == {TypeOfBank.BANK}, f"banks = {banks}"
        assert "Chase" in [b.name for b in banks], f"banks = {banks}"
        assert "Bank of America" in [b.name for b in banks], f"banks = {banks}"
        assert "https://www.bankofamerica.com/" in [b.url for b in banks], f"banks = {banks}"
        assert "https://www.chase.com/" in [b.url for b in banks], f"banks = {banks}"

        assert Bank.fetch(0xDEADBEEF) is None

        Bank._db.close()


def test_account_type_class():
    with tempfile.TemporaryDirectory() as workspace:
        db_url = "sqlite:///" + workspace + "test.sqlite3"
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        AccountType._db = Bank._db
        Bank._db.create_tables(**Table.database_description(Bank, AccountType))

        boa = Bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_id = boa.id
        assert boa.id is not None, boa

        boa_cc = AccountType.create(boa, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_cc_id = boa_cc.id
        assert boa_cc.id is not None
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_cc.type == TypeOfAccount.CRED
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa_id

        boa_check = AccountType.create(boa, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        boa_check_id = boa_check.id
        assert boa_check.id is not None
        assert boa_check.name == "Advantage Banking"
        assert boa_check.type == TypeOfAccount.CHCK
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_check.bank_id == boa_id

        chase = Bank.create("Chase", "https://www.chase.com/")
        chase_id = chase.id
        assert chase.id is not None

        chase_cc = AccountType.create(chase, "Amazon Rewards", TypeOfAccount.CRED)
        chase_cc_id = chase_cc.id
        assert chase_cc.id is not None
        assert chase_cc.name == "Amazon Rewards"
        assert chase_cc.type == TypeOfAccount.CRED
        assert chase_cc.url is None
        assert chase_cc.bank_id == chase_id

        chase_savings = AccountType.create(chase, "Chase Savings", TypeOfAccount.SAVE)
        chase_savings_id = chase_savings.id
        assert chase_savings.id is not None
        assert chase_savings.name == "Chase Savings"
        assert chase_savings.type == TypeOfAccount.SAVE
        assert chase_savings.url is None
        assert chase_savings.bank_id == chase_id

        assert boa_cc.bank().id == boa.id, f"boa_cc = {boa_cc} boa = {boa}"
        assert boa_check.bank().id == boa.id
        assert chase_cc.bank().id == chase.id
        assert chase_savings.bank().id == chase.id

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        AccountType._db = Bank._db

        boa = Bank.fetch(boa_id)
        boa_account_types = boa.account_types()
        assert len(boa_account_types) == 2
        boa_cc = [t for t in boa_account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa_account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa_account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa.id
        assert boa_check.bank_id == boa.id

        chase = Bank.fetch(chase_id)
        chase_account_types = chase.account_types()
        assert len(chase_account_types) == 2
        chase_cc = [t for t in chase_account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase_account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase_account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank_id == chase.id
        assert chase_cc.bank_id == chase.id

        chase_cc = AccountType.fetch(chase_cc_id)
        assert chase_cc.id is not None
        assert chase_cc.name == "Amazon Rewards"
        assert chase_cc.type == TypeOfAccount.CRED, chase_cc
        assert chase_cc.url is None
        assert chase_cc.bank_id == chase_id

        chase_savings = AccountType.fetch(chase_savings_id)
        assert chase_savings.id is not None
        assert chase_savings.name == "Chase Savings"
        assert chase_savings.type == TypeOfAccount.SAVE
        assert chase_savings.url is None
        assert chase_savings.bank_id == chase_id

        boa_cc = AccountType.fetch(boa_cc_id)
        assert boa_cc.bank_id == boa.id
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_cc.url is None

        boa_check = AccountType.fetch(boa_check_id)
        assert boa_check.bank_id == boa.id
        assert boa_check.name == "Advantage Banking"
        assert boa_check.url == "https://www.bankofamerica.com/checking"

        assert boa_cc.bank().id == boa.id
        assert boa_check.bank().id == boa.id
        assert chase_cc.bank().id == chase.id
        assert chase_savings.bank().id == chase.id

        assert AccountType.fetch(0xDEADBEEF) is None

        Bank._db.close()


def test_account_class():
    with tempfile.TemporaryDirectory() as workspace:
        db_url = "sqlite:///" + workspace + "test.sqlite3"
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        AccountType._db, Account._db, User._db = (Bank._db,)*3
        Bank._db.create_tables(**Table.database_description(Bank, AccountType, Account, User))

        john = User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        jane = User.create("Jane.Doe@apple.com", "too many secrets", "Jane", john)

        boa = Bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_cc = AccountType.create(boa, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_check = AccountType.create(boa, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        chase = Bank.create("Chase", "https://www.chase.com/")
        chase_cc = AccountType.create(chase, "Amazon Rewards", TypeOfAccount.CRED)
        chase_savings = AccountType.create(chase, "Chase Savings", TypeOfAccount.SAVE)

        john_checking = Account.create(john, boa_check, "budget", "usual", AccountPurpose.BUDG)
        assert john_checking.id is not None
        assert john_checking.label == "budget"
        assert john_checking.hint == "usual"
        assert john_checking.purpose == AccountPurpose.BUDG
        assert john_checking.user().id == john.id
        assert john_checking.account_type().id == boa_check.id

        john_cc = Account.create(john, boa_cc, "credit card", "normal")
        assert john_cc.id is not None
        assert john_cc.label == "credit card"
        assert john_cc.hint == "normal"
        assert john_cc.purpose is None
        assert john_cc.user().id == john.id
        assert john_cc.account_type().id == boa_cc.id

        jane_main_cc = Account.create(jane, boa_cc, "main card")
        assert jane_main_cc.id is not None
        assert jane_main_cc.label == "main card"
        assert jane_main_cc.hint is None
        assert jane_main_cc.purpose is None
        assert jane_main_cc.user().id == jane.id
        assert jane_main_cc.account_type().id == boa_cc.id

        jane_backup_cc = Account.create(jane, chase_cc, "backup card")
        assert jane_backup_cc.id is not None
        assert jane_backup_cc.label == "backup card"
        assert jane_backup_cc.hint is None
        assert jane_backup_cc.purpose is None
        assert jane_backup_cc.user().id == jane.id
        assert jane_backup_cc.account_type().id == chase_cc.id

        jane_savings = Account.create(jane, chase_savings, "emergency", purpose=AccountPurpose.MRGC)
        assert jane_savings.id is not None
        assert jane_savings.label == "emergency"
        assert jane_savings.hint is None
        assert jane_savings.purpose == AccountPurpose.MRGC
        assert jane_savings.user().id == jane.id
        assert jane_savings.account_type().id == chase_savings.id

        jane_savings.change(label="emergency fund")
        assert jane_savings.label == "emergency fund"

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        AccountType._db, Account._db, User._db = (Bank._db,)*3

        john_cc = Account.fetch(john_cc.id)
        assert john_cc.id is not None
        assert john_cc.label == "credit card"
        assert john_cc.hint == "normal"
        assert john_cc.purpose is None
        assert john_cc.user().id == john.id
        assert john_cc.account_type().id == boa_cc.id

        jane_main_cc = Account.fetch(jane_main_cc.id)
        assert jane_main_cc.id is not None
        assert jane_main_cc.label == "main card"
        assert jane_main_cc.hint is None
        assert jane_main_cc.purpose is None
        assert jane_main_cc.user().id == jane.id
        assert jane_main_cc.account_type().id == boa_cc.id

        jane_backup_cc = Account.fetch(jane_backup_cc.id)
        assert jane_backup_cc.id is not None
        assert jane_backup_cc.label == "backup card"
        assert jane_backup_cc.hint is None
        assert jane_backup_cc.purpose is None
        assert jane_backup_cc.user().id == jane.id
        assert jane_backup_cc.account_type().id == chase_cc.id

        jane_savings = Account.fetch(jane_savings.id)
        assert jane_savings.id is not None
        assert jane_savings.label == "emergency fund"
        assert jane_savings.hint is None
        assert jane_savings.purpose == AccountPurpose.MRGC
        assert jane_savings.user().id == jane.id
        assert jane_savings.account_type().id == chase_savings.id


def test_statement_class():
    with tempfile.TemporaryDirectory() as workspace:
        db_url = "sqlite:///" + workspace + "test.sqlite3"
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        Statement._db, AccountType._db, Account._db, User._db = (Bank._db,)*4
        Bank._db.create_tables(**Table.database_description(Bank, Statement, AccountType, Account, User))

        john = User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        jane = User.create("Jane.Doe@apple.com", "too many secrets", "Jane", john)
        boa = Bank.create("Bank of America", "https://www.bankofamerica.com/")
        boa_cc = AccountType.create(boa, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_check = AccountType.create(boa, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        chase = Bank.create("Chase", "https://www.chase.com/")
        chase_cc = AccountType.create(chase, "Amazon Rewards", TypeOfAccount.CRED)
        chase_savings = AccountType.create(chase, "Chase Savings", TypeOfAccount.SAVE)
        john_checking = Account.create(john, boa_check, "budget", "usual", AccountPurpose.BUDG)
        john_cc = Account.create(john, boa_cc, "credit card", "normal")
        jane_main_cc = Account.create(jane, boa_cc, "main card")
        jane_backup_cc = Account.create(jane, chase_cc, "backup card")
        jane_savings = Account.create(jane, chase_savings, "emergency", purpose=AccountPurpose.MRGC)

        john_checking_june = Statement.create(account=john_checking, start_date=date(2022, 6, 1), end_date=date(2022, 6, 30), start_value=3.14, end_value=13.37, deposits=12.95, withdrawals=2.72, fees=0.00, interest=0.00, rate=0.50)
        assert john_checking_june.id is not None
        assert john_checking_june.account().id == john_checking.id
        assert john_checking_june.start_date == date(2022, 6, 1)
        assert john_checking_june.end_date == date(2022, 6, 30)
        assert abs(john_checking_june.start_value - 3.14) < 0.001
        assert abs(john_checking_june.end_value - 13.37) < 0.001
        assert abs(john_checking_june.deposits - 12.95) < 0.001
        assert abs(john_checking_june.withdrawals - 2.72) < 0.001
        assert abs(john_checking_june.fees) < 0.001
        assert abs(john_checking_june.interest) < 0.001
        assert abs(john_checking_june.rate - 0.50) < 0.001
        assert john_checking_june.mileage is None

        john_checking_may = Statement.create(account=john_checking, start_date=date(2022, 5, 1), end_date=date(2022, 5, 31), start_value=0.00, end_value=3.14, deposits=12.95, withdrawals=9.20, fees=0.81, interest=0.20, rate=0.50)
        assert john_checking_may.id is not None
        assert john_checking_may.account().id == john_checking.id
        assert john_checking_may.start_date == date(2022, 5, 1)
        assert john_checking_may.end_date == date(2022, 5, 31)
        assert abs(john_checking_may.start_value) < 0.001
        assert abs(john_checking_may.end_value - 3.14) < 0.001
        assert abs(john_checking_may.deposits - 12.95) < 0.001
        assert abs(john_checking_may.withdrawals - 9.20) < 0.001
        assert abs(john_checking_may.fees - 0.81) < 0.001
        assert abs(john_checking_may.interest - 0.20) < 0.001
        assert abs(john_checking_may.rate - 0.50) < 0.001
        assert john_checking_may.mileage is None

        john_cc_june = Statement.create(account=john_cc, start_date=date(2022, 5, 22), end_date=date(2022, 6, 21), start_value=3.13, end_value=13.33, deposits=12.95, withdrawals=2.72, fees=0.01, interest=-0.02, rate=1.20)
        assert john_cc_june.id is not None
        assert john_cc_june.account().id == john_cc.id
        assert john_cc_june.start_date == date(2022, 5, 22)
        assert john_cc_june.end_date == date(2022, 6, 21)
        assert abs(john_cc_june.start_value - 3.13) < 0.001
        assert abs(john_cc_june.end_value - 13.33) < 0.001
        assert abs(john_cc_june.deposits - 12.95) < 0.001
        assert abs(john_cc_june.withdrawals - 2.72) < 0.001
        assert abs(john_cc_june.fees - 0.01) < 0.001
        assert abs(john_cc_june.interest + 0.02) < 0.001
        assert abs(john_cc_june.rate - 1.2) < 0.001
        assert john_cc_june.mileage is None

        jane_savings_june = Statement.create(account=jane_savings, start_date=date(2022, 5, 15), end_date=date(2022, 6, 14), start_value=3.11, end_value=13.36, deposits=12.97, withdrawals=2.71, fees=0.03, interest=0.02, rate=4.32, mileage=100000)
        assert jane_savings_june.id is not None
        assert jane_savings_june.account().id == jane_savings.id
        assert jane_savings_june.start_date == date(2022, 5, 15)
        assert jane_savings_june.end_date == date(2022, 6, 14)
        assert abs(jane_savings_june.start_value - 3.11) < 0.001
        assert abs(jane_savings_june.end_value - 13.36) < 0.001
        assert abs(jane_savings_june.deposits - 12.97) < 0.001
        assert abs(jane_savings_june.withdrawals - 2.71) < 0.001
        assert abs(jane_savings_june.fees - 0.03) < 0.001
        assert abs(jane_savings_june.interest - 0.02) < 0.001
        assert abs(jane_savings_june.rate - 4.32) < 0.001
        assert jane_savings_june.mileage == 100000

        john_checking_statements = john_checking.statements()
        assert len(john_checking_statements) == 2
        assert set(s.id for s in john_checking_statements) == {john_checking_may.id, john_checking_june.id}

        john_cc_statements = john_cc.statements()
        assert len(john_cc_statements) == 1
        assert set(s.id for s in john_cc_statements) == {john_cc_june.id}

        jane_savings_statments = jane_savings.statements()
        assert len(jane_savings_statments) == 1
        assert set(s.id for s in jane_savings_statments) == {jane_savings_june.id}

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        Statement._db, AccountType._db, Account._db, User._db = (Bank._db,)*4

        john_checking_june = Statement.fetch(john_checking_june.id)
        assert john_checking_june.id is not None
        assert john_checking_june.account().id == john_checking.id
        assert john_checking_june.start_date == date(2022, 6, 1)
        assert john_checking_june.end_date == date(2022, 6, 30)
        assert abs(john_checking_june.start_value - 3.14) < 0.001
        assert abs(john_checking_june.end_value - 13.37) < 0.001
        assert abs(john_checking_june.deposits - 12.95) < 0.001
        assert abs(john_checking_june.withdrawals - 2.72) < 0.001
        assert abs(john_checking_june.fees) < 0.001
        assert abs(john_checking_june.interest) < 0.001
        assert abs(john_checking_june.rate - 0.50) < 0.001
        assert john_checking_june.mileage is None

        john_checking_may = Statement.fetch(john_checking_may.id)
        assert john_checking_may.id is not None
        assert john_checking_may.account().id == john_checking.id
        assert john_checking_may.start_date == date(2022, 5, 1)
        assert john_checking_may.end_date == date(2022, 5, 31)
        assert abs(john_checking_may.start_value) < 0.001
        assert abs(john_checking_may.end_value - 3.14) < 0.001
        assert abs(john_checking_may.deposits - 12.95) < 0.001
        assert abs(john_checking_may.withdrawals - 9.20) < 0.001
        assert abs(john_checking_may.fees - 0.81) < 0.001
        assert abs(john_checking_may.interest - 0.20) < 0.001
        assert abs(john_checking_may.rate - 0.50) < 0.001
        assert john_checking_may.mileage is None

        john_cc_june = Statement.fetch(john_cc_june.id)
        assert john_cc_june.id is not None
        assert john_cc_june.account().id == john_cc.id
        assert john_cc_june.start_date == date(2022, 5, 22)
        assert john_cc_june.end_date == date(2022, 6, 21)
        assert abs(john_cc_june.start_value - 3.13) < 0.001
        assert abs(john_cc_june.end_value - 13.33) < 0.001
        assert abs(john_cc_june.deposits - 12.95) < 0.001
        assert abs(john_cc_june.withdrawals - 2.72) < 0.001
        assert abs(john_cc_june.fees - 0.01) < 0.001
        assert abs(john_cc_june.interest + 0.02) < 0.001
        assert abs(john_cc_june.rate - 1.2) < 0.001
        assert john_cc_june.mileage is None

        jane_savings_june = Statement.fetch(jane_savings_june.id)
        assert jane_savings_june.id is not None
        assert jane_savings_june.account().id == jane_savings.id
        assert jane_savings_june.start_date == date(2022, 5, 15)
        assert jane_savings_june.end_date == date(2022, 6, 14)
        assert abs(jane_savings_june.start_value - 3.11) < 0.001
        assert abs(jane_savings_june.end_value - 13.36) < 0.001
        assert abs(jane_savings_june.deposits - 12.97) < 0.001
        assert abs(jane_savings_june.withdrawals - 2.71) < 0.001
        assert abs(jane_savings_june.fees - 0.03) < 0.001
        assert abs(jane_savings_june.interest - 0.02) < 0.001
        assert abs(jane_savings_june.rate - 4.32) < 0.001
        assert jane_savings_june.mileage == 100000

        john_checking = Account.fetch(john_checking.id)
        john_checking_statements = john_checking.statements()
        assert len(john_checking_statements) == 2
        assert set(s.id for s in john_checking_statements) == {john_checking_may.id, john_checking_june.id}

        john_cc = Account.fetch(john_cc.id)
        john_cc_statements = john_cc.statements()
        assert len(john_cc_statements) == 1
        assert set(s.id for s in john_cc_statements) == {john_cc_june.id}

        jane_savings = Account.fetch(jane_savings.id)
        jane_savings_statments = jane_savings.statements()
        assert len(jane_savings_statments) == 1
        assert set(s.id for s in jane_savings_statments) == {jane_savings_june.id}

        jane_savings_june.change(mileage=120000)
        assert jane_savings_june.mileage == 120000

        Bank._db.close()
        Bank._db = financial_game.database.Connection.connect(db_url, False)
        Statement._db, AccountType._db, Account._db, User._db = (Bank._db,)*4

        jane_savings_june = Statement.fetch(jane_savings_june.id)
        assert jane_savings_june.mileage == 120000


if __name__ == "__main__":
    test_statement_class()
    test_account_class()
    test_account_type_class()
    test_bank_class()
    test_user_class()
    test_user()
    test_bank()
    test_account_type()
    test_serialize()

