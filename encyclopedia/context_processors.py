from .data import ARTICLES_BY_SLUG
from .preferences import get_recent_slugs, get_theme


def reader_preferences(request):
    return {
        'theme': get_theme(request),
        'recent_articles': [ARTICLES_BY_SLUG[s] for s in get_recent_slugs(request)],
    }
