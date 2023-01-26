#!/usr/bin/env python3


from financial_game.database_model import Table, Integer, Identifier, String


def test_basic():
    class User(Table):
        id = Identifier()
        name = String(50)
        count = Integer()

    assert Table.tables
    user = User(a=5,name="John")
    assert user.id is None
    assert user.name == "John"
    assert user.count is None, f"user.count = {user.count}"
    assert repr(user).startswith("User(")
    assert str(user).startswith("User(")
    description = Table.database_description()
    assert 'INTEGER' == description['User']['count'], description
    assert 'VARCHAR(50)' == description['User']['name'], description
    assert 'PRIMARY KEY' in description['User']['id'], description


def test_table_name():
    class User(Table):
        __table__='user'
        id = Identifier()
        name = String(50)

    assert Table.tables
    user = User(a=5,name="Jane")
    assert user.id is None
    assert user.name == "Jane"
    description = Table.database_description()
    assert 'user' in description, description
    assert repr(user).startswith("User(")
    assert str(user).startswith("user(")


def test_normalize():
    class User(Table):
        __table__='user'
        id = Identifier()
        name = String(50)
        def normalize(self):
            super().normalize()
            self.name = self.name.upper()
        def denormalize(self):
            value = super().denormalize()
            value['name'] = value['name'].lower()
            return value

    user = User(id=1, name="John")
    assert user.id == 1
    assert user.name == "JOHN"
    for_db = user.denormalize()
    assert for_db['name'] == 'john'


if __name__ == "__main__":
    test_basic()
    test_table_name()
    test_normalize()
