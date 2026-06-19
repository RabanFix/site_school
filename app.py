import os
import random
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify
)
from database import db
from models import Vacancy, Resume, Application
from config import config
from datetime import datetime


# ───────────────────────── helpers ──────────────────────────────

def make_sort_options(current):
    opts = [
        ('date',   'По дате'),
        ('salary', 'По зарплате'),
        ('title',  'По названию'),
    ]
    return [{'value': v, 'label': l, 'selected': v == current} for v, l in opts]


def make_category_options(current):
    cats = [
        ('all',                      'Все категории'),
        ('Курьеры и доставка',       'Курьеры и доставка'),
        ('Промоутеры',               'Промоутеры'),
        ('Помощники и стажеры',      'Помощники и стажеры'),
        ('Озеленение и благоустройство', 'Озеленение и благоустройство'),
        ('Работа в интернете',       'Работа в интернете'),
    ]
    return [{'value': v, 'label': l, 'selected': v == current} for v, l in cats]


def make_type_options(current):
    types = [
        ('',                   'Любой'),
        ('Полная занятость',   'Полная занятость'),
        ('Частичная занятость','Частичная занятость'),
        ('Совместительство',   'Совместительство'),
    ]
    return [{'value': v, 'label': l, 'selected': v == current} for v, l in types]


def make_experience_options(current=''):
    exps = [
        ('',          'Выберите...'),
        ('Без опыта', 'Без опыта'),
        ('До 1 года', 'До 1 года'),
        ('От 1 года', 'От 1 года'),
        ('От 3 лет',  'От 3 лет'),
        ('От 5 лет',  'От 5 лет'),
    ]
    return [{'value': v, 'label': l, 'selected': v == current} for v, l in exps]


def make_hero_categories(current, query):
    cats = [
        ('all',                      'Все',           'fas fa-border-all'),
        ('Курьеры и доставка',       'Курьеры',       'fas fa-bicycle'),
        ('Промоутеры',               'Промоутеры',    'fas fa-bullhorn'),
        ('Помощники и стажеры',      'Помощники',     'fas fa-hands-helping'),
        ('Озеленение и благоустройство', 'Озеленение', 'fas fa-leaf'),
    ]
    result = []
    for val, label, icon in cats:
        result.append({
            'url':    url_for('index', category=val, q=query),
            'label':  label,
            'icon':   icon,
            'active': val == current,
        })
    return result


def get_publish_form_data(vacancy=None):
    if vacancy:
        return {
            'title':        vacancy.title,
            'salary_from':  vacancy.salary_from or '',
            'salary_to':    vacancy.salary_to or '',
            'education':    vacancy.education,
            'description':  vacancy.description,
            'duties':       vacancy.duties,
            'requirements': vacancy.requirements,
            'conditions':   vacancy.conditions,
            'contact_name': vacancy.contact_name,
            'contact_phone':vacancy.contact_phone,
            'is_featured':  vacancy.is_featured,
            'is_urgent':    vacancy.is_urgent,
        }
    return {
        'title': '', 'salary_from': '', 'salary_to': '',
        'education': '', 'description': '', 'duties': '',
        'requirements': '', 'conditions': '',
        'contact_name': 'Иван Иванович',
        'contact_phone': '+7 (846) 956-47-78',
        'is_featured': False, 'is_urgent': False,
    }


COLORS = [
    'linear-gradient(135deg,#667eea,#764ba2)',
    'linear-gradient(135deg,#f093fb,#f5576c)',
    'linear-gradient(135deg,#4facfe,#00f2fe)',
    'linear-gradient(135deg,#43e97b,#38f9d7)',
    'linear-gradient(135deg,#fa709a,#fee140)',
    'linear-gradient(135deg,#a18cd1,#fbc2eb)',
]

ICONS_MAP = {
    'Курьеры и доставка':           '🚲',
    'Промоутеры':                   '📢',
    'Помощники и стажеры':          '🤝',
    'Озеленение и благоустройство': '🌱',
    'Работа в интернете':           '💻',
}


# ───────────────────────── factory ──────────────────────────────

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_data()

    @app.context_processor
    def inject_globals():
        return {
            'vacancy_count': Vacancy.query.filter_by(is_active=True).count(),
            'resume_count':  Resume.query.filter_by(is_active=True).count(),
            'current_year':  datetime.utcnow().year,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

    register_routes(app)
    return app


# Gunicorn ищет объект `app` в этом модуле (команда: gunicorn app:app)
app = create_app(os.environ.get('FLASK_CONFIG', 'default'))


# ───────────────────────── routes ───────────────────────────────

def register_routes(app):

    # ── Главная ──────────────────────────────────────────────────
    @app.route('/')
    def index():
        query    = request.args.get('q', '').strip()
        category = request.args.get('category', 'all')
        sort_by  = request.args.get('sort', 'date')
        page     = request.args.get('page', 1, type=int)

        vq = Vacancy.query.filter_by(is_active=True)
        if query:
            vq = vq.filter(
                Vacancy.title.ilike('%' + query + '%') |
                Vacancy.description.ilike('%' + query + '%')
            )
        if category and category != 'all':
            vq = vq.filter_by(category=category)
        if sort_by == 'salary':
            vq = vq.order_by(Vacancy.salary_from.desc())
        elif sort_by == 'title':
            vq = vq.order_by(Vacancy.title)
        else:
            vq = vq.order_by(Vacancy.created_at.desc())

        pagination = vq.paginate(
            page=page,
            per_page=app.config['VACANCIES_PER_PAGE'],
            error_out=False
        )
        featured = (Vacancy.query
                    .filter_by(is_active=True, is_featured=True)
                    .limit(3).all())

        return render_template(
            'index.html',
            vacancies      = pagination.items,
            pagination     = pagination,
            featured       = featured,
            query          = query,
            category       = category,
            sort_by        = sort_by,
            sort_options   = make_sort_options(sort_by),
            categories     = make_hero_categories(category, query),
        )

    # ── Все вакансии ─────────────────────────────────────────────
    @app.route('/vacancies')
    def vacancies():
        query    = request.args.get('q', '').strip()
        category = request.args.get('category', 'all')
        job_type = request.args.get('type', '')
        sal_from = request.args.get('sal_from', 0, type=int)
        sal_to   = request.args.get('sal_to',   0, type=int)
        sort_by  = request.args.get('sort', 'date')
        page     = request.args.get('page', 1, type=int)

        vq = Vacancy.query.filter_by(is_active=True)
        if query:
            vq = vq.filter(
                Vacancy.title.ilike('%' + query + '%') |
                Vacancy.description.ilike('%' + query + '%')
            )
        if category and category != 'all':
            vq = vq.filter_by(category=category)
        if job_type:
            vq = vq.filter_by(job_type=job_type)
        if sal_from:
            vq = vq.filter(Vacancy.salary_from >= sal_from)
        if sal_to:
            vq = vq.filter(Vacancy.salary_to <= sal_to)
        if sort_by == 'salary':
            vq = vq.order_by(Vacancy.salary_from.desc())
        elif sort_by == 'title':
            vq = vq.order_by(Vacancy.title)
        else:
            vq = vq.order_by(Vacancy.created_at.desc())

        pagination = vq.paginate(
            page=page,
            per_page=app.config['VACANCIES_PER_PAGE'],
            error_out=False
        )

        return render_template(
            'vacancies.html',
            vacancies        = pagination.items,
            pagination       = pagination,
            query            = query,
            category         = category,
            job_type         = job_type,
            sal_from         = sal_from,
            sal_to           = sal_to,
            sort_by          = sort_by,
            total            = Vacancy.query.filter_by(is_active=True).count(),
            app_count        = Application.query.count(),
            sort_options     = make_sort_options(sort_by),
            category_options = make_category_options(category),
            type_options     = make_type_options(job_type),
        )

    # ── Детальная вакансия ───────────────────────────────────────
    @app.route('/vacancies/<int:vacancy_id>')
    def vacancy_detail(vacancy_id):
        vacancy = Vacancy.query.get_or_404(vacancy_id)
        related = (Vacancy.query
                   .filter_by(is_active=True, category=vacancy.category)
                   .filter(Vacancy.id != vacancy_id)
                   .limit(3).all())
        app_count = Application.query.filter_by(vacancy_id=vacancy_id).count()
        return render_template(
            'vacancy_detail.html',
            vacancy   = vacancy,
            related   = related,
            app_count = app_count,
        )

    # ── Опубликовать вакансию ────────────────────────────────────
    @app.route('/vacancies/publish', methods=['GET', 'POST'])
    def publish_vacancy():
        if request.method == 'POST':
            try:
                category = request.form.get('category', '')
                vacancy = Vacancy(
                    title         = request.form['title'].strip(),
                    category      = category,
                    job_type      = request.form.get('job_type', ''),
                    salary_from   = int(request.form.get('salary_from') or 0),
                    salary_to     = int(request.form.get('salary_to')   or 0),
                    location      = 'Самара',
                    experience    = request.form.get('experience', '').strip(),
                    education     = request.form.get('education',  '').strip(),
                    description   = request.form.get('description','').strip(),
                    duties        = request.form.get('duties',     '').strip(),
                    requirements  = request.form.get('requirements','').strip(),
                    conditions    = request.form.get('conditions', '').strip(),
                    contact_name  = request.form.get('contact_name', '').strip(),
                    contact_phone = request.form.get('contact_phone','').strip(),
                    icon          = ICONS_MAP.get(category, '📌'),
                    is_featured   = bool(request.form.get('is_featured')),
                    is_urgent     = bool(request.form.get('is_urgent')),
                    is_new        = True,
                    is_active     = True,
                )
                db.session.add(vacancy)
                db.session.commit()
                flash('Вакансия «' + vacancy.title + '» успешно опубликована!', 'success')
                return redirect(url_for('vacancy_detail', vacancy_id=vacancy.id))
            except Exception as e:
                db.session.rollback()
                flash('Ошибка при публикации: ' + str(e), 'danger')

        return render_template(
            'publish.html',
            page_title       = 'Публикация вакансии',
            form_icon        = '📌',
            form_action      = url_for('publish_vacancy'),
            submit_label     = 'Опубликовать вакансию',
            form_data        = get_publish_form_data(),
            category_options = make_category_options(''),
            job_type_options = make_type_options(''),
            experience_options = make_experience_options(''),
            edit             = False,
        )

    # ── Редактировать вакансию ───────────────────────────────────
    @app.route('/vacancies/<int:vacancy_id>/edit', methods=['GET', 'POST'])
    def edit_vacancy(vacancy_id):
        vacancy = Vacancy.query.get_or_404(vacancy_id)
        if request.method == 'POST':
            try:
                vacancy.title         = request.form['title'].strip()
                vacancy.category      = request.form.get('category', '')
                vacancy.job_type      = request.form.get('job_type', '')
                vacancy.salary_from   = int(request.form.get('salary_from') or 0)
                vacancy.salary_to     = int(request.form.get('salary_to')   or 0)
                vacancy.experience    = request.form.get('experience',   '').strip()
                vacancy.education     = request.form.get('education',    '').strip()
                vacancy.description   = request.form.get('description',  '').strip()
                vacancy.duties        = request.form.get('duties',       '').strip()
                vacancy.requirements  = request.form.get('requirements', '').strip()
                vacancy.conditions    = request.form.get('conditions',   '').strip()
                vacancy.contact_name  = request.form.get('contact_name', '').strip()
                vacancy.contact_phone = request.form.get('contact_phone','').strip()
                vacancy.is_featured   = bool(request.form.get('is_featured'))
                vacancy.is_urgent     = bool(request.form.get('is_urgent'))
                db.session.commit()
                flash('Вакансия обновлена!', 'success')
                return redirect(url_for('vacancy_detail', vacancy_id=vacancy.id))
            except Exception as e:
                db.session.rollback()
                flash('Ошибка: ' + str(e), 'danger')

        return render_template(
            'publish.html',
            page_title       = 'Редактировать вакансию',
            form_icon        = vacancy.icon,
            form_action      = url_for('edit_vacancy', vacancy_id=vacancy.id),
            submit_label     = 'Сохранить изменения',
            form_data        = get_publish_form_data(vacancy),
            category_options = make_category_options(vacancy.category),
            job_type_options = make_type_options(vacancy.job_type),
            experience_options = make_experience_options(vacancy.experience),
            edit             = True,
            vacancy          = vacancy,
        )

    # ── Удалить вакансию ─────────────────────────────────────────
    @app.route('/vacancies/<int:vacancy_id>/delete', methods=['POST'])
    def delete_vacancy(vacancy_id):
        vacancy = Vacancy.query.get_or_404(vacancy_id)
        vacancy.is_active = False
        db.session.commit()
        flash('Вакансия «' + vacancy.title + '» удалена.', 'info')
        return redirect(url_for('vacancies'))

    # ── Откликнуться ─────────────────────────────────────────────
    @app.route('/vacancies/<int:vacancy_id>/apply', methods=['GET', 'POST'])
    def apply(vacancy_id):
        vacancy = Vacancy.query.get_or_404(vacancy_id)
        if request.method == 'POST':
            try:
                application = Application(
                    vacancy_id   = vacancy_id,
                    first_name   = request.form['first_name'].strip(),
                    last_name    = request.form['last_name'].strip(),
                    email        = request.form['email'].strip(),
                    phone        = request.form['phone'].strip(),
                    experience   = request.form.get('experience', '').strip(),
                    education    = request.form.get('education',  '').strip(),
                    cover_letter = request.form.get('cover_letter','').strip(),
                    status       = 'new',
                )
                db.session.add(application)
                db.session.commit()
                flash(
                    'Заявка на вакансию «' + vacancy.title +
                    '» отправлена! Мы свяжемся с вами в течение 2 рабочих дней.',
                    'success'
                )
                return redirect(url_for('vacancy_detail', vacancy_id=vacancy_id))
            except Exception as e:
                db.session.rollback()
                flash('Ошибка при отправке заявки: ' + str(e), 'danger')

        return render_template('apply.html', vacancy=vacancy)

    # ── Список резюме ────────────────────────────────────────────
    @app.route('/resumes')
    def resumes():
        query   = request.args.get('q', '').strip()
        sort_by = request.args.get('sort', 'date')
        page    = request.args.get('page', 1, type=int)

        rq = Resume.query.filter_by(is_active=True)
        if query:
            rq = rq.filter(
                Resume.first_name.ilike('%' + query + '%') |
                Resume.last_name.ilike('%'  + query + '%') |
                Resume.position.ilike('%'   + query + '%') |
                Resume.skills.ilike('%'     + query + '%')
            )
        if sort_by == 'salary':
            rq = rq.order_by(Resume.salary.desc())
        else:
            rq = rq.order_by(Resume.created_at.desc())

        pagination = rq.paginate(
            page=page,
            per_page=app.config['RESUMES_PER_PAGE'],
            error_out=False
        )
        return render_template(
            'resumes.html',
            resumes      = pagination.items,
            pagination   = pagination,
            query        = query,
            sort_by      = sort_by,
            sort_options = make_sort_options(sort_by),
        )

    # ── Детальное резюме ─────────────────────────────────────────
    @app.route('/resumes/<int:resume_id>')
    def resume_detail(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        return render_template('resume_detail.html', resume=resume)

    # ── Добавить резюме ──────────────────────────────────────────
    @app.route('/resumes/add', methods=['GET', 'POST'])
    def add_resume():
        if request.method == 'POST':
            try:
                resume = Resume(
                    first_name   = request.form['first_name'].strip(),
                    last_name    = request.form['last_name'].strip(),
                    position     = request.form['position'].strip(),
                    email        = request.form['email'].strip(),
                    phone        = request.form.get('phone', '').strip(),
                    age          = int(request.form.get('age') or 0) or None,
                    experience   = request.form.get('experience', '').strip(),
                    education    = request.form.get('education',  '').strip(),
                    city         = request.form.get('city', 'Самара').strip(),
                    salary       = int(request.form.get('salary') or 0),
                    about        = request.form.get('about',  '').strip(),
                    skills       = request.form.get('skills', '').strip(),
                    avatar_color = random.choice(COLORS),
                    is_active    = True,
                )
                db.session.add(resume)
                db.session.commit()
                flash('Резюме ' + resume.full_name + ' успешно добавлено!', 'success')
                return redirect(url_for('resume_detail', resume_id=resume.id))
            except Exception as e:
                db.session.rollback()
                flash('Ошибка: ' + str(e), 'danger')

        return render_template(
            'add_resume.html',
            experience_options = make_experience_options(),
        )

    # ── О школе ──────────────────────────────────────────────────
    @app.route('/about')
    def about():
        stats = {
            'vacancy_count': Vacancy.query.filter_by(is_active=True).count(),
            'resume_count':  Resume.query.filter_by(is_active=True).count(),
            'app_count':     Application.query.count(),
        }
        return render_template('about.html', stats=stats)

    # ── API autocomplete ─────────────────────────────────────────
    @app.route('/api/search')
    def api_search():
        q = request.args.get('q', '').strip()
        if len(q) < 2:
            return jsonify([])
        results = (Vacancy.query
                   .filter(Vacancy.is_active == True,
                           Vacancy.title.ilike('%' + q + '%'))
                   .limit(8).all())
        return jsonify([
            {'id': v.id, 'title': v.title, 'salary': v.salary_display}
            for v in results
        ])

    # ── API stats ─────────────────────────────────────────────────
    @app.route('/api/stats')
    def api_stats():
        return jsonify({
            'vacancies':    Vacancy.query.filter_by(is_active=True).count(),
            'resumes':      Resume.query.filter_by(is_active=True).count(),
            'applications': Application.query.count(),
        })


# ───────────────────────── seed ─────────────────────────────────

def seed_data():
    if Vacancy.query.first():
        return

    vacancies = [
        dict(
            title='Курьер по доставке документов',
            category='Курьеры и доставка',
            job_type='Частичная занятость',
            salary_from=15000, salary_to=25000,
            experience='Без опыта',
            education='Не имеет значения',
            description='Ищем активных школьников для доставки документов по району.',
            duties='Доставка документов и мелких посылок\nВедение отчетности по доставкам',
            requirements='Ответственность\nПунктуальность\nХорошее знание района',
            conditions='Свободный график\nОплата за каждую доставку\nПроездной оплачивается',
            icon='🚲',
            is_featured=True, is_new=True, is_urgent=False,
            contact_name='ИП Смирнов',
            contact_phone='+7 (846) 111-22-33',
        ),
        dict(
            title='Промоутер на раздачу листовок',
            category='Промоутеры',
            job_type='Частичная занятость',
            salary_from=10000, salary_to=15000,
            experience='Без опыта',
            education='Не имеет значения',
            description='Работа на свежем воздухе для активных ребят.',
            duties='Раздача рекламных листовок прохожим\nКонсультирование по акциям (кратко)',
            requirements='Общительность\nДоброжелательность\nГотовность работать на улице',
            conditions='Работа по 3-4 часа в день\nЕженедельные выплаты\nРабота в вашем районе',
            icon='📢',
            is_featured=False, is_new=True, is_urgent=False,
            contact_name='Рекламное агентство "Старт"',
            contact_phone='+7 (846) 222-33-44',
        ),
        dict(
            title='Помощник вожатого в летний лагерь',
            category='Помощники и стажеры',
            job_type='Полная занятость',
            salary_from=20000, salary_to=25000,
            experience='Без опыта',
            education='Не имеет значения',
            description='Отличная возможность провести лето весело и с пользой в городском лагере.',
            duties='Помощь вожатому в организации игр\nСопровождение детей на экскурсиях\nПодготовка материалов для мастер-классов',
            requirements='Любовь к детям\nОрганизаторские способности\nВозраст от 14 лет',
            conditions='Питание за счет работодателя\nИнтересный коллектив\nРабота в будние дни',
            icon='🤝',
            is_featured=True, is_new=False, is_urgent=True,
            contact_name='Детский центр "Радуга"',
            contact_phone='+7 (846) 333-44-55',
        ),
        dict(
            title='Помощник по озеленению территории',
            category='Озеленение и благоустройство',
            job_type='Частичная занятость',
            salary_from=12000, salary_to=18000,
            experience='Без опыта',
            education='Не имеет значения',
            description='Работа в парках и скверах города по уходу за растениями.',
            duties='Полив клумб и газонов\nПрополка сорняков\nУборка мелкого мусора',
            requirements='Трудолюбие\nОтсутствие аллергии на растения\nГотовность к физическому труду',
            conditions='Работа в утренние часы\nПредоставляется инвентарь\nРабота на свежем воздухе',
            icon='🌱',
            is_featured=False, is_new=True, is_urgent=False,
            contact_name='ГорЗеленХоз',
            contact_phone='+7 (846) 444-55-66',
        ),
        dict(
            title='Контент-менеджер (ведение соцсетей)',
            category='Работа в интернете',
            job_type='Частичная занятость',
            salary_from=15000, salary_to=20000,
            experience='Без опыта',
            education='Не имеет значения',
            description='Ищем креативного школьника для помощи в ведении группы ВКонтакте.',
            duties='Поиск интересных картинок и видео\nНаписание коротких текстов\nОтветы на комментарии',
            requirements='Грамотность\nУмение пользоваться соцсетями\nКреативность',
            conditions='Удаленная работа\nСвободный график\nОбучение в процессе работы',
            icon='💻',
            is_featured=False, is_new=False, is_urgent=False,
            contact_name='Магазин "Канцтовары"',
            contact_phone='+7 (846) 555-66-77',
        ),
    ]

    resumes_seed = [
        dict(
            first_name='Максим', last_name='Иванов',
            position='Курьер',
            email='maksim@example.com',
            phone='+7 (846) 111-22-33',
            age=15, experience='Без опыта',
            education='Школа №147, 9 класс',
            city='Самара', salary=15000,
            about='Хорошо знаю город, есть велосипед. Готов работать во второй половине дня.',
            skills='Пунктуальность, ответственность, знание города',
            avatar_color='linear-gradient(135deg,#667eea,#764ba2)',
        ),
        dict(
            first_name='Анна', last_name='Смирнова',
            position='Помощник вожатого',
            email='anna@example.com',
            phone='+7 (846) 222-33-44',
            age=16, experience='Без опыта',
            education='Школа №147, 10 класс',
            city='Самара', salary=18000,
            about='Люблю детей, умею организовывать игры. Занимаюсь в театральной студии.',
            skills='Коммуникабельность, творческий подход, организация игр',
            avatar_color='linear-gradient(135deg,#f093fb,#f5576c)',
        ),
        dict(
            first_name='Егор', last_name='Кузнецов',
            position='Промоутер',
            email='egor@example.com',
            phone='+7 (846) 333-44-55',
            age=14, experience='До 1 года',
            education='Школа №147, 8 класс',
            city='Самара', salary=10000,
            about='Уже работал промоутером прошлым летом. Не боюсь общаться с людьми.',
            skills='Общительность, активность, громкий голос',
            avatar_color='linear-gradient(135deg,#4facfe,#00f2fe)',
        ),
    ]

    for v in vacancies:
        db.session.add(Vacancy(**v))
    for r in resumes_seed:
        db.session.add(Resume(**r))

    db.session.commit()
    print('База данных заполнена тестовыми данными')


# ───────────────────────── entry point ──────────────────────────

if __name__ == '__main__':
    # Получаем порт из переменных окружения (по умолчанию 5000)
    port = int(os.environ.get("PORT", 6000))
    # Запускаем на 0.0.0.0
    app.run(host='0.0.0.0', port=port)
