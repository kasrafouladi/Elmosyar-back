# elmosyar_back

A Django-based authentication backend API providing user registration, email verification, login, profile management, and password reset functionality. Designed for local development with an easy setup and a production checklist.

## Key Features
- User registration (IUST email domain: @iust.ac.ir), email verification (24h)
- Login with username or email; session-based auth; logout
- Profile view/edit (first/last name, student ID, bio, profile picture)
- Password reset via email (1h tokens)
- REST JSON API, CORS enabled, media handling (Pillow)
- Posts/feed, likes, comments, mentions, notifications (implemented)

## Prerequisites
- Python 3.8+
- pip
- Virtual environment recommended

## Quick Setup (development)
1. Clone repository
```bash
git clone <repository-url>
cd elmosyar_back
```
2. Create & activate venv, install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Configure environment variables
```bash
cp .env.example .env
# Edit .env: SECRET_KEY, DEBUG, ALLOWED_HOSTS, email settings, etc.
```
4. Database & admin
```bash
rm -f db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```
(You can use `--username` and `--email` flags; set password interactively.)

5. Run dev server
```bash
python manage.py runserver 0.0.0.0:8000
```
Local test URL: http://localhost:8000

## Project structure (overview)
```
elmosyar_back/
├── core/               # auth app (models, views, urls)
│   ├── models.py       # User, Post, Comment, Like, Notification models
│   ├── views.py        # API view functions and logic
│   ├── urls.py         # URL routing for core endpoints
│   ├── migrations/     # Database migration files
│   ├── __init__.py
│   └── admin.py        # Django admin configuration
├── templates/          # frontend testing interface
│   ├── base.html       # base template (optional)
│   ├── index.html      # main authentication interface
│   ├── posts.html      # social feed interface
│   └── components/     # reusable template components
│       ├── navbar.html
│       ├── home-view.html
│       ├── signup-view.html
│       ├── login-view.html
│       ├── verify-email-view.html
│       ├── forgot-password-view.html
│       ├── reset-password-view.html
│       ├── profile-view.html
│       ├── post-form.html
│       └── post-list.html
├── static/             # CSS, JavaScript, images
│   ├── css/
│   ├── js/
│   └── images/
├── media/              # uploaded files (user-generated)
│   ├── profiles/       # user profile pictures
│   └── posts/          # post media (images, videos, docs)
│       ├── images/
│       ├── videos/
│       └── media/
├── elmosyar_back/      # main Django project settings
│   ├── __init__.py
│   ├── asgi.py         # ASGI configuration for async
│   ├── settings.py     # Django settings (DB, auth, apps, etc.)
│   ├── urls.py         # main URL routing
│   ├── wsgi.py         # WSGI configuration for production
│   └── admin.py        # project-level admin config
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies (pip install -r)
├── .env.example        # environment variables template
├── db.sqlite3          # SQLite database (development)
├── README.md           # this file
└── .gitignore          # git ignore rules
```

### Key File Descriptions

**settings.py**
```python
# Critical configurations:
- DEBUG: Enable/disable debug mode
- SECRET_KEY: Django secret for cryptography
- DATABASES: Database configuration (SQLite/PostgreSQL)
- INSTALLED_APPS: Enabled Django and third-party apps
- MIDDLEWARE: Request/response processing pipeline
- TEMPLATES: Template engine configuration
- REST_FRAMEWORK: DRF settings for API
- CORS_ALLOWED_ORIGINS: Frontend domains allowed
- MEDIA_ROOT/MEDIA_URL: File upload configuration
- EMAIL_BACKEND: Email configuration
- AUTH_USER_MODEL: Custom user model reference
```

**urls.py (main)**
```python
# Main URL dispatcher:
- Admin panel: /admin/
- Core app endpoints: /api/* (via include)
- Static files: /static/ (development)
- Media files: /media/ (development)
```

**core/views.py**
```python
# API endpoints (15+ functions):
- signup(): User registration
- verify_email(): Email confirmation
- login_user(): Authentication
- logout_user(): Session termination
- get_profile(): User profile retrieval
- update_profile(): Profile information update
- update_profile_picture(): Image upload
- request_password_reset(): Password recovery request
- reset_password(): Password change
- posts_list_create(): Post feed and creation
- post_like(): Like/unlike posts
- post_comment(): Add comments
- post_repost(): Share posts
- notifications_list(): User notifications
- notifications_mark_read(): Mark notifications
```

**core/models.py**
```python
# Database models (6 main models):
- User: Extended Django User with IUST fields
- Post: Content creation
- PostMedia: Media files for posts
- Like: Post interactions
- Comment: Post discussions
- Notification: User notifications
```

**requirements.txt**
```
Django==5.2.2
djangorestframework==3.14.0
django-cors-headers==4.3.1
python-decouple==3.8
Pillow==10.1.0
(plus transitive dependencies)
```

## API (summary)
- POST /api/signup/ — register
- GET /api/verify-email/<token>/ — verify email
- POST /api/login/ — login (username_or_email + password)
- POST /api/logout/ — logout
- GET /api/profile/ — get profile
- POST /api/profile/update/ — update profile fields
- POST /api/profile/update-picture/ — upload profile picture (multipart)
- POST /api/password-reset/request/ — request reset
- POST /api/password-reset/<token>/ — reset password

Example signup request:
```json
{
    "username":"john_doe",
    "email":"john@iust.ac.ir",
    "password":"SecurePass123",
    "password_confirm":"SecurePass123"
}
```

## User model (high level)
- Required: username, email (@iust.ac.ir), password (min 8)
- Optional: first_name, last_name, student_id, bio, profile_picture
- System: is_email_verified, email_verification_token (24h), password_reset_token (1h), created_at, updated_at

## Database Schema (Entity Relationship Diagram)

```
┌─────────────────────────────────────────────────┐
│                    USER                         │
├─────────────────────────────────────────────────┤
│ id (PK)                                         │
│ username (UNIQUE)                               │
│ email (UNIQUE, @iust.ac.ir)                    │
│ password (hashed)                               │
│ first_name                                      │
│ last_name                                       │
│ student_id                                      │
│ bio (TextField)                                 │
│ profile_picture (ImageField)                   │
│ is_email_verified (Boolean)                    │
│ email_verification_token                       │
│ email_verification_sent_at                     │
│ password_reset_token                           │
│ password_reset_sent_at                         │
│ is_active (Boolean)                            │
│ created_at (DateTime)                          │
│ updated_at (DateTime)                          │
└─────────────────────────────────────────────────┘
           ▲              ▲            ▲
           │              │            │
           │ 1:N          │ 1:N       │ 1:N
           │              │           │
    ┌──────┴────┐  ┌──────┴──────┐ ┌─┴──────────┐
    │            │  │             │ │            │
    ▼            ▼  ▼             ▼ ▼            ▼
┌────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌──────────────┐
│  POST  │ │ COMMENT │ │  LIKE   │ │NOTIFIC.│ │NOTIFICATION │
├────────┤ ├─────────┤ ├─────────┤ ├────────┤ ├──────────────┤
│ id(PK) │ │ id(PK)  │ │ id(PK)  │ │id(PK)  │ │ id (PK)      │
│author_id│ │user_id  │ │user_id  │ │recip.. │ │ recipient_id │
│content  │ │post_id  │ │post_id  │ │sender..│ │ sender_id    │
│tags    │ │content  │ │created_at│ │type    │ │ notif_type   │
│is_repost│ │post_id  │ │         │ │post_id │ │ post_id      │
│original │ │parent_id│ │UNIQUE   │ │message │ │ comment_id   │
│mentions │ │created_at│ │(user,  │ │is_read │ │ message      │
│created_at│ │         │ │post)   │ │created │ │ is_read      │
│updated_at│ │         │ │        │ │_at    │ │ created_at   │
└────────┘ └─────────┘ └─────────┘ └────────┘ └──────────────┘
    │
    │ 1:N
    │
    ▼
┌──────────────┐
│  POSTMEDIA   │
├──────────────┤
│ id (PK)      │
│ post_id (FK) │
│ file         │
│ media_type   │
│ created_at   │
└──────────────┘
```

### Relationships Summary

| Model | Relationship | Target | Type |
|-------|---|---|---|
| POST | author | USER | ForeignKey |
| POST | mentions | USER | ManyToMany |
| POST | original_post | POST | ForeignKey (self) |
| POSTMEDIA | post | POST | ForeignKey |
| LIKE | user | USER | ForeignKey |
| LIKE | post | POST | ForeignKey |
| COMMENT | user | USER | ForeignKey |
| COMMENT | post | POST | ForeignKey |
| COMMENT | parent | COMMENT | ForeignKey (self) |
| NOTIFICATION | recipient | USER | ForeignKey |
| NOTIFICATION | sender | USER | ForeignKey |
| NOTIFICATION | post | POST | ForeignKey |
| NOTIFICATION | comment | COMMENT | ForeignKey |

## Development notes
- In development emails are printed to console.
- Add frontend domain to CORS_ALLOWED_ORIGINS/CORS_ALLOWED_HOSTS.
- MEDIA_ROOT used for uploaded files; DEBUG=True is fine for development.

## Production checklist
- Set DEBUG = False
- Use a strong SECRET_KEY
- Configure ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
- Configure SMTP for email (see settings.py)
- Use persistent DB (Postgres), secure credentials
- Use S3/CDN or web server (Nginx) for static/media
- Enable HTTPS, SECURE_SSL_REDIRECT, proper logging & backups

Example SMTP config for settings.py:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'user@example.com'
EMAIL_HOST_PASSWORD = 'password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

## Common commands
```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
rm db.sqlite3 && python manage.py migrate
```

## Troubleshooting
- Module not found: activate the correct venv and be in project root.
- DB errors: remove db.sqlite3 and rerun migrations.
- CORS errors: add frontend URL to CORS_ALLOWED_ORIGINS.
- Port in use: runserver with different port (e.g., 8001).

## Dependencies
See requirements.txt (Django ~5.2.2, djangorestframework ~3.14, django-cors-headers, python-decouple, Pillow, etc.)

## Notes
- Tokens: email verification 24h, password reset 1h.
- All API responses use a consistent JSON format: { success, message, data }.
- Frontend testing interface available at the project root (templates/index.html).

For full details, refer to the project files and API routes in core/ and settings.py.

---

## About Elmosyar Project

**Elmosyar** is a comprehensive social platform and authentication system designed for the Iran University of Science and Technology (IUST) community. The name "Elmosyar" (الموسیقار) reflects the harmony and coordination required in a connected university network.

### Project Purpose

elmosyar_back provides the backend infrastructure for a LinkedIn-like social network specifically tailored for IUST students and faculty, enabling:
- Secure user authentication and profile management
- Academic and professional networking
- Content sharing and community engagement
- Real-time notifications and interactions

### Target Users

- **IUST Students**: Using @iust.ac.ir email addresses
- **Faculty Members**: Academic staff at IUST
- **Alumni**: Former students maintaining connections

### Key Design Principles

1. **Security First**: All passwords hashed, email verification required, token-based operations
2. **Scalability**: RESTful API design, database-optimized queries, media storage separation
3. **User Privacy**: Only authenticated users can access profiles and content
4. **Community Focus**: Built-in social features (mentions, tags, notifications)
5. **Academic Integration**: Student ID tracking, institution email verification

### Core Capabilities

#### Authentication & Authorization
- Email-based domain verification (IUST-only)
- Session-based authentication
- Token expiration for security
- Password hashing with PBKDF2

#### User Profiles
- Customizable profile information
- Profile picture support with image processing
- Academic identity (student ID)
- Bio and professional information

#### Social Features
- Post creation with rich media support
- Like and comment system
- Repost functionality for content amplification
- @mentions for direct communication
- Hashtags for content organization
- Notification system for user interactions

#### Media Management
- Image upload and storage
- Video media support
- Document sharing capabilities
- Automatic file type detection
- Storage organization by content type

### Technical Architecture

**Backend**: Django 5.2.2
- Modular app structure (core app for authentication)
- Django ORM for database operations
- Django REST Framework for API endpoints

**Database**: SQLite (development) / PostgreSQL (recommended production)
- Relational schema with proper indexing
- Foreign key relationships for data integrity
- Many-to-many relationships for tags and mentions

**Authentication**: Session-based
- HTTP-only cookies for token storage
- CSRF protection enabled
- CORS support for frontend integration

**File Storage**: Django's FileField
- Local storage for development
- S3/CDN recommended for production
- Automatic path organization

### Security Measures

- Password minimum 8 characters with confirmation
- Email verification before account activation
- Token-based operations with expiration
- SQL injection prevention via ORM
- XSS protection through Django templates
- CSRF tokens on all state-changing operations
- Rate limiting recommended for production

### API Design Patterns

- RESTful endpoints following HTTP semantics
- Consistent JSON response format
- HTTP status codes for clarity
- Error messages in responses
- Pagination support for large datasets

### Deployment Considerations

**Development**:
- SQLite database
- DEBUG mode enabled
- Console email printing
- CORS permissive settings

**Production**:
- PostgreSQL database
- DEBUG disabled
- SMTP email configuration
- Specific ALLOWED_HOSTS
- HTTPS enforcement
- CDN for media files
- Automated backups

### Future Enhancement Opportunities

- Advanced search functionality
- User recommendation system
- Direct messaging between users
- Event creation and management
- Group creation for courses/clubs
- File sharing with access control
- Activity feed algorithms
- Mobile application API expansion
- Analytics dashboard
- Two-factor authentication

### Integration Points

- Email verification via SMTP
- OAuth integration ready
- Frontend framework agnostic
- Mobile app compatible
- Third-party social media sharing

### Support & Maintenance

- Regular security updates
- Database migration support
- API versioning ready
- Performance monitoring
- Error logging and tracking
- Community contribution ready

### License & Attribution

elmosyar_back is developed for educational and community purposes at IUST. The platform respects user privacy and data security standards.

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Maintained By**: IUST Development Team
