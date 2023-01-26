#!/usr/bin/env python3

import tempfile
import os

import financial_game.model
from financial_game.model import TypeOfAccount, TypeOfBank


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

        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/")
        boa_id = boa.id
        assert boa.id is not None, boa
        assert boa.name == "Bank of America", boa
        assert boa.url == "https://www.bankofamerica.com/", boa
        assert boa.type == TypeOfBank.BANK, boa

        chase = db.create_bank("Chase", "https://www.chase.com/")
        chase_id = chase.id
        assert chase.id is not None, chase
        assert chase.name == "Chase", chase
        assert chase.url == "https://www.chase.com/", chase
        assert chase.type == TypeOfBank.BANK, chase

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.get_bank(boa_id)
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK

        chase = db.get_bank(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        banks = db.get_banks()
        assert set(b.type for b in banks) == {TypeOfBank.BANK}, f"banks = {banks}"
        assert "Chase" in [b.name for b in banks], f"banks = {banks}"
        assert "Bank of America" in [b.name for b in banks], f"banks = {banks}"
        assert "https://www.bankofamerica.com/" in [b.url for b in banks], f"banks = {banks}"
        assert "https://www.chase.com/" in [b.url for b in banks], f"banks = {banks}"

        assert db.get_bank(0xDEADBEEF) is None

        db.close()


def test_account_type():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/")
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

        chase = db.create_bank("Chase", "https://www.chase.com/")
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

        boa = db.get_bank(boa_id)
        boa_account_types = db.get_bank_account_types(boa.id)
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

        chase = db.get_bank(chase_id)
        chase_account_types = db.get_bank_account_types(chase.id)
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
        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/")
        boa_cc = db.create_account_type(boa.id, "Customized Cash Rewards", TypeOfAccount.CRED)
        boa_check = db.create_account_type(boa.id, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking")
        chase = db.create_bank("Chase", "https://www.chase.com/")
        chase_cc = db.create_account_type(chase.id, "Amazon Rewards", TypeOfAccount.CRED)
        chase_savings = db.create_account_type(chase.id, "Chase Savings", TypeOfAccount.SAVE)

        assert db.user.count() == 2, "users = {db.user.count()}"
        assert db.count_banks() == 2
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

        banks = db.get_banks()
        assert set(b.type for b in banks) == {TypeOfBank.BANK}
        assert "Chase" in [b.name for b in banks]
        assert "Bank of America" in [b.name for b in banks]
        assert "https://www.bankofamerica.com/" in [b.url for b in banks]
        assert "https://www.chase.com/" in [b.url for b in banks]
        boa_id = [b.id for b in banks if b.name == "Bank of America"][0]
        chase_id = [b.id for b in banks if b.name == "Chase"][0]

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test2.sqlite3")

        boa = db.get_bank(boa_id)
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK
        boa_account_types = db.get_bank_account_types(boa.id)
        boa_cc = [t for t in boa_account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa_account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa_account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank_id == boa.id
        assert boa_check.bank_id == boa.id

        chase = db.get_bank(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK
        chase_account_types = db.get_bank_account_types(chase.id)
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
        banks = db.get_banks()

        boa = [b for b in banks if b.name == "Bank of America"][0]
        assert boa.id is not None
        assert boa.name == "Bank of America"
        assert boa.url == "https://www.bankofamerica.com/"
        assert boa.type == TypeOfBank.BANK
        boa_account_types = db.get_bank_account_types(boa.id)
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
        chase_account_types = db.get_bank_account_types(chase.id)
        chase_cc = [t for t in chase_account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase_account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase_account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank_id == chase.id
        assert chase_cc.bank_id == chase.id


if __name__ == "__main__":
    test_user()
    test_bank()
    test_account_type()
    test_serialize()

