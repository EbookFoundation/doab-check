from django.test import TestCase
from django.test.client import Client

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
