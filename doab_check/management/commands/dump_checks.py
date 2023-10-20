import csv
import datetime
import logging
import os
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

from doab_check.models import Item
    

class Command(BaseCommand):
    help = "check items in based on primary key"

    def add_arguments(self, parser):
        parser.add_argument('--outdir', nargs='?', type=str, default='', action="store", 
            help="output directory")

    def check_data(self, item):
        link_dict = {'doab': item.doab}
        for link in item.links.filter(live=True):
            link_dict['url'] = link.url
            if link.recent_check:
                link_dict['checked'] = link.recent_check.created
                link_dict['return_code'] = link.recent_check.return_code
                link_dict['content_type'] = link.recent_check.content_type
            else:
                link_dict['checked'] = ''
                link_dict['return_code'] = ''
                link_dict['content_type'] = ''
            yield(link_dict)
    
    def handle(self, outdir, **options):
        start_time = datetime.datetime.now()
        num = 0
        filepath = os.path.join(outdir, 'doab_checks.csv')
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'doab', 'url', 'checked', 'return_code', 'content_type'])
            writer.writeheader()
            for item in Item.objects.filter(status=1):
                writer.writerows(self.check_data(item))
                num += 1

        end_time = datetime.datetime.now()
        logger.info(f'wrote {num} link checks in {end_time - start_time}')
        self.stdout.write(f'wrote {num} link checks in {end_time - start_time}')

