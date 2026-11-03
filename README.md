# Резюме-білдер

Локальный Django-сайт с регистрацией, SQLite, четырьмя дизайнами резюме, личным кабинетом, просмотром и редактированием сохранённых резюме. К резюме можно добавлять проекты и безопасно скачиваемые вложения портфолио.

## Запуск в Windows / PyCharm

1. Откройте папку проекта в PyCharm и выберите Python 3.10 или новее.
2. В терминале PyCharm создайте окружение и установите зависимости:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Примените миграции и при необходимости создайте администратора:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

   Миграция переводит старые ID шаблонов `creative` и `professional` на `modern` и `classic`.

4. Запустите Django:

   ```powershell
   python manage.py runserver
   ```

5. Сайт: http://127.0.0.1:8000/ . Django Admin: http://127.0.0.1:8000/admin/ .

## Production на Railway

Проєкт підготовлено до Railway: Railpack визначає Python за `requirements.txt` та `.python-version`, а `Procfile` запускає Gunicorn на Railway `$PORT`. У Railway Dashboard один раз задайте команду збірки `DEBUG=False python manage.py collectstatic --no-input`, pre-deploy команду `python manage.py migrate --noinput` і health check `/healthz/`. Статичні файли віддає WhiteNoise. Локальна розробка лишається на SQLite; production без PostgreSQL не перемикається непомітно на тимчасову SQLite.

1. Надішліть проєкт у власний GitHub-репозиторій, потім у Railway створіть **New Project → Deploy from GitHub Repo** і виберіть цей репозиторій. Push автоматично не виконується.
2. У Railway додайте PostgreSQL через **New → Database → PostgreSQL**. У змінних Django-сервісу створіть `DATABASE_URL` як посилання `${{Postgres.DATABASE_URL}}` (ім’я `Postgres` замініть на фактичну назву сервісу бази). Код також підтримує Railway `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, якщо ви прив’яжете їх до web-сервісу.
3. Створіть постійний **Volume**, прив’яжіть до web-сервісу та встановіть mount path `/app/media`. Railway передасть `RAILWAY_VOLUME_MOUNT_PATH`; він використовується як `MEDIA_ROOT`. Перевірка `/healthz/` не пройде, якщо volume не підключений. Аватари віддаються з цього сховища, а вкладення портфоліо залишаються за авторизованим download-обробником.
4. У **Settings → Networking** натисніть **Generate Domain**. Railway задає `RAILWAY_PUBLIC_DOMAIN`; з нього автоматично формуються дозволений host, CSRF origin і HTTPS-посилання підтвердження email. Для власного домену додайте його в `ALLOWED_HOSTS` (тільки домен, без схеми) та `CSRF_TRUSTED_ORIGINS` (повний `https://...`).
5. У **Variables** задайте `SECRET_KEY` (випадковий секрет; створіть локально командою знизу), `DEBUG=False`, `EMAIL_HOST_USER`, Gmail App Password у `EMAIL_HOST_PASSWORD`, і цей самий поштовий акаунт у `DEFAULT_FROM_EMAIL`. SMTP host/port/TLS уже мають Gmail defaults. Не вставляйте ці секрети в GitHub і не надсилайте їх у чат.
6. Після першого deployment перевірте `/healthz/`, реальне отримання листа активації, повторну відправку, завантаження аватара/вкладення та PDF. SMTP не можна підтвердити без справжніх поштових реквізитів.

Секрет для Railway можна створити локально без публікації в репозиторії:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Для production потрібні активна підписка/кредити Railway. Поточний Hobby має $5 мінімального місячного usage з $5 кредиту, а Free має $1/місяць після пробного періоду; ресурси тарифікуються за фактичним використанням. Обсяг volume у плані Hobby включає до 5 GB. Актуальні тарифи й ціни окремих ресурсів перевіряйте перед створенням сервісів у [Railway Pricing](https://railway.com/pricing). Railway volume не є спільним сховищем для кількох реплік і має бути резервно скопійований. Для цього застосунку почніть з однієї web-репліки; масштабування потребуватиме object storage для media-файлів.

`render.yaml` залишено як наявну конфігурацію для Render. Для нового Railway-сервісу використовується `Procfile` і команди з кроку вище; `railway.toml` не застосовується до нових сервісів у поточній системі Railway.

## Работа с резюме

- В каталоге выберите Classic, Modern, Minimal или Developer.
- После сохранения откроется приватный просмотр готового резюме. Из него можно перейти к редактированию или печати в PDF.
- В личном кабинете доступны собственные сохранённые резюме.
- В режиме редактирования добавляйте проекты, ссылки на репозиторий и демо, а также до пяти вложений за отправку.
- Поддерживаются PDF, PNG, JPG/JPEG, WEBP, TXT, MD и ZIP; каждый файл ограничен 10 МБ. Сервер проверяет расширение и сигнатуру содержимого. SVG и исполняемые файлы запрещены; ZIP не распаковываются и не запускаются.
- Вложения хранятся в `media/portfolio/` и скачиваются через защищённый Django-обработчик, проверяющий владельца резюме. Файлы не публикуются напрямую через `MEDIA_URL`.

## Проверка

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts
```

Тесты покрывают регистрацию и вход, все четыре оформления, сохранение и редактирование, проекты и несколько вложений, запрет исполняемых файлов и ограничения доступа между пользователями.

## Структура

```text
accounts/                 модели, формы, обработчики, валидаторы и тесты
accounts/migrations/      SQLite-схема и перенос старых ID шаблонов
resume_builder/           настройки и маршруты Django
templates/                главная, формы, просмотр и четыре темы резюме
static/resume/            стили и JavaScript
media/                    локальные файлы портфолио
outputs/                  самостоятельная HTML/CSS/JS-версия макета
```

Настройки DEBUG и секретного ключа подходят только для локальной разработки. Перед размещением сайта отдельно настройте production-секреты, `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS и приватное хранилище файлов.
