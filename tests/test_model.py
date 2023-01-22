#!/usr/bin/env python3

import tempfile
import os

import financial_game.model
from financial_game.model import TypeOfAccount, TypeOfBank


TEST_YAML_PATH = os.path.join(os.path.split(__file__)[0], "model.yaml")


def test_user():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.create_user("john.appleseed@apple.com", "Setec astronomy", "John", None, return_created=True)
        assert john.id is not None
        db.create_user("Jane.Doe@apple.com", "too many secrets", "Jane", john.id)

        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        assert db.count_users() == 2, "users = {db.count_users()}"
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.find_user("john.appleseed@apple.com")
        john_id = john.id
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert john.name == "John"
        assert john.password_matches("Setec astronomy")
        assert not john.password_matches("setec astronomy")
        assert not john.password_matches("too many secrets")
        assert '"John"' in repr(john)
        john.set_password("setec astronomy")

        jane = db.find_user("jane.doe@apple.com")
        jane_id = jane.id
        assert jane.name == "Jane"
        assert jane.sponsor_id == john.id, f"Jane sponsor = {jane.sponsor_id} john = {john.id}"
        assert jane.password_matches("too many secrets")
        assert not jane.password_matches("Setec astronomy")
        assert not jane.password_matches("too many Secrets")
        assert '"Jane"' in repr(jane)
        assert jane.sponsor.id == john.id
        assert len(jane.sponsored) == 0
        assert len(john.sponsored) == 1
        assert john.sponsored[0].id == jane.id

        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.get_user(john_id)
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert john.name == "John"
        assert john.password_matches("setec astronomy")
        assert not john.password_matches("Setec astronomy")

        jane = db.get_user(jane_id)
        assert jane.name == "Jane"
        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        assert jane.sponsor.id == john.id
        assert len(jane.sponsored) == 0
        assert len(john.sponsored) == 1
        assert john.sponsored[0].id == jane.id
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        users = db.get_users()
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert len(users) == 2
        user_names = [u.name for u in users]
        assert 'John' in user_names
        assert 'Jane' in user_names


def test_bank():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/", return_created=True)
        boa_id = boa.id
        assert boa.id is not None, boa
        assert boa.name == "Bank of America", boa
        assert boa.url == "https://www.bankofamerica.com/", boa
        assert boa.type == TypeOfBank.BANK, boa
        assert '"Bank of America"' in repr(boa)

        chase = db.create_bank("Chase", "https://www.chase.com/", return_created=True)
        chase_id = chase.id
        assert chase.id is not None, chase
        assert chase.name == "Chase", chase
        assert chase.url == "https://www.chase.com/", chase
        assert chase.type == TypeOfBank.BANK, chase
        assert '"Chase"' in repr(chase)

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


def test_account_type():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/", return_created=True)
        boa_id = boa.id
        assert boa.id is not None, boa

        boa_cc = db.create_account_type(boa.id, "Customized Cash Rewards", TypeOfAccount.CRED, return_created=True)
        boa_cc_id = boa_cc.id
        assert boa_cc.id is not None
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_cc.type == TypeOfAccount.CRED
        assert boa_cc.url is None
        assert boa_cc.bank.id == boa_id

        boa_check = db.create_account_type(boa.id, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking", return_created=True)
        boa_check_id = boa_check.id
        assert boa_check.id is not None
        assert boa_check.name == "Advantage Banking"
        assert boa_check.type == TypeOfAccount.CHCK
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_check.bank.id == boa_id

        chase = db.create_bank("Chase", "https://www.chase.com/", return_created=True)
        chase_id = chase.id
        assert chase.id is not None

        chase_cc = db.create_account_type(chase.id, "Amazon Rewards", TypeOfAccount.CRED, return_created=True)
        chase_cc_id = chase_cc.id
        assert chase_cc.id is not None
        assert chase_cc.name == "Amazon Rewards"
        assert chase_cc.type == TypeOfAccount.CRED
        assert chase_cc.url is None
        assert chase_cc.bank.id == chase_id

        chase_savings = db.create_account_type(chase.id, "Chase Savings", TypeOfAccount.SAVE, return_created=True)
        chase_savings_id = chase_savings.id
        assert chase_savings.id is not None
        assert chase_savings.name == "Chase Savings"
        assert chase_savings.type == TypeOfAccount.SAVE
        assert chase_savings.url is None
        assert chase_savings.bank.id == chase_id

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        boa = db.get_bank(boa_id)
        assert len(boa.account_types) == 2
        boa_cc = [t for t in boa.account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa.account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa.account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank.id == boa.id
        assert boa_check.bank.id == boa.id
        assert '"Advantage Banking"' in repr(boa_check)
        assert '"Customized Cash Rewards"' in repr(boa_cc)

        chase = db.get_bank(chase_id)
        assert len(chase.account_types) == 2
        chase_cc = [t for t in chase.account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase.account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase.account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank.id == chase.id
        assert chase_cc.bank.id == chase.id
        assert "Chase Savings" in repr(chase_savings)
        assert "Amazon Rewards" in repr(chase_cc)

        db.close()


def test_serialize():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")

        john = db.create_user("john.appleseed@apple.com", "Setec astronomy", "John", None, return_created=True)
        assert john.id is not None
        db.create_user("Jane.Doe@apple.com", "too many secrets", "Jane", john.id)
        boa = db.create_bank("Bank of America", "https://www.bankofamerica.com/", return_created=True)
        boa_cc = db.create_account_type(boa.id, "Customized Cash Rewards", TypeOfAccount.CRED, return_created=True)
        boa_check = db.create_account_type(boa.id, "Advantage Banking", TypeOfAccount.CHCK, "https://www.bankofamerica.com/checking", return_created=True)
        chase = db.create_bank("Chase", "https://www.chase.com/", return_created=True)
        chase_cc = db.create_account_type(chase.id, "Amazon Rewards", TypeOfAccount.CRED, return_created=True)
        chase_savings = db.create_account_type(chase.id, "Chase Savings", TypeOfAccount.SAVE, return_created=True)

        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert db.count_banks() == 2
        db.flush()
        serialized = db.serialize()
        db.close()

        db = financial_game.model.Database("sqlite:///" + workspace + "test2.sqlite3", serialized)

        john = db.find_user("john.appleseed@apple.com")
        assert db.count_users() == 2, "users = {db.count_users()}"
        assert john.name == "John"
        assert not john.password_matches("setec astronomy")
        assert john.password_matches("Setec astronomy")

        jane = db.find_user("jane.doe@apple.com")
        assert jane.name == "Jane"
        assert len(db.sessions()) == 1, f"sessions = {db.sessions()}"
        assert jane.sponsor_id == john.id, f"Jane sponsor = {jane.sponsor_id} john = {john.id}"
        assert jane.sponsor.id == john.id
        assert len(jane.sponsored) == 0
        assert len(john.sponsored) == 1
        assert john.sponsored[0].id == jane.id

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
        boa_cc = [t for t in boa.account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa.account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa.account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank.id == boa.id
        assert boa_check.bank.id == boa.id
        assert '"Advantage Banking"' in repr(boa_check)
        assert '"Customized Cash Rewards"' in repr(boa_cc)

        chase = db.get_bank(chase_id)
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK
        chase_cc = [t for t in chase.account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase.account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase.account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank.id == chase.id
        assert chase_cc.bank.id == chase.id
        assert "Chase Savings" in repr(chase_savings)
        assert "Amazon Rewards" in repr(chase_cc)

        db.close()
        db = financial_game.model.Database("sqlite:///" + workspace + "test3.sqlite3", TEST_YAML_PATH)

        users = db.get_users()
        assert db.count_users() == 2, "users = {db.count_users()}"
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
        boa_cc = [t for t in boa.account_types if t.type == TypeOfAccount.CRED][0]
        boa_check = [t for t in boa.account_types if t.type == TypeOfAccount.CHCK][0]
        assert set(t.type for t in boa.account_types) == {TypeOfAccount.CHCK, TypeOfAccount.CRED}
        assert boa_check.name == "Advantage Banking"
        assert boa_cc.name == "Customized Cash Rewards"
        assert boa_check.url == "https://www.bankofamerica.com/checking"
        assert boa_cc.url is None
        assert boa_cc.bank.id == boa.id
        assert boa_check.bank.id == boa.id
        assert '"Advantage Banking"' in repr(boa_check)
        assert '"Customized Cash Rewards"' in repr(boa_cc)

        chase = [b for b in banks if b.name == "Chase"][0]
        assert chase.id is not None
        assert chase.name == "Chase"
        assert chase.url == "https://www.chase.com/"
        assert chase.type == TypeOfBank.BANK
        chase_cc = [t for t in chase.account_types if t.type == TypeOfAccount.CRED][0]
        chase_savings = [t for t in chase.account_types if t.type == TypeOfAccount.SAVE][0]
        assert set(t.type for t in chase.account_types) == {TypeOfAccount.SAVE, TypeOfAccount.CRED}
        assert chase_savings.name == "Chase Savings"
        assert chase_cc.name == "Amazon Rewards"
        assert chase_savings.url is None
        assert chase_cc.url is None
        assert chase_savings.bank.id == chase.id
        assert chase_cc.bank.id == chase.id
        assert "Chase Savings" in repr(chase_savings)
        assert "Amazon Rewards" in repr(chase_cc)


if __name__ == "__main__":
    test_user()
    test_bank()
    test_account_type()
    test_serialize()

