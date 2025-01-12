import abc
import datetime
import re

UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

UnknownState = object()


class ValidationErrors(Exception):
    def __init__(self, message, errors: dict[str, ValueError]):
        self.message = message
        self.errors = errors

    def __str__(self):
        errors = "\n  ".join([f"{k}: {error}" for k, error in self.errors.items()])
        return f"{self.message}.\n Errors list: \n  {errors}"


class BaseField(abc.ABC):
    def __init__(self, required: bool = True, nullable: bool = False):
        self.required = required
        self.nullable = nullable
        self.field_name = None

        super().__init__()

    @property
    def __instance_field_name(self):
        return f"_{self.field_name}"

    def __get__(self, instance, owner):
        if hasattr(instance, self.__instance_field_name):
            return getattr(instance, self.__instance_field_name)

        return None

    def __set__(self, instance, value):
        self.pre_validate(value)
        self.validate(value)
        setattr(instance, self.__instance_field_name, self.prepare(value))

    def pre_validate(self, value):
        if value == UnknownState and self.required:
            raise ValueError("Field value is required")
        if not self.nullable and value is None:
            raise ValueError("Field value value should not be a null")

    def prepare(self, value):
        if value == UnknownState:
            return None

        return value

    @abc.abstractmethod
    def validate(self, value):
        pass

    def __delete__(self, instance):
        if not hasattr(instance, self.__instance_field_name):
            return

        delattr(instance, self.__instance_field_name)


class CharField(BaseField):
    def validate(self, value):
        if not value or value == UnknownState:
            return
        if not isinstance(value, str):
            raise ValueError("Field value should be string")


class EmailField(BaseField):
    def validate(self, value):
        if not value or value == UnknownState:
            return

        if not isinstance(value, str) or "@" not in value:
            raise ValueError("Please provide valid email")


class PhoneField(BaseField):
    def prepare(self, value):
        return str(value)

    def validate(self, value):
        if not value or value == UnknownState:
            return

        if not re.match(r"7\d{10}", str(value)):
            raise ValueError("Please provide valid phone number")


class DateField(BaseField):
    def prepare(self, value):
        if not value or value == UnknownState:
            return None

        return datetime.datetime.strptime(value, "%d.%m.%Y").date()

    def validate(self, value):
        if not value or value == UnknownState:
            return
        try:
            _ = self.prepare(value)
        except (ValueError, TypeError):
            raise ValueError("Please provide valid date")


class BirthDayField(DateField):
    def validate(self, value):
        if not value or value == UnknownState:
            return

        try:
            birth_day = self.prepare(value)
        except (ValueError, TypeError):
            raise ValueError("Please provide valid date")

        today = datetime.date.today()

        if birth_day > today:
            raise ValueError("Date should be in tha past")

        if (today - birth_day).days / 365.25 > 70:
            raise ValueError("You are too old for this")


class GenderField(BaseField):
    def validate(self, value):
        if not value or value == UnknownState:
            return

        if not isinstance(value, int) or value not in GENDERS:
            raise ValueError(f"Gender must be one of this {GENDERS} or empty")


class ClientIDsField(BaseField):
    def validate(self, value):
        if not isinstance(value, list) or not any([isinstance(i, int) for i in value]):
            raise ValueError("ClientId`s must be list of integers")


class ArgumentsField(BaseField):
    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Arguments should be valid dict")


class ValidatableMeta(type):
    def __new__(cls, name: str, bases: tuple, dct: dict):
        new_class = super().__new__(cls, name, bases, dct)
        validatable_fields = []
        for k, v in dct.items():
            if isinstance(v, BaseField):
                v.field_name = k
                validatable_fields.append(k)

        setattr(new_class, "__validatable_fields__", validatable_fields)
        setattr(new_class, "__validation_errors__", None)
        setattr(new_class, "__is_valid__", None)
        setattr(new_class, "__has__", None)

        return new_class


class Validatable(metaclass=ValidatableMeta):
    __validatable_fields__: list[str]
    __validation_errors__: ValidationErrors
    __has__: list[str]
    __is_valid__: bool

    @property
    def has(self) -> list[str] | None:
        return self.__has__

    @property
    def is_valid(self) -> bool | None:
        return self.__is_valid__

    @property
    def validation_errors(self) -> ValidationErrors | None:
        return self.__validation_errors__

    @classmethod
    def validate(cls, data: dict):
        instance = cls()
        field_name: str

        validation_errors: dict[str, ValueError] = {}

        has_fields: list[str] = []
        for field_name in instance.__validatable_fields__:
            try:
                val = data.get(field_name, UnknownState)
                if val != UnknownState:
                    has_fields.append(field_name)
                setattr(instance, field_name, val)

            except ValueError as e:
                validation_errors[field_name] = e

        if hasattr(instance, "post_validate"):
            try:
                getattr(instance, "post_validate")()
            except ValueError as e:
                validation_errors["post_validate"] = e

        if validation_errors:
            instance.__validation_errors__ = ValidationErrors(
                "Validation errors occurred!", validation_errors
            )
            instance.__is_valid__ = False
        else:
            instance.__is_valid__ = True

        instance.__has__ = has_fields

        return instance
