# Атлас (Онлайн-энциклопедия)

Django-проект онлайн-энциклопедии 

## Функционал

- 8 статей в разделах: космос, природа, наука и история
- Поиск по названию и тексту статьи, фильтрация по разделам
- Страницы статей с фактами и оглавлением
- Форма переключения темы (светлая / тёмная)
- Сохранение выбранной темы и четырёх последних прочитанных статей
- Переход к случайной статье
- Тесты (`encyclopedia/tests.py`)

## Установка

```bash
git clone https://github.com/durilka25311/atlas-encyclopedia.git
cd atlas-encyclopedia

python -m venv .venv

# Активация окружения — выберите команду для своего терминала:
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (CMD)
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Открыть в браузере: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Тесты

```bash
python manage.py test
```

Тесты проверяют страницы, поиск, фильтры, формы и сохранение настроек в cookies.

## Структура

```text
atlas-encyclopedia/
├── config/                      # настройки проекта и основные URL
├── encyclopedia/                # приложение
│   ├── data.py                  # статьи и разделы в списках и словарях
│   ├── forms.py                 # формы поиска и выбора темы
│   ├── views.py                 # представления
│   ├── urls.py                  # маршруты приложения
│   ├── preferences.py           # работа с cookies
│   ├── context_processors.py    # тема и история чтения для шаблонов
│   ├── tests.py                 # тесты
│   └── templates/               # HTML-шаблоны
├── static/
│   ├── css/                     # стили
│   └── images/                  # изображения
├── .vscode/                     # настройки запуска в VS Code
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```
