import secrets

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .data import ARTICLES, ARTICLES_BY_SLUG, CATEGORIES
from .forms import SearchForm, ThemeForm
from .preferences import (
    RECENT_COOKIE, THEME_COOKIE, get_recent_slugs, set_preference_cookie,
)


@never_cache
@require_GET
def index(request):
    return render_catalog(request)


def render_catalog(request, theme_errors=None, status=200):
    form = SearchForm(request.GET)
    articles = ARTICLES
    query, category = '', ''
    if form.is_valid():
        query = form.cleaned_data['q']
        category = form.cleaned_data['category']
        if category:
            articles = [a for a in articles if a['category'] == category]
        if query:
            def matches(article):
                content = ' '.join([
                    article['title'], article['summary'], article['category_title'],
                    *(text for section in article['sections'] for text in section),
                ]).casefold()
                return query.casefold() in content
            articles = [a for a in articles if matches(a)]
    else:
        articles = []
    return render(request, 'encyclopedia/index.html', {
        'form': form, 'articles': articles, 'query': query, 'category': category,
        'categories': CATEGORIES, 'article_count': len(ARTICLES),
        'theme_errors': theme_errors,
        'is_filtered': bool(request.GET.get('q') or request.GET.get('category')),
    }, status=status)


@never_cache
@require_GET
def article_detail(request, slug):
    article = ARTICLES_BY_SLUG.get(slug)
    if not article:
        raise Http404('Статья не найдена')
    response = render(request, 'encyclopedia/article.html', {'article': article})
    history = [slug] + [s for s in get_recent_slugs(request) if s != slug]
    set_preference_cookie(response, request, RECENT_COOKIE, ','.join(history[:4]))
    return response


@never_cache
@require_http_methods(['GET', 'POST'])
def preferences(request):
    if request.method == 'GET':
        return redirect('encyclopedia:index')
    form = ThemeForm(request.POST)
    if request.method == 'POST' and form.is_valid():
        destination = form.cleaned_data['next']
        if not destination or not url_has_allowed_host_and_scheme(
            destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
        ):
            destination = reverse('encyclopedia:index')
        response = redirect(destination)
        set_preference_cookie(response, request, THEME_COOKIE, form.cleaned_data['theme'])
        return response
    return render_catalog(request, theme_errors=form.errors, status=400)


@never_cache
@require_GET
def random_article(request):
    return redirect('encyclopedia:article', slug=secrets.choice(ARTICLES)['slug'])
