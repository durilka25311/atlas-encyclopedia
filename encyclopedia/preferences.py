from .data import ARTICLES_BY_SLUG

THEME_COOKIE = 'atlas_theme'
RECENT_COOKIE = 'atlas_recent'
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def get_theme(request):
    theme = request.COOKIES.get(THEME_COOKIE, 'light')
    return theme if theme in ('light', 'dark') else 'light'


def get_recent_slugs(request):
    """Cookie недоверенные: оставляем только известные уникальные slug."""
    slugs = request.COOKIES.get(RECENT_COOKIE, '')[:512].split(',')
    return list(dict.fromkeys(slug for slug in slugs if slug in ARTICLES_BY_SLUG))[:4]


def set_preference_cookie(response, request, name, value):
    response.set_cookie(
        name, value, max_age=COOKIE_MAX_AGE, path='/',
        httponly=True, samesite='Lax', secure=request.is_secure(),
    )
