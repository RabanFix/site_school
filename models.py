from database import db
from datetime import datetime


class Vacancy(db.Model):
    __tablename__ = 'vacancies'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    category    = db.Column(db.String(100), nullable=False)
    job_type    = db.Column(db.String(100), nullable=False)
    salary_from = db.Column(db.Integer, default=0)
    salary_to   = db.Column(db.Integer, default=0)
    location    = db.Column(db.String(200), default='Самара, ул. Пятилетки, 14')
    experience  = db.Column(db.String(100), default='По договорённости')
    education   = db.Column(db.String(200), default='По договорённости')
    description = db.Column(db.Text, nullable=False)
    duties      = db.Column(db.Text, nullable=False)
    requirements= db.Column(db.Text, nullable=False)
    conditions  = db.Column(db.Text, default='')
    contact_name= db.Column(db.String(150), default='')
    contact_phone=db.Column(db.String(50), default='')
    icon        = db.Column(db.String(10), default='📌')
    is_featured = db.Column(db.Boolean, default=False)
    is_active   = db.Column(db.Boolean, default=True)
    is_urgent   = db.Column(db.Boolean, default=False)
    is_new      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        'Application', backref='vacancy', lazy=True, cascade='all, delete-orphan'
    )

    @property
    def salary_display(self):
        if self.salary_from and self.salary_to:
            return f"{self.salary_from:,} – {self.salary_to:,} ₽".replace(',', ' ')
        elif self.salary_from:
            return f"от {self.salary_from:,} ₽".replace(',', ' ')
        return 'По договорённости'

    @property
    def posted_display(self):
        delta = datetime.utcnow() - self.created_at
        if delta.days == 0:
            return 'Сегодня'
        elif delta.days == 1:
            return 'Вчера'
        elif delta.days < 7:
            return f'{delta.days} дня(-ей) назад'
        elif delta.days < 30:
            weeks = delta.days // 7
            return f'{weeks} недел(ю/и) назад'
        return self.created_at.strftime('%d.%m.%Y')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'job_type': self.job_type,
            'salary_display': self.salary_display,
            'salary_from': self.salary_from,
            'location': self.location,
            'experience': self.experience,
            'posted_display': self.posted_display,
            'icon': self.icon,
            'is_featured': self.is_featured,
            'is_urgent': self.is_urgent,
            'is_new': self.is_new,
        }

    def __repr__(self):
        return f'<Vacancy {self.title}>'


class Resume(db.Model):
    __tablename__ = 'resumes'

    id           = db.Column(db.Integer, primary_key=True)
    first_name   = db.Column(db.String(100), nullable=False)
    last_name    = db.Column(db.String(100), nullable=False)
    position     = db.Column(db.String(200), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    phone        = db.Column(db.String(50), default='')
    age          = db.Column(db.Integer, nullable=True)
    experience   = db.Column(db.String(100), default='')
    education    = db.Column(db.String(200), default='')
    city         = db.Column(db.String(100), default='Самара')
    salary       = db.Column(db.Integer, default=0)
    about        = db.Column(db.Text, default='')
    skills       = db.Column(db.String(500), default='')
    avatar_color = db.Column(db.String(200), default='linear-gradient(135deg,#667eea,#764ba2)')
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def salary_display(self):
        if self.salary:
            return f"{self.salary:,} ₽".replace(',', ' ')
        return 'По договорённости'

    @property
    def skills_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

    @property
    def posted_display(self):
        delta = datetime.utcnow() - self.created_at
        if delta.days == 0:
            return 'Сегодня'
        elif delta.days == 1:
            return 'Вчера'
        elif delta.days < 7:
            return f'{delta.days} дня(-ей) назад'
        return self.created_at.strftime('%d.%m.%Y')

    def __repr__(self):
        return f'<Resume {self.full_name}>'


class Application(db.Model):
    __tablename__ = 'applications'

    id           = db.Column(db.Integer, primary_key=True)
    vacancy_id   = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    first_name   = db.Column(db.String(100), nullable=False)
    last_name    = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    phone        = db.Column(db.String(50), nullable=False)
    experience   = db.Column(db.String(100), default='')
    education    = db.Column(db.String(100), default='')
    cover_letter = db.Column(db.Text, default='')
    status       = db.Column(
        db.String(50),
        default='new'
    )  # new | reviewed | invited | rejected
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def status_display(self):
        statuses = {
            'new': 'Новая',
            'reviewed': 'Рассмотрена',
            'invited': 'Приглашён',
            'rejected': 'Отклонена'
        }
        return statuses.get(self.status, self.status)

    def __repr__(self):
        return f'<Application {self.full_name} → {self.vacancy_id}>'
