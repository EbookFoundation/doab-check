#!/usr/bin/env python
# encoding: utf-8

import datetime
import logging
import re

from oaipmh.client import Client
from oaipmh.error import IdDoesNotExistError, NoRecordsMatchError
from oaipmh.metadata import MetadataRegistry

import requests

from .doab_utils import doab_reader
from .models import Item, Link, Record, Timestamp

DOAB_OAIURL = 'https://directory.doabooks.org/oai/request'
DOAB_PATT = re.compile(r'oai:directory\.doabooks\.org:(.*)')

logger = logging.getLogger(__name__)

mdregistry = MetadataRegistry()
mdregistry.registerReader('oai_dc', doab_reader)
doab_client = Client(DOAB_OAIURL, mdregistry)


def unlist(alist):
    if not alist:
        return None
    return alist[0]

def getdoab(url):
    id_match = DOAB_PATT.search(url)
    if id_match:
        return f'oai:doab-books:{id_match.group(1)}'
    return False


def add_by_doab(doab_id, record=None):
    try:
        record = record if record else doab_client.getRecord(
            metadataPrefix='oai_dc',
            identifier=doab_id
        )
        if not record[1]:
            logger.error('No content in record %s', record)
            return None
        metadata = record[1].getMap()
        urls = []
        for ident in metadata.pop('identifier', []):
            if ident.find('doabooks.org') >= 0:
                # should already know the doab_id
                continue
            if ident.startswith('http'):
                urls.append(ident)
        title = unlist(metadata.pop('title', ['']))
        item_type = unlist(metadata.pop('type', []))
        timestamps = metadata.pop('timestamp', [])
        added_record = load_doab_record(
            doab_id,
            title,
            item_type,
            urls,
            timestamps,
            **metadata
        )
        return added_record
    except IdDoesNotExistError as e:
        logger.error(e)
        return None

def load_doab_record(doab_id, title, item_type, urls, timestamps, **kwargs):
    """
    create a record from doabooks.org represented by input parameters 
    """
    logger.info('load doab %s', doab_id)
    (new_item, created) = Item.objects.get_or_create(doab=doab_id)
    new_record = Record.objects.create(item=new_item)
    for timestamp in timestamps:
        (new_timestamp, created) = Timestamp.objects.get_or_create(
            datetime=timestamp,
            record=new_record)
    for url in urls:
        url = url.strip()
        (link, created) = Link.objects.get_or_create(url=url)
        link.items.add(new_item)
    return new_record
        


def load_doab_oai(from_date, until_date, limit=100):
    '''
    use oai feed to get oai updates
    '''
    start = datetime.datetime.now()
    if from_date:
        from_ = from_date
    else:
        # last 15 days
        from_ = datetime.datetime.now() - datetime.timedelta(days=15)
    num_doabs = 0
    new_doabs = 0
    lasttime = datetime.datetime(2000, 1, 1)
    try:
        for record in doab_client.listRecords(metadataPrefix='oai_dc', from_=from_,
                                              until=until_date):
            if not record[1]:
                continue
            item_type = unlist(record[1].getMap().get('type', None))
            ident = record[0].identifier()
            responsestamp = record[0].datestamp()
            lasttime = responsestamp if responsestamp > lasttime else lasttime
            doab = getdoab(ident)
            if doab:
                num_doabs += 1
                rec = add_by_doab(doab, record=record)
                if not rec:
                    logger.error('error for doab #%s', doab)
                    continue
                if lasttime > start:
                    new_doabs += 1
                title = rec.item.title
                logger.info(u'updated:\t%s\t%s', doab, title)
            if num_doabs >= limit:
                break
    except NoRecordsMatchError:
        pass
    return num_doabs, new_doabs, lasttime
