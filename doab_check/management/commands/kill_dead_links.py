from django.core.management.base import BaseCommand


from doab_check.models import Link
    

class Command(BaseCommand):
    help = "set live attribute for all links"

    def handle(self, **options):
        changed = 0
        for link in Link.objects.all():
            live = link.live
            link.save()
            if live != link.live:
                changed += 1

        self.stdout.write(f'changed {changed} links')

