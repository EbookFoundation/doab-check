from django.contrib import admin

# Register your models here.

from . import models 

admin.site.register(models.Item)
admin.site.register(models.Link)
admin.site.register(models.Timestamp)
admin.site.register(models.Record)
admin.site.register(models.LinkRel)
admin.site.register(models.Check)
