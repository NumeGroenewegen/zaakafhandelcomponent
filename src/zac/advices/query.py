from typing import List

from django.db import models

from zgw_consumers.api_models.base import ZGWModel


class AdviceQuerySet(models.QuerySet):
    def get_for(self, api_object: ZGWModel) -> "AdviceQuerySet":
        qs = self.select_related("user")
        return qs.filter(object_url=api_object.url)

    def set_counts(self, api_objects: List[ZGWModel], to_attr="n_advices"):
        object_urls = [obj.url for obj in api_objects]

        qs = (
            self.filter(object_url__in=object_urls)
            .values("object_url")
            .annotate(count=models.Count("id"))
        )
        counts = {result["object_url"]: result["count"] for result in qs}
        for api_object in api_objects:
            count = counts.get(api_object.url, 0)
            setattr(api_object, to_attr, count)