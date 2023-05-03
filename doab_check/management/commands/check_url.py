import datetime
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

from doab_check.check import check_link, type_for_url
from doab_check.models import Link

class Command(BaseCommand):
    help = "check links in rando. order"

    def add_arguments(self, parser):
        parser.add_argument('url', nargs='?', type=str, help="url to check")

    def handle(self, **options):
        url = options['url']
        try:
            link = Link.objects.get(url=url)
            check = check_link(link)
            self.stdout.write(
                f'checked {url}: type is {check.content_type}, code is {check.return_code}')
        except Link.DoesNotExist:
            code, ctype = type_for_url(url)
            self.stdout.write(
                f'checked {url}: type is  {ctype}, code is {code}')
            
            
            

