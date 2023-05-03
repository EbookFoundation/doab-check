from django.contrib import admin
from django.utils.safestring import mark_safe

# Register your models here.

from . import models
from .check import check_link


@admin.register(models.Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ('link_url', 'return_code', 'content_type')
    date_hierarchy = 'created'
    search_fields = ['return_code']
    ordering = ('created', 'return_code', 'content_type')
    readonly_fields = ('link_url', 'return_code', 'content_type', 'link', 'location')
    def link_url(self, obj):
        return mark_safe(f'<a href="/admin/doab_check/link/{obj.link.id}/">{obj.link.url}</a>')

@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (str, 'title', 'resource_type', 'status')
    date_hierarchy = 'created'
    search_fields = ['title']


@admin.register(models.Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'provider')
    date_hierarchy = 'created'
    search_fields = ['url']
    exclude = ['url']
    readonly_fields = ('link_display', 'provider')
    actions = ['recheck']
    
    @admin.action(description="Recheck the links")
    def recheck(self, request, queryset):
        for link in queryset:
            check_link(link)

    def link_display(self, obj):
        return mark_safe(f'<a href="{obj.url}">{obj.url}</a>')
    

@admin.register(models.LinkRel)
class LinkRelAdmin(admin.ModelAdmin):
    list_display = ('role', 'doab', 'url',)
    readonly_fields = ('item', 'link')
    search_fields = ['link__url']
    def doab(self, obj):
        return mark_safe(f'<a href="/admin/doab_check/item/{obj.item.id}/">{obj.item}</a>')
    def url(self, obj):
        return mark_safe(f'<a href="/admin/doab_check/link/{obj.link.id}/">{obj.link.url}</a>')



