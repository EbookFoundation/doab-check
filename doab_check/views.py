"""doab_check views
"""

from django.db.models import Count, OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Item, Link

NOPUBNAME = '*** no publisher name ***'
class HomepageView(generic.TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        codes = Link.objects.filter(recent_check__isnull=False).order_by(
            '-recent_check__return_code').values(
            'recent_check__return_code').distinct()
        num_checked = Link.objects.filter(
                recent_check__return_code__isnull=False).distinct().count()
        for code in codes:
            code['count'] = Link.objects.filter(
                recent_check__return_code=code['recent_check__return_code'],
            ).distinct().count()
            code['percent'] = '{:.2%}'.format(code['count'] / num_checked)
        return {'num_checked': num_checked, 'codes': codes}


class ProblemsView(generic.TemplateView):
    template_name = 'problems.html'

    def get_context_data(self, **kwargs):
        code = kwargs['code']
        
        problems = Link.objects.exclude(recent_check__isnull=True).filter(
            recent_check__return_code__exact=code).order_by('provider')
        providers = problems.values('provider').distinct()
        for provider in providers:
            provider['links'] = problems.filter(provider=provider['provider'])
            provider['count'] = provider['links'].count()
        return {'code': code, 'providers': providers}


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
        provider_links = Link.objects.filter(provider=prov, live=True, recent_check__isnull=False)
        provider['link_count'] = provider_links.count()
        codes = provider_links.order_by('-recent_check__return_code').values(
            'recent_check__return_code').distinct()
        for code in codes:
            code['count'] = provider_links.filter(
                recent_check__return_code=code['recent_check__return_code'],
            ).distinct().count()
        
        return {'provider': provider, 'links': provider_links, 'codes': codes}


class PublishersView(generic.TemplateView):
    template_name = 'publishers.html'

    def get_context_data(self, **kwargs):
        publishers = Item.objects.order_by('publisher_name').values('publisher_name').distinct()
        for publisher in publishers:
            publisher['item_count'] = Item.objects.filter(
                publisher_name=publisher['publisher_name'], status=1).count()
        return {'publisher_list': publishers}


class ProblemPublishersView(generic.TemplateView):
    template_name = 'probpubs.html'

    def get_context_data(self, **kwargs):
        probpubs = {}
        problinks = Link.objects.exclude(
            recent_check__isnull=True).exclude(
            recent_check__return_code__exact=200)
        for link in problinks:
            pub = link.items.filter(status=1).first().publisher_name
            probpubs[pub] = probpubs.get(pub, 0) + 1
        pubs = sorted(probpubs.items(), key=lambda x: x[0])
        def fixempty(publist):
            for k, v in publist:
                yield (NOPUBNAME if not k else k), v
        return {'pubs':  fixempty(pubs)}


class PublisherView(generic.TemplateView):
    template_name = 'publisher.html'

    def get_context_data(self, **kwargs):
        pub = kwargs['publisher']
        publisher = {'publisher': pub}
        if pub == NOPUBNAME:
            pub = ''
        publisher_items = Item.objects.filter(
            publisher_name=pub, status=1,
        )
        publisher['item_count'] = publisher_items.count()
        publisher_items = publisher_items.filter(links__recent_check__isnull=False).distinct()
        
        codes = publisher_items.order_by('-links__recent_check__return_code').values(
            'links__recent_check__return_code').distinct()
        for code in codes:
            code['count'] = Link.objects.filter(live=True,
                recent_check__return_code=code['links__recent_check__return_code'],
                items__publisher_name=pub).distinct().count()
        
        
        
        return {'publisher': publisher, 'items': publisher_items, 'codes': codes}
