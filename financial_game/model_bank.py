#!/usr/bin/env python3

""" The Bank model data
"""


import enum


from financial_game.table import Table, Identifier, String, Enum, ForeignKey


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
