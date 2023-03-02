import datetime
from django.core.management.base import BaseCommand

from doab_check.check import check_link
from doab_check.models import Link

class Command(BaseCommand):
    help = "check links in rando. order"

    def add_arguments(self, parser):
        parser.add_argument('--max', nargs='?', type=int, default=1000, help="max checks")

    def handle(self, **options):
        max = options['max']
        n_checked = 0
        for link in Link.objects.all().order_by('?'):
            check_link(link)
            n_checked += 1
            if n_checked >= max:
                break
        self.stdout.write(f'checked {n_checked} links')
