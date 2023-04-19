from django.test import TestCase
from django.test.client import Client

from .doab_oai import add_by_doab, doab_client
from .models import Item

class PageTests(TestCase):
    fixtures = ['testdata.json',]

    def setUp(self):
        self.client = Client()

    def test_pages(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/publishers/")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/publishers/Universidad%20Nacional%20de%20La%20Plata.%20Facultad%20de%20Humanidades%20y%20Ciencias%20de%20la%20Educación")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/providers/")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/providers/elibrary.duncker-humblot.com/")
        self.assertEqual(r.status_code, 200)


sample_doab = 'oai:doab-books:20.500.12854/25850'
class HarvestTests(TestCase):
    def test_add(self):
        add_by_doab(sample_doab)
        item = Item.objects.get(doab=sample_doab)
        self.assertTrue('Sieveking' in item.title)
        urls = []
        for linkrel in item.related.filter(status=1):
            urls.append(linkrel.link.url)
        self.assertTrue('http://library.oapen.org/handle/20.500.12657/27590' in urls)

        # tweak the record to make it a delete record
        record = doab_client.getRecord(
                metadataPrefix='oai_dc',
                identifier=sample_doab
            )
        record[0]._deleted = True
        add_by_doab(sample_doab, record=record)
        item = Item.objects.get(doab=sample_doab)
        self.assertTrue(item.status == 0)
        self.assertTrue(item.related.filter(status=1).count() == 0)
    
    
    
