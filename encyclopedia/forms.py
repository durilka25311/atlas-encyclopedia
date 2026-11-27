from django import forms

from .data import CATEGORIES

THEME_CHOICES = [('light', 'Светлая'), ('dark', 'Тёмная')]


class SearchForm(forms.Form):
    q = forms.CharField(
        label='Что вам интересно?', required=False, max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Планеты, океаны, открытия…',
            'type': 'search', 'autocomplete': 'off',
        }),
    )
    category = forms.ChoiceField(
        required=False, label='Раздел',
        choices=[('', 'Все темы')] + [(c['slug'], c['title']) for c in CATEGORIES],
    )


class ThemeForm(forms.Form):
    theme = forms.ChoiceField(
        label='Оформление страницы', choices=THEME_CHOICES,
        widget=forms.RadioSelect,
    )
    next = forms.CharField(required=False, max_length=2048, widget=forms.HiddenInput)
