#!/usr/bin/env python3

""" Structure for models based on database
"""


import datetime


class DatabaseType:
    """Base class for all database types"""

    def normalize(self, value):
        """convert value to usable type"""
        return value

    def denormalize(self, value):
        """convert usable type to database value"""
        return value


class Integer(DatabaseType):
    """integer"""

    def __str__(self):
        return "INTEGER"


class Identifier(DatabaseType):
    """key"""

    def __str__(self):
        return "INTEGER PRIMARY KEY"


class String(DatabaseType):
    """varchar"""

    def __init__(self, length):
        self.length = length

    def __str__(self):
        return f"VARCHAR({self.length})"


class Date(String):
    """Date or really VARCHAR"""

    def __init__(self):
        super().__init__(10)

    def normalize(self, value):
        """convert value (YYYY-MM-DD HH:MM:SS.SSS) to usable type"""
        return (
            None
            if value is None
            else datetime.datetime.strptime(value.split(" ")[0], "%Y-%m-%d")
        ).date()

    def denormalize(self, value):
        """convert usable type to database value (YYYY-MM-DD HH:MM:SS.SSS)"""
        return value.strftime("%Y-%m-%d") + " 00:00:00.000"


class Table:
    """Table model"""

    tables = {}

    @staticmethod
    def database_description():
        """Get a description that can be passed to database"""
        return {
            Table.__table_name(t): {
                f: Table.__describe(t, f) for f in Table.__fields(t)
            }
            for t in Table.tables
        }

    @staticmethod
    def __table_class(table_class_name: str) -> type:
        return Table.tables[table_class_name]

    @staticmethod
    def __is_field(name: str) -> bool:
        return not name.startswith("_") and name not in dir(Table)

    @staticmethod
    def __describe(table_class_name: str, field: str) -> str:
        return str(Table.__type(table_class_name, field))

    @staticmethod
    def __type(table_class_name: str, field: str) -> DatabaseType:
        return Table.__table_class(table_class_name).__dict__[field]

    @staticmethod
    def __fields(table_class_name: str) -> [str]:
        return [
            f for f in dir(Table.__table_class(table_class_name)) if Table.__is_field(f)
        ]

    @staticmethod
    def __table_name(table_class_name: str) -> str:
        cls = Table.__table_class(table_class_name)
        return cls.__dict__.get("__table__", table_class_name)

    def __init_subclass__(cls: type):
        super().__init_subclass__()
        fields = [f for f in dir(cls) if Table.__is_field(f)]
        assert fields, f"No fields in {cls.__name__}"
        Table.tables[cls.__name__] = cls

    def __repr__(self):
        class_name = self.__class__.__name__
        fields = Table.__fields(class_name)
        parameters = ", ".join(
            f"{f}={repr(self.__dict__.get(f, None))}" for f in fields
        )
        return f"{class_name}({parameters})"

    def __str__(self):
        class_name = self.__class__.__name__
        table_name = Table.__table_name(class_name)
        fields = Table.__fields(class_name)
        parameters = ", ".join(f"{f}={str(self.__dict__[f])}" for f in fields)
        return f"{table_name}({parameters})"

    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.normalize()

    def normalize(self):
        """Converts database types to user-friendly types"""
        for field in Table.__fields(self.__class__.__name__):
            typ = Table.__type(self.__class__.__name__, field)
            self.__dict__[field] = typ.normalize(self.__dict__.get(field, None))

    def denormalize(self) -> dict:
        """Converts usable types to database types"""
        class_name = self.__class__.__name__
        return {
            f: Table.__type(class_name, f).denormalize(self.__dict__.get(f, None))
            for f in Table.__fields(class_name)
        }
