#!/usr/bin/env python3

""" Structure for models based on database
"""


import datetime


class DatabaseType:
    """Base class for all database types"""

    def __init__(self, allow_null: bool):
        self.allow_null = allow_null

    def null_clause(self):
        """Get the NOT NULL clause"""
        return "" if self.allow_null else " NOT NULL"

    def normalize(self, value):
        """convert value to usable type"""
        return value

    def denormalize(self, value):
        """convert usable type to database value"""
        return value


class Integer(DatabaseType):
    """integer"""

    def __init__(self, allow_null: bool = True):
        super().__init__(allow_null)

    def __str__(self):
        return f"INTEGER{self.null_clause()}"


class Fixed(Integer):
    """Fixed precision number"""

    def __init__(self, precision: int, allow_null: bool = True):
        self.__precision = precision
        super().__init__(allow_null)

    def normalize(self, value):
        """convert value (100) to usable type (10.00)"""
        return float(value) / pow(10, self.__precision)

    def denormalize(self, value):
        """convert usable type (10.00) to database value (100)"""
        return int(value * pow(10, self.__precision))


class Money(Fixed):
    """Currency"""

    def __init__(self, precision: int = 2, allow_null: bool = True):
        super().__init__(precision, allow_null)


class Identifier(DatabaseType):
    """key"""

    def __init__(self):
        super().__init__(allow_null=False)

    def __str__(self):
        return "INTEGER PRIMARY KEY{self.null_clause()}"


class ForeignKey(Integer):
    """key in another table"""

    def __init__(self, table, field_name: str = "id", allow_null: bool = True):
        super().__init__(allow_null)
        self.table = table
        self.field = field_name


class String(DatabaseType):
    """varchar"""

    def __init__(self, length, allow_null: bool = True):
        self.length = length
        super().__init__(allow_null)

    def __str__(self):
        return f"VARCHAR({self.length}){self.null_clause()}"


class Enum(String):
    """enum"""

    def __init__(self, enum_type, allow_null: bool = True):
        self.enum_type = enum_type
        largest = max(len(e.name) for e in list(enum_type))
        super().__init__(length=largest, allow_null=allow_null)

    def __str__(self):
        return f"VARCHAR({self.length}){self.null_clause()}"

    def normalize(self, value):
        """convert string to enum"""
        return None if value is None else self.enum_type[value]

    def denormalize(self, value):
        """convert enum to string"""
        return None if value is None else value.name


class Date(String):
    """Date or really VARCHAR"""

    def __init__(self, allow_null: bool = True):
        super().__init__(10, allow_null)

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
    def __is_field(name: str, cls: type) -> bool:
        maybe = not name.startswith("_") and name not in dir(Table)
        return maybe and cls.__dict__[name].__class__.__name__ != "function"

    @staticmethod
    def __describe(table_class_name: str, field: str) -> str:
        return str(Table.__type(table_class_name, field))

    @staticmethod
    def __type(table_class_name: str, field: str) -> DatabaseType:
        return Table.__table_class(table_class_name).__dict__[field]

    @staticmethod
    def __fields(table_class_name: str) -> [str]:
        cls = Table.__table_class(table_class_name)
        return [f for f in dir(cls) if Table.__is_field(f, cls)]

    @staticmethod
    def __table_name(table_class_name: str) -> str:
        cls = Table.__table_class(table_class_name)
        return cls.__dict__.get("__table__", table_class_name)

    def __init_subclass__(cls: type):
        super().__init_subclass__()
        fields = [f for f in dir(cls) if Table.__is_field(f, cls)]
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
