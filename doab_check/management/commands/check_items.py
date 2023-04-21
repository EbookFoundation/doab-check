import datetime
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

from doab_check.check import check_link
from doab_check.models import Item

def mo_hr_now():
    now = datetime.datetime.now()
    return (now.day - 1) * 24 + now.hour
    

class Command(BaseCommand):
    help = "check items in based on primary key"

    def add_arguments(self, parser):
        parser.add_argument('--max', nargs='?', type=int, default=120, help="max checks")

    def handle(self, **options):
        max_pk = Item.objects.latest('pk').pk
        # round up to nearest 1000
        top = max_pk - (max_pk % 1000) + 1000
        start_time = datetime.datetime.now()
        max = options['max']
        n_checked = l_checked = 0
        prime = 349
        this_hr = mo_hr_now()
        logger.info(f'this_hr: {this_hr} top: {top}')
        for i in range(0, max):
            j = (i * prime + this_hr) % top 
            try:
                item = Item.objects.get(pk=j)
                for link in item.related.filter(status=1):
                    check_link(link.link)
                    l_checked += 1
                n_checked += 1
                if n_checked >= max:
                    break
            except Item.DoesNotExist:
                continue

        end_time = datetime.datetime.now()
        logger.info(f'checked {l_checked} links in {end_time - start_time}')
        self.stdout.write(f'checked {l_checked} links for {n_checked} items in {end_time - start_time}')

