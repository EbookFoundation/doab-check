#!/usr/bin/env python
# encoding: utf-8

import datetime
import logging
import re

import pytz
from dateutil.parser import isoparse
from dateutil.utils import default_tzinfo

from oaipmh.client import Client
from oaipmh.error import IdDoesNotExistError, NoRecordsMatchError
from oaipmh.metadata import MetadataRegistry

import requests

from .doab_utils import doab_reader
from .models import Item, Link, Timestamp

DOAB_OAIURL = 'https://directory.doabooks.org/oai/request'
DOAB_PATT = re.compile(r'oai:(directory\.doabooks\.org|doab-books):(.*)')

logger = logging.getLogger(__name__)

mdregistry = MetadataRegistry()
mdregistry.registerReader('oai_dc', doab_reader)
doab_client = Client(DOAB_OAIURL, mdregistry)


def unlist(alist):
    if not alist:
        return None
    return alist[0]

def getdoab(url, new_ns=False):
    id_match = DOAB_PATT.search(url)
    if id_match:
        if new_ns:
            return f'oai:directory.doabooks.org:{id_match.group(2)}'
        return f'oai:doab-books:{id_match.group(2)}'
    return False


def add_by_doab(doab_id, record=None):
    try:
        record = record if record else doab_client.getRecord(
            metadataPrefix='oai_dc',
            identifier=getdoab(doab_id, new_ns=True)
        )
        if record[0].isDeleted() or not record[1]:
            logger.warning('record %s has no content or is deleted', record)
            return set_deleted(record)
        metadata = record[1].getMap()
        urls = []
        for ident in metadata.pop('identifier', []):
            if ident.find('doabooks.org') >= 0:
                # should already know the doab_id
                continue
            if ident.startswith('http'):
                urls.append(ident)
        title = unlist(metadata.pop('title', ['']))
        publisher_name = unlist(metadata.pop('publisher', ['']))
        item_type = unlist(metadata.pop('type', []))
        timestamps = metadata.pop('timestamp', [])
        added_item = load_doab_record(
            doab_id,
            title,
            publisher_name if publisher_name else '',
            item_type,
            urls,
            timestamps,
            **metadata
        )
        return added_item
    except IdDoesNotExistError as e:
        logger.error(e)
        return None

def load_doab_record(doab_id, title, publisher_name, item_type, urls, timestamps, **kwargs):
    """
    create a record from doabooks.org represented by input parameters 
    """
    logger.info('load doab %s', doab_id)
    (new_item, created) = Item.objects.get_or_create(doab=doab_id)
    new_item.title = title
    new_item.publisher_name = publisher_name if publisher_name else ''
    new_item.resource_type = item_type
    new_item.save()
    for timestamp in timestamps:
        timestamp = default_tzinfo(isoparse(timestamp), pytz.UTC)
        (new_timestamp, created) = Timestamp.objects.get_or_create(
            datetime=timestamp,
            item=new_item)
    for url in urls:
        url = url.strip()
        (link, created) = Link.objects.get_or_create(url=url)
        link.items.add(new_item)
    for linkrel in new_item.related.filter(role='identifier'):
        if linkrel.link.url in urls:
            linkrel.status = 1
        else:
            linkrel.status = 0
    return new_item
        

def set_deleted(record):
    if record[0].isDeleted():
        ident = record[0].identifier()
        doab = getdoab(ident)
        try:
            item = Item.objects.get(doab=doab)
            item.status = 0
            item.save()
            for linkrel in item.related.all():
                linkrel.status = 0
                linkrel.save()
            return item
        except Item.DoesNotExist:
            logger.warning(f'no item {doab}')
            return None
    

def load_doab_oai(from_date, until_date, limit=100):
    '''
    use oai feed to get oai updates
    '''
    start = datetime.datetime.now(pytz.UTC)
    if from_date:
        from_ = from_date
    else:
        # last 15 days
        from_ = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=15)
    num_doabs = 0
    new_doabs = 0
    lasttime = datetime.datetime(2000, 1, 1)
    try:
        for record in doab_client.listRecords(metadataPrefix='oai_dc', from_=from_,
                                              until=until_date):
            if not record[1]:
                # probably a deleted record
                set_deleted(record)
                continue
            item_type = unlist(record[1].getMap().get('type', None))
            ident = record[0].identifier()
            responsestamp = record[0].datestamp()
            lasttime = responsestamp if responsestamp > lasttime else lasttime
            doab = getdoab(ident)
            if doab:
                num_doabs += 1
                item = add_by_doab(doab, record=record)
                if not item:
                    logger.error('error for doab #%s', doab)
                    continue
                if item.created > start:
                    new_doabs += 1
                title = item.title
                logger.info(u'updated:\t%s\t%s', doab, title)
            if num_doabs >= limit:
                break
    except NoRecordsMatchError:
        pass
    return num_doabs, new_doabs, lasttime
