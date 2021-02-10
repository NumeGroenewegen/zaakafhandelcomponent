from django.utils.translation import gettext_lazy as _

from rest_framework import fields, serializers

from zac.api.polymorphism import PolymorphicSerializer

from ..user_tasks import usertask_context_serializer


def get_default_field_kwargs(definition: dict):
    initial = definition["value"]
    return {
        "label": definition["label"],
        "initial": initial if initial is not None else fields.empty,
    }


def enum_field_kwargs(definition):
    base = get_default_field_kwargs(definition)
    choices = definition["enum"]
    return {**base, "choices": choices}


FIELD_TYPE_MAP = {
    "enum": (
        serializers.ChoiceField,
        enum_field_kwargs,
    ),
    "string": (
        serializers.CharField,
        get_default_field_kwargs,
    ),
    "long": (
        serializers.IntegerField,
        get_default_field_kwargs,
    ),
    "boolean": (
        serializers.BooleanField,
        get_default_field_kwargs,
    ),
    "date": (
        serializers.DateTimeField,
        get_default_field_kwargs,
    ),
}


INPUT_TYPE_MAP = {
    "enum": "enum",
    "string": "string",
    "long": "int",
    "boolean": "boolean",
    "date": "date",
}


class EnumField(serializers.ListField):
    child = serializers.ListField(
        child=serializers.CharField(),
        label=_("Possible enum choice"),
        help_text=_("First element is the value, second element is the label."),
        min_length=2,
        max_length=2,
    )


VALUE_DEFAULTS = {
    "label": _("Field value"),
    "help_text": _("Current or default value."),
    "allow_null": True,
}


class StringSerializer(serializers.Serializer):
    value = serializers.CharField(**VALUE_DEFAULTS)


class EnumSerializer(StringSerializer):
    enum = EnumField(
        label=_("Possible enum choices"),
        required=True,
    )


class IntSerializer(serializers.Serializer):
    value = serializers.IntegerField(**VALUE_DEFAULTS)


class BooleanSerializer(serializers.Serializer):
    value = serializers.BooleanField(**VALUE_DEFAULTS)


class DatetimeSerializer(serializers.Serializer):
    value = serializers.DateTimeField(**VALUE_DEFAULTS)


class FormFieldSerializer(PolymorphicSerializer):
    discriminator_field = "input_type"
    serializer_mapping = {
        "enum": EnumSerializer,
        "string": StringSerializer,
        "int": IntSerializer,
        "boolean": BooleanSerializer,
        "date": DatetimeSerializer,
    }

    name = serializers.CharField(
        label=_("Field name/identifier"),
        required=True,
    )
    label = serializers.CharField(
        label=_("Field label"),
        help_text=_(
            "Human-readable field title. Defaults to `name` property if not provided."
        ),
        required=True,
    )
    input_type = serializers.ChoiceField(
        label=_("Input data type"),
        choices=list(INPUT_TYPE_MAP.values()),
        required=True,
    )


@usertask_context_serializer
class DynamicFormSerializer(serializers.Serializer):
    form_fields = FormFieldSerializer(many=True, read_only=True)


# Write serializers


class DynamicFormWriteSerializer(serializers.Serializer):
    def on_submission(self):
        pass

    def get_process_variables(self):
        return self.validated_data