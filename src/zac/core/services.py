import asyncio
import hashlib
import logging
from typing import Dict, List

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

import aiohttp
from nlx_url_rewriter.rewriter import Rewriter
from zgw.models import Document, Eigenschap, InformatieObjectType, StatusType, Zaak
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.zaken import Status
from zgw_consumers.client import get_client_class
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from .utils import get_paginated_results

logger = logging.getLogger(__name__)


def _client_from_url(url: str):
    # build the client
    Client = get_client_class()
    client = Client.from_url(url)

    base_urls = [client.base_url]
    Rewriter().backwards(base_urls)
    service = Service.objects.get(api_root=base_urls[0])

    return service.build_client()


def _client_from_object(obj):
    return _client_from_url(obj.url)


def _get_zaaktypes() -> List[Dict]:
    """
    Read the configured zaaktypes and cache the result.
    """
    KEY = "zaaktypes"

    result = cache.get(KEY)
    if result:
        logger.debug("Zaaktypes cache hit")
        return result

    result = []

    ztcs = Service.objects.filter(api_type=APITypes.ztc)
    for ztc in ztcs:
        client = ztc.build_client()
        result += get_paginated_results(client, "zaaktype")

    cache.set(KEY, result, 60 * 60)
    return result


def get_zaaktypes() -> List[ZaakType]:
    zaaktypes_raw = _get_zaaktypes()
    zaaktypes = factory(ZaakType, zaaktypes_raw)
    return zaaktypes


def fetch_zaaktype(url: str) -> ZaakType:
    key = f"zaaktype:{url}"

    result = cache.get(key)
    if result:
        logger.debug("Cache hit for zaaktype %s", url)
    else:
        client = _client_from_url(url)
        result = client.retrieve("zaaktype", url=url)
        cache.set(key, result, 60 * 24)

    return factory(ZaakType, result)


def get_statustypen(zaaktype: ZaakType) -> List[StatusType]:
    cache_key = f"zt:statustypen:{zaaktype.url}"
    result = cache.get(cache_key)
    if result is not None:
        return result

    client = _client_from_object(zaaktype)
    cat_uuid = zaaktype.catalogus.split("/")[-1]
    _statustypen = client.list(
        "statustype", catalogus_uuid=cat_uuid, zaaktype_uuid=zaaktype.uuid
    )["results"]
    statustypen = [StatusType.from_raw(raw) for raw in _statustypen]

    cache.set(cache_key, statustypen, 60 * 30)
    return statustypen


def get_zaken(
    zaaktypen: List[str] = None, identificatie: str = "", bronorganisatie: str = "",
) -> List[Zaak]:
    """
    Fetch all zaken from the ZRCs.
    """
    query = {
        "zaaktype": zaaktypen,
        "identificatie": identificatie,
        "bronorganisatie": bronorganisatie,
    }
    if zaaktypen is None:
        zaaktypen = [zt.url for zt in get_zaaktypes()]

    zt_key = ",".join(sorted(zaaktypen))
    cache_key = hashlib.md5(
        f"zaken.{zt_key}.{identificatie}.{bronorganisatie}".encode("ascii")
    ).hexdigest()

    zaken = cache.get(cache_key)
    if zaken is not None:
        logger.debug("Zaken cache hit")
        return zaken

    zrcs = Service.objects.filter(api_type=APITypes.zrc)

    zaken = []
    for zrc in zrcs:
        client = zrc.build_client()
        _zaken = client.list("zaak", query_params=query)["results"]
        zaken += factory(Zaak, _zaken)

    # resolve zaaktype URL
    _zaaktypen = {zt.url: zt for zt in get_zaaktypes()}
    for zaak in zaken:
        if zaak.zaaktype not in _zaaktypen:
            zaaktype = fetch_zaaktype(zaak.zaaktype)
            _zaaktypen[zaak.zaaktype] = zaaktype

        zaak.zaaktype = _zaaktypen[zaak.zaaktype]

    cache.set(cache_key, zaken, 60 * 30)

    return zaken


def find_zaak(bronorganisatie: str, identificatie: str) -> Zaak:
    """
    Find the Zaak, uniquely identified by bronorganisatie & identificatie.
    """
    cache_key = f"zaak:{bronorganisatie}:{identificatie}"
    result = cache.get(cache_key)
    if result is not None:
        # TODO: when ETag is implemented, check that the cache is still up to
        # date!
        return result

    query = {"bronorganisatie": bronorganisatie, "identificatie": identificatie}

    # not in cache -> check it in all known ZRCs
    zrcs = Service.objects.filter(api_type=APITypes.zrc)
    for zrc in zrcs:
        client = zrc.build_client()
        results = client.list("zaak", query_params=query)["results"]

        if not results:
            continue

        if len(results) > 1:
            logger.warning("Found multiple Zaken for query %r", query)

        # there's only supposed to be one unique case
        result = factory(Zaak, results[0])
        break

    if result is None:
        raise ObjectDoesNotExist("Zaak object was not found in any known registrations")

    cache.set(cache_key, result, 60 * 30)
    return result


def get_statussen(zaak: Zaak) -> List[Status]:
    client = _client_from_object(zaak)

    # re-use cached objects
    zaaktype = fetch_zaaktype(zaak.zaaktype)
    statustypen = {st.url: st for st in get_statustypen(zaaktype)}

    # fetch the statusses
    _statussen = get_paginated_results(
        client, "status", query_params={"zaak": zaak.url}
    )

    statussen = factory(Status, _statussen)

    # convert URL references into objects
    for status in statussen:
        status.statustype = statustypen[status.statustype]
        status.zaak = zaak

    return sorted(statussen, key=lambda x: x.datum_status_gezet, reverse=True)


def get_eigenschappen(zaak: Zaak) -> List[Eigenschap]:
    client = _client_from_object(zaak)

    eigenschappen = client.list("zaakeigenschap", zaak_uuid=zaak.id)
    for _eigenschap in eigenschappen:
        _eigenschap["zaak"] = zaak

    return [Eigenschap.from_raw(_eigenschap) for _eigenschap in eigenschappen]


def get_statustype(url: str) -> StatusType:
    cache_key = f"statustype:{url}"
    result = cache.get(cache_key)
    if result is not None:
        # TODO: when ETag is implemented, check that the cache is still up to
        # date!
        return result

    client = _client_from_url(url)
    status_type = client.retrieve("statustype", url=url)

    result = StatusType.from_raw(status_type)
    cache.set(cache_key, result, 60 * 30)
    return result


def get_documenten(zaak: Zaak) -> List[Document]:
    logger.debug("Retrieving documents linked to zaak %r", zaak)
    rewriter = Rewriter()

    zrc_client = _client_from_object(zaak)

    # get zaakinformatieobjecten
    zaak_informatieobjecten = zrc_client.list(
        "zaakinformatieobject", query_params={"zaak": zaak.url}
    )

    # retrieve the documents themselves, in parallel
    cache_key = "zios:{}".format(
        ",".join([zio["informatieobject"] for zio in zaak_informatieobjecten])
    )
    cache_key = hashlib.md5(cache_key.encode("ascii")).hexdigest()

    logger.debug("Fetching %d documents", len(zaak_informatieobjecten))
    documenten = fetch_async(cache_key, fetch_documents, zaak_informatieobjecten)

    # FIXME!
    documenten = [doc for doc in documenten if "informatieobjecttype" in doc]

    logger.debug("Retrieving ZTC configuration for informatieobjecttypen")
    # figure out relevant ztcs
    informatieobjecttypen = {
        document["informatieobjecttype"] for document in documenten
    }

    _iot = list(informatieobjecttypen)
    rewriter.backwards(_iot)

    ztcs = Service.objects.filter(api_type=APITypes.ztc)
    relevant_ztcs = []
    for ztc in ztcs:
        if any(iot.startswith(ztc.api_root) for iot in _iot):
            relevant_ztcs.append(ztc)

    all_informatieobjecttypen = []
    for ztc in relevant_ztcs:
        client = ztc.build_client()
        results = get_paginated_results(client, "informatieobjecttype")
        all_informatieobjecttypen += [
            iot for iot in results if iot["url"] in informatieobjecttypen
        ]

    informatieobjecttypen = {
        raw["url"]: InformatieObjectType.from_raw(raw)
        for raw in all_informatieobjecttypen
    }

    for document in documenten:
        document["informatieobjecttype"] = informatieobjecttypen[
            document["informatieobjecttype"]
        ]

    return [Document.from_raw(raw) for raw in documenten]


def find_document(bronorganisatie: str, identificatie: str) -> Document:
    """
    Find the document uniquely identified by bronorganisatie and identificatie.
    """
    cache_key = f"document:{bronorganisatie}:{identificatie}"
    result = cache.get(cache_key)
    if result is not None:
        # TODO: when ETag is implemented, check that the cache is still up to
        # date!
        return result

    query = {"bronorganisatie": bronorganisatie, "identificatie": identificatie}

    # not in cache -> check it in all known ZRCs
    drcs = Service.objects.filter(api_type=APITypes.drc)
    claims = {}
    for drc in drcs:
        client = drc.build_client(**claims)
        results = client.list("enkelvoudiginformatieobject", query_params=query)

        if not results:
            continue

        if len(results) > 1:
            logger.warning("Found multiple Zaken for query %r", query)

        # there's only supposed to be one unique case
        result = Document.from_raw(results[0])
        break

    if result is None:
        raise ObjectDoesNotExist(
            "Document object was not found in any known registrations"
        )

    cache.set(cache_key, result, 60 * 30)
    return result


async def fetch(session: aiohttp.ClientSession, url: str):
    creds = _client_from_url(url).auth.credentials()
    async with session.get(url, headers=creds) as response:
        return await response.json()


# TODO: add auth
async def fetch_documents(zios: list):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for zio in zios:
            task = asyncio.ensure_future(
                fetch(session=session, url=zio["informatieobject"])
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    return responses


def fetch_async(cache_key: str, job, *args, **kwargs):
    result = cache.get(cache_key)
    if result is not None:
        return result

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = job(*args, **kwargs)
    result = loop.run_until_complete(coro)
    cache.set(cache_key, result, 30 * 60)
    return result


def get_zaak(zaak_uuid=None, zaak_url=None, zaaktypes=None) -> Zaak:
    """retrieve zaak with uuid or url"""
    zrcs = Service.objects.filter(api_type=APITypes.zrc)
    result = None

    for zrc in zrcs:
        client = zrc.build_client()
        result = client.retrieve("zaak", url=zaak_url, uuid=zaak_uuid)

        if not result:
            continue

        result = factory(Zaak, result)

    if result is None:
        raise ObjectDoesNotExist("Zaak object was not found in any known registrations")

    return result


def get_related_zaken(zaak: Zaak, zaaktypes) -> list:
    """
    return list of related zaken with selected zaaktypes
    """

    related_urls = [related["url"] for related in zaak.relevante_andere_zaken]

    zaken = []
    for url in related_urls:
        zaken.append(get_zaak(zaak_url=url, zaaktypes=zaaktypes))

    # FIXME remove string after testing
    zaken = get_zaken(zaaktypes)[:3]
    return zaken
