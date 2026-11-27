from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from .data import ARTICLES
from .preferences import COOKIE_MAX_AGE, RECENT_COOKIE, THEME_COOKIE


class EncyclopediaTests(SimpleTestCase):
    """Статьи не требуют БД: тестируем реальные запросы и ответы Django."""

    def test_home_lists_all_articles(self):
        response = self.client.get('/')
        self.assertEqual(len(response.context['articles']), 8)
        self.assertContains(response, 'data-theme="light"')
        self.assertContains(response, '/static/css/style.css')

    def test_all_articles_render(self):
        for article in ARTICLES:
            with self.subTest(article=article['slug']):
                response = self.client.get(reverse('encyclopedia:article', args=[article['slug']]))
                self.assertContains(response, article['title'])
                self.assertContains(response, article['sections'][0][1])

    def test_search_is_case_insensitive(self):
        response = self.client.get('/', {'q': '  лУнА  '})
        self.assertEqual([a['slug'] for a in response.context['articles']], ['moon'])

    def test_search_in_article_body(self):
        response = self.client.get('/', {'q': 'оптоволоконных'})
        self.assertEqual([a['slug'] for a in response.context['articles']], ['light'])

    def test_category_filter(self):
        response = self.client.get('/', {'category': 'space'})
        self.assertEqual([a['slug'] for a in response.context['articles']], ['solar-system', 'moon'])

    def test_search_and_category_combined(self):
        response = self.client.get('/', {'category': 'nature', 'q': 'лес'})
        self.assertEqual([a['slug'] for a in response.context['articles']], ['forest'])

    def test_empty_results(self):
        response = self.client.get('/', {'q': 'несуществующийтермин'})
        self.assertContains(response, 'Пока ничего не нашлось')
        self.assertEqual(response.context['articles'], [])

    def test_invalid_search_is_displayed(self):
        for params in ({'q': 'x' * 101}, {'category': 'unknown'}):
            with self.subTest(params=params):
                response = self.client.get('/', params)
                self.assertTrue(response.context['form'].errors)
                self.assertEqual(response.context['articles'], [])

    def test_search_escapes_html(self):
        response = self.client.get('/', {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_random_article_redirects_to_existing_article(self):
        response = self.client.get('/random/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(response['Location'], [reverse('encyclopedia:article', args=[a['slug']]) for a in ARTICLES])

    def test_unknown_article_is_404(self):
        self.assertEqual(self.client.get('/article/missing/').status_code, 404)

    @override_settings(DEBUG=False)
    def test_custom_404(self):
        self.assertContains(self.client.get('/missing/'), 'Здесь пока пусто.', status_code=404)

    def test_about_page_is_removed(self):
        self.assertEqual(self.client.get('/about/').status_code, 404)
        response = self.client.get('/')
        self.assertNotContains(response, 'О проекте')
        self.assertNotContains(response, 'Настройки чтения')
        self.assertNotContains(response, 'У знаний нет')

    def test_read_only_pages_reject_post(self):
        for url in ('/', '/random/', '/article/moon/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 405)

    def test_static_assets_exist(self):
        self.assertIsNotNone(finders.find('css/style.css'))
        for filename in [a['image'] for a in ARTICLES]:
            with self.subTest(filename=filename):
                path = finders.find(f'images/{filename}')
                self.assertIsNotNone(path)
                self.assertIn(Path(path).suffix, ('.jpg', '.png', '.webp'))
                self.assertGreater(Path(path).stat().st_size, 0)


class ThemeCookieTests(SimpleTestCase):
    def test_dark_theme_is_saved_and_reused(self):
        response = self.client.post('/preferences/', {'theme': 'dark', 'next': '/article/moon/'})
        self.assertRedirects(response, '/article/moon/')
        cookie = response.cookies[THEME_COOKIE]
        self.assertEqual(cookie.value, 'dark')
        self.assertEqual(cookie['max-age'], COOKIE_MAX_AGE)
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertTrue(cookie['httponly'])
        for url in ('/', '/article/moon/'):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'data-theme="dark"')

    def test_switch_back_to_light(self):
        self.client.cookies[THEME_COOKIE] = 'dark'
        self.assertContains(self.client.post('/preferences/', {'theme': 'light'}, follow=True), 'data-theme="light"')

    def test_cookie_survives_a_new_browser_session(self):
        response = self.client.post('/preferences/', {'theme': 'dark'})
        self.assertTrue(response.cookies[THEME_COOKIE]['expires'])
        new_client = Client()
        new_client.cookies[THEME_COOKIE] = response.cookies[THEME_COOKIE].value
        self.assertContains(new_client.get('/'), 'data-theme="dark"')

    def test_invalid_cookie_falls_back_to_light(self):
        self.client.cookies[THEME_COOKIE] = 'invalid'
        self.assertContains(self.client.get('/'), 'data-theme="light"')

    def test_invalid_or_missing_theme_does_not_change_cookie(self):
        for payload in ({'theme': 'blue'}, {}):
            with self.subTest(payload=payload):
                response = self.client.post('/preferences/', payload)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn(THEME_COOKIE, response.cookies)
                self.assertTrue(response.context['theme_errors'])

    def test_get_does_not_change_theme(self):
        response = self.client.get('/preferences/', {'theme': 'dark'}, follow=True)
        self.assertNotIn(THEME_COOKIE, response.cookies)
        self.assertContains(response, 'data-theme="light"')

    def test_external_redirect_is_rejected(self):
        for target in ('https://example.org/', '//example.org/', 'javascript:alert(1)', '///example.org/'):
            with self.subTest(target=target):
                self.assertRedirects(self.client.post('/preferences/', {'theme': 'dark', 'next': target}), '/')

    def test_query_string_is_preserved(self):
        response = self.client.post('/preferences/', {'theme': 'dark', 'next': '/?category=space&q=moon'})
        self.assertEqual(response['Location'], '/?category=space&q=moon')

    def test_cookies_are_secure_on_https(self):
        response = self.client.post('/preferences/', {'theme': 'dark'}, secure=True)
        self.assertTrue(response.cookies[THEME_COOKIE]['secure'])
        self.assertTrue(self.client.get('/article/moon/', secure=True).cookies[RECENT_COOKIE]['secure'])

    def test_csrf_is_required_and_valid_token_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/preferences/', {'theme': 'dark'}).status_code, 403)
        client.get('/')
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post('/preferences/', {'theme': 'dark', 'csrfmiddlewaretoken': token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies[THEME_COOKIE].value, 'dark')

    def test_personalized_responses_are_not_cached(self):
        self.assertIn('no-store', self.client.get('/')['Cache-Control'])


class RecentArticlesTests(SimpleTestCase):
    def test_history_is_unique_and_limited_to_four_articles(self):
        for slug in ('solar-system', 'ocean', 'light', 'moon', 'forest', 'moon'):
            self.client.get(f'/article/{slug}/')
        self.assertEqual(self.client.cookies[RECENT_COOKIE].value, 'moon,forest,light,ocean')
        response = self.client.get('/')
        self.assertEqual([a['slug'] for a in response.context['recent_articles']], ['moon', 'forest', 'light', 'ocean'])
        self.assertContains(response, 'Вы недавно читали')

    def test_untrusted_history_values_are_ignored(self):
        self.client.cookies[RECENT_COOKIE] = 'missing,moon,moon,<script>,forest'
        response = self.client.get('/')
        self.assertEqual([a['slug'] for a in response.context['recent_articles']], ['moon', 'forest'])

    def test_missing_article_does_not_update_history(self):
        self.client.cookies[RECENT_COOKIE] = 'moon'
        response = self.client.get('/article/missing/')
        self.assertNotIn(RECENT_COOKIE, response.cookies)
        self.assertEqual(self.client.cookies[RECENT_COOKIE].value, 'moon')


class SoundTests(SimpleTestCase):
    def test_sound_replaces_fractals(self):
        response = self.client.get('/article/sound/')
        self.assertContains(response, 'Как появляется звук')
        self.assertContains(response, '/static/images/sound.jpg')
        self.assertEqual(self.client.get('/article/fractals/').status_code, 404)
        response = self.client.get('/', {'q': 'эхо'})
        self.assertEqual([a['slug'] for a in response.context['articles']], ['sound'])

    def test_preferences_has_no_separate_page(self):
        self.assertRedirects(self.client.get('/preferences/'), '/')
