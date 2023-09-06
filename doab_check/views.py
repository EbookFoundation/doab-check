"""doab_check views
"""

from django.db.models import Count, F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Item, Link

NOPUBNAME = '*** no publisher name ***'
class HomepageView(generic.TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        active_links = Link.objects.filter(recent_check__isnull=False).only(
            'recent_check').order_by('-recent_check__return_code').distinct()
        codes = active_links.values(
            'recent_check__return_code').distinct()
        num_checked = active_links.count()
        for code in codes:
            code['count'] = active_links.filter(
                recent_check__return_code=code['recent_check__return_code'],
            ).count()
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
        providers = Link.objects.order_by('provider').filter(live=True, recent_check__isnull=False,
            ).values('provider').distinct().annotate(Count('provider'))
        return {'provider_list': providers}


class ProviderView(generic.TemplateView):
    template_name = 'provider.html'

    def get_context_data(self, **kwargs):
        prov = kwargs['provider']
        provider = {'provider': prov}
        provider_links = Link.objects.filter(provider=prov, live=True, recent_check__isnull=False)
        provider['link_count'] = provider_links.count()
        codes = provider_links.order_by('-recent_check__return_code').values(
            'recent_check__return_code').distinct().annotate(Count('recent_check__return_code'))
        for code in codes:
            code['links'] = provider_links.filter(live=True,
                recent_check__return_code=code['recent_check__return_code'],
            ).order_by('items__title').annotate(title=F('items__title'))
            code['links'] = code['links'][:1000]
        
        return {'provider': provider, 
                'links': provider_links.order_by('-recent_check__return_code'),
                'codes': codes}

class LinkView(generic.TemplateView):
    template_name = 'link.html'

    def get_context_data(self, **kwargs):
        link_id = int(kwargs['link_id'])
        link = get_object_or_404(Link, id=link_id)
        
        return {'link': link}


class PublishersView(generic.TemplateView):
    template_name = 'publishers.html'

    def get_context_data(self, **kwargs):
        items = Item.objects.filter(status=1)
        publishers = items.order_by('publisher_name').values(
            'publisher_name').distinct().annotate(Count('publisher_name'))
        return {'publisher_list': publishers}


class ProblemPublishersView(generic.TemplateView):
    template_name = 'probpubs.html'

    def get_context_data(self, **kwargs):
        problinks = Link.objects.filter(live=True, recent_check__isnull=False).exclude(
            recent_check__return_code__exact=200)
        pubnames = problinks.order_by('items__publisher_name').values(
            'items__publisher_name').distinct().annotate(Count('items__publisher_name'))
        return {'pubs':  pubnames}

        
class PublisherView(generic.TemplateView):
    template_name = 'publisherlinks.html'

    def get_context_data(self, **kwargs):
        pub = kwargs['publisher']
        publisher = {'publisher': pub}
        if pub == NOPUBNAME:
            pub = ''
        publisher_links = Link.objects.filter(
            items__publisher_name=pub, items__status=1, recent_check__isnull=False
        )
        link_count = publisher_links.distinct().count()

        codes = publisher_links.order_by('-recent_check__return_code').values(
            'recent_check__return_code').distinct()
        for code in codes:
            code['links'] = publisher_links.filter(live=True,
                recent_check__return_code=code['recent_check__return_code'],
            ).order_by('items__title')
            code['count'] = code['links'].count()
        
        return {'codes': codes, 'publisher': pub, 'count': link_count}

