
from urllib.parse import urlparse

from django.db import models
from django.urls import reverse

class Item(models.Model):
    ''' an object in DOAB'''
    # for example, oai:doab-books:20.500.12854/25932
    doab = models.CharField(max_length=40, null=False, unique=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)

    # book, chapter, etc.
    resource_type = models.CharField(max_length=20, null=True)
    
    # titles, publisher name can change
    title = models.CharField(max_length=1000, default='')
    publisher_name = models.CharField(max_length=1000, default='')
    status = models.IntegerField(default=1) # 0 if deleted

    def __str__(self):
        return self.doab.split('/')[1] if '/' in self.doab else self.doab

    @property
    def url(self):
        return f'https://directory.doabooks.org/handle/{self.doab}'

class Link(models.Model):
    ''' these are the links we're going to check '''
    url = models.URLField(max_length=1024, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    # the items reporting this link
    items = models.ManyToManyField("Item", related_name="links", db_index=True, through="LinkRel")

    # so we can set it to dead instead of deleting
    live = models.BooleanField(default=True)
    
    # derived from url so we can do sorting, etc.
    provider = models.CharField(max_length=255, default='')
    
    recent_check = models.ForeignKey("Check", null=True, related_name='checked_link',
        on_delete=models.SET_NULL)
    
    def recent_checks(self):
        return self.checks.order_by('-created')
    
    def save(self, *args, **kwargs):
        if self.url:
            netloc = urlparse(self.url).netloc.lower()
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            self.provider = netloc
        if self.id:
            live = False
            for linkrel in self.related.filter(status=1):
                live = True
                break
            self.live = live
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse("link", args=[self.id])


class Timestamp(models.Model):
    ''' timestamp of the record returned by doab. records can have multiple timestamps '''
    created = models.DateTimeField(auto_now_add=True)
    datetime =  models.DateTimeField()
    item = models.ForeignKey("Item", related_name="timestamps", null=False,
                               on_delete=models.CASCADE)
    def __str__(self):
        return f'Record for {self.record.item} on {self.datetime}'    



class LinkRel(models.Model):
    ''' association between an item and a link '''
    # might be 'cover'
    role = models.CharField(max_length=10, default='identifier')
    link = models.ForeignKey("Link", related_name='related', on_delete=models.CASCADE)
    item = models.ForeignKey("Item", related_name='related', on_delete=models.CASCADE)
    status = models.IntegerField(default=1) # 0 if deleted
    
class Check(models.Model):
    ''' The results of a link check '''
    created = models.DateTimeField(auto_now_add=True)
    link = models.ForeignKey("Link", related_name='checks', on_delete=models.CASCADE)
    return_code = models.IntegerField(db_index=True)
    content_type = models.CharField(max_length=255, null=True)
    location = models.ForeignKey("Link", related_name='redirects_from', null=True,
                                 on_delete=models.SET_NULL)
    