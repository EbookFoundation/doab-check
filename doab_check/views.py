"""doab_check views
"""

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Item, Link


class ProvidersView(generic.TemplateView):
    template_name = 'providers.html'

    def get_context_data(self, **kwargs):
        providers = Link.objects.order_by('provider').values('provider').distinct()
        for provider in providers:
            provider['link_count'] = Link.objects.filter(provider=provider['provider']).count()
        return {'provider_list': providers}


class ProviderView(generic.TemplateView):
    template_name = 'provider.html'

    def get_context_data(self, **kwargs):
        prov = kwargs['provider']
        provider = {'provider': prov}
        provider_links = Link.objects.filter(provider=prov, live=True)
        provider['link_count'] = provider_links.count()
        
        return {'provider': provider, 'links': provider_links}

class PublishersView(generic.TemplateView):
    template_name = 'publishers.html'

    def get_context_data(self, **kwargs):
        publishers = Item.objects.order_by('publisher_name').values('publisher_name').distinct()
        for publisher in publishers:
            publisher['item_count'] = Item.objects.filter(
                publisher_name=publisher['publisher_name']).count()
        return {'publisher_list': publishers}

class PublisherView(generic.TemplateView):
    template_name = 'publisher.html'

    def get_context_data(self, **kwargs):
        pub = kwargs['publisher']
        publisher = {'publisher': pub}
        publisher_items = Item.objects.filter(publisher_name=pub)
        publisher['link_count'] = publisher_items.count()
        
        return {'publisher': publisher, 'items': publisher_items}
