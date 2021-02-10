"""
Provide polymorphic serializer base class.

Polymorphism happens when a resource takes a certain shape depending on the type
of the resource. Usually they have a common base type. The exact type/shape is not
statically known, but depends on the run-time values.

Note that we cannnot use https://github.com/apirobot/django-rest-polymorphic because
it builds on the django-polymorphic Model, which we don't use since our data
is retrieved from upstream APIs.

The implementation is inspired on the vng-api-common implementation:
https://github.com/VNG-Realisatie/vng-api-common/blob/master/vng_api_common/polymorphism.py

Note that the discriminator field must exist at the same depth as the mapped serializer
fields for the OpenAPI introspection. See
https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/ for
more information. As such, it's not possible to define something like:

{
    "object_type": "foo",
    "polymorphic_context": {
        <foo-specific fields>
    }
}

without explicitly wrapping this in a parent serializer, i.e. - ``polymorphic_context``
can not be a PolymorphicSerializer itself, as it requires access to the ``object_type``
in the parent scope.
"""
import warnings
from typing import Dict, Optional, Type, Union

from django.core.exceptions import ImproperlyConfigured

from rest_framework import serializers

SerializerCls = Type[serializers.Serializer]
SerializerClsOrInstance = Union[serializers.Serializer, SerializerCls]
Primitive = Union[str, int, float]


class PolymorphicSerializer(serializers.Serializer):
    # mapping of discriminator value to serializer (instance or class)
    serializer_mapping: Optional[Dict[Primitive, SerializerClsOrInstance]] = None
    # the serializer field that holds the discriminator values
    discriminator_field = "object_type"
    fallback_distriminator_value = None
    strict = True

    def __new__(cls, *args, **kwargs):
        if cls.serializer_mapping is None:
            raise ImproperlyConfigured(
                "`{cls}` is missing a `{cls}.serializer_mapping` attribute".format(
                    cls=cls.__name__
                )
            )

        if not isinstance(cls.discriminator_field, str):
            raise ImproperlyConfigured(
                "`{cls}.discriminator_field` must be a string".format(cls=cls.__name__)
            )

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serializer_mapping = self.serializer_mapping
        self.serializer_mapping = {}

        for object_type, serializer in serializer_mapping.items():
            if callable(serializer):
                serializer = serializer(*args, **kwargs)
                serializer.parent = self

            self.serializer_mapping[object_type] = serializer

    def to_representation(self, instance):
        default = super().to_representation(instance)
        serializer = self._get_serializer_from_instance(instance)
        extra = serializer.to_representation(instance)
        return {**default, **extra}

    def _get_serializer_from_instance(self, instance):
        discriminator_value = self.fields[self.discriminator_field].get_attribute(
            instance
        )

        if (
            discriminator_value not in self.serializer_mapping
            and self.fallback_distriminator_value is not None
        ):
            warnings.warn(
                f"Discriminator value {discriminator_value} missing from mapping, "
                f"falling back to {self.fallback_distriminator_value}",
                RuntimeWarning,
            )
            discriminator_value = self.fallback_distriminator_value

        try:
            return self.serializer_mapping[discriminator_value]
        except KeyError as exc:
            if self.strict:
                raise KeyError(
                    "`{cls}.serializer_mapping` is missing a corresponding serializer "
                    "for the `{value}` key".format(
                        cls=self.__class__.__name__,
                        value=discriminator_value,
                    )
                ) from exc
            else:
                return serializers.Serializer()