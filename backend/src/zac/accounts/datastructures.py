import itertools
from dataclasses import dataclass, field
from typing import List, Optional, Set

from django.db.models import F
from django.utils.functional import cached_property

from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

VA_ORDER = {
    value: VertrouwelijkheidsAanduidingen.get_choice(value).order
    for value, _ in VertrouwelijkheidsAanduidingen.choices
}


@dataclass
class ZaaktypeCollection:
    catalogus: str
    identificaties: List[str]

    @cached_property
    def _all_zaaktypen(self) -> List[ZaakType]:
        from zac.core.services import get_zaaktypen

        if not self.catalogus:
            return []

        _zaaktypen = get_zaaktypen(catalogus=self.catalogus)
        if not self.identificaties:
            return _zaaktypen

        return [x for x in _zaaktypen if x.identificatie in self.identificaties]

    def get_all(self) -> List[ZaakType]:
        return self._all_zaaktypen

    def get_for_presentation(self) -> List[ZaakType]:
        zaaktypen = []
        seen = set()
        for zaaktype in self._all_zaaktypen:
            if zaaktype.identificatie in seen:
                continue
            zaaktypen.append(zaaktype)
            seen.add(zaaktype.identificatie)

        return zaaktypen


@dataclass
class ZaaktypePermission:
    permission: str
    catalogus: str
    identificatie: str
    max_va: str
    oo: Optional[str] = None

    @property
    def zaaktypen(self) -> List[ZaakType]:
        from zac.core.services import get_zaaktypen

        if not hasattr(self, "_zaaktypen"):
            zts = get_zaaktypen(catalogus=self.catalogus)
            self._zaaktypen = [
                zt for zt in zts if zt.identificatie == self.identificatie
            ]
        return self._zaaktypen

    @zaaktypen.setter
    def zaaktypen(self, zaaktypen):
        self._zaaktypen = zaaktypen

    def contains(self, url: str) -> bool:
        return any(zaaktype.url == url for zaaktype in self.zaaktypen)

    def test_va(self, other_va: str) -> bool:
        va_nr = VA_ORDER[self.max_va]
        other_va_nr = VA_ORDER[other_va]
        return va_nr >= other_va_nr


class ZaakPermissionCollection:
    def __init__(self, perms: List[ZaaktypePermission]):
        self._perms = perms

        # build an index on permission
        self._permissions = {}
        for perm in sorted(self._perms, key=lambda perm: perm.permission):
            for perm_key, _perms in itertools.groupby(
                self._perms, key=lambda perm: perm.permission
            ):
                self._permissions[perm_key] = list(_perms)

    def __iter__(self):
        return iter(self._perms)

    @classmethod
    def for_user(cls, user):
        """
        Query the database for the permissions for a user.

        Factory method to create the permissions collection to test a user's
        permissions.
        """
        from .models import PermissionSet

        def group_key(zaaktype: ZaakType) -> str:
            return zaaktype.identificatie

        _zt_perms = {}
        _zt_objects = {}

        perm_sets = PermissionSet.objects.filter(
            authorizationprofile__user=user
        ).annotate(oo=F("authorizationprofile__oo__slug"))
        for perm_set in perm_sets:
            for perm_key in perm_set.permissions:
                # group by identificatie
                zaaktypen = sorted(perm_set.zaaktypen.get_all(), key=group_key)
                for identificatie, _zaaktypen in itertools.groupby(
                    zaaktypen, key=group_key
                ):
                    zt_perm_key = (
                        perm_key,
                        perm_set.catalogus,
                        identificatie,
                        perm_set.oo,
                    )

                    # if permission not set yet -> store it in mapping
                    if zt_perm_key not in _zt_perms:
                        zaaktype_permission = ZaaktypePermission(
                            permission=perm_key,
                            catalogus=perm_set.catalogus,
                            identificatie=identificatie,
                            max_va=perm_set.max_va,
                            oo=perm_set.oo,  # None or slug
                        )
                        _zt_perms[zt_perm_key] = zaaktype_permission
                    # otherwise, retrieve it so we can update it in subsequent checks
                    # _if_ needed
                    else:
                        zaaktype_permission = _zt_perms[zt_perm_key]

                    # track the actual zaaktype objects
                    # TOOD: this can probably be lifted up in the loops
                    _zt_objects[(perm_set.catalogus, identificatie)] = list(_zaaktypen)

                    # check if the max_va of this perm_set grants more access than what
                    # is currently known
                    current_order = VA_ORDER[zaaktype_permission.max_va]
                    perm_order = VA_ORDER[perm_set.max_va]
                    if perm_order > current_order:
                        zaaktype_permission.max_va = perm_set.max_va

        zt_perms = list(_zt_perms.values())

        for zt_perm in zt_perms:
            _zaaktypen = _zt_objects.get((zt_perm.catalogus, zt_perm.identificatie))
            if not _zaaktypen:
                continue
            zt_perm.zaaktypen = _zaaktypen

        return cls(zt_perms)

    def contains(
        self, permission: str, zaaktype: str, vertrouwelijkheidaanduiding: str
    ):
        # user does not have permission at all
        if permission not in self._permissions:
            return False

        # filter out permission objects that do not apply (different permission) or
        # already are limited in VA
        _relevant_perms = [
            perm
            for perm in self._permissions[permission]
            if perm.test_va(vertrouwelijkheidaanduiding)
        ]
        if not _relevant_perms:
            return False

        return any(perm.contains(zaaktype) for perm in _relevant_perms)

    @property
    def zaaktype_urls(self) -> Set[str]:
        if not self._perms:
            return []

        urls = set()
        for perm in self:
            for zaaktype in perm.zaaktypen:
                urls.add(zaaktype.url)
        return urls