import factory


class ActivityFactory(factory.django.DjangoModelFactory):
    zaak = factory.Faker("url")
    name = factory.Faker("bs")

    class Meta:
        model = "activities.Activity"
        # To avoid database integrity errors because of unique constraint on model
        django_get_or_create = (
            "zaak",
            "name",
        )


class EventFactory(factory.django.DjangoModelFactory):
    activity = factory.SubFactory(ActivityFactory)
    notes = factory.Faker("bs")

    class Meta:
        model = "activities.Event"
