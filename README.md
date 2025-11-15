# GitHub Codespaces ♥️ Django

Welcome to your shiny new Codespace running Django! We've got everything fired up and running for you to explore Django.

You've got a blank canvas to work on from a git perspective as well. There's a single initial commit with what you're seeing right now - where you go from here is up to you!

Everything you do here is contained within this one codespace. There is no repository on GitHub yet. If and when you’re ready you can click "Publish Branch" and we’ll create your repository and push up your project. If you were just exploring then and have no further need for this code then you can simply delete your codespace and it's gone forever.

## installing dependancies

```python
pip install -r requirements.txt
# Elmosyar Backend - Authentication System

A Django-based authentication backend API with user registration, email verification, login, profile management, and password reset functionality.

## Features

- **User Registration** (Sign Up)
	- Username and email validation
	- IUST email domain verification (`@iust.ac.ir`)
	- Password confirmation
	- Email verification before account activation

- **Email Verification**
	- Token-based email verification
	- 24-hour token expiration
	- Email confirmation required before login

- **User Authentication**
	- Login with username or email
	- Session-based authentication
	- Logout functionality

- **Profile Management**
	- View user profile information
	- Edit profile fields:
		- First Name
		- Last Name
		- Student ID
		- Bio (optional)
	- Email and password are not editable through profile API

- **Password Recovery**
	- Request password reset via email
	- Token-based password reset
	- 1-hour token expiration
	- Password confirmation required

- **HTTP API**
	- All communication through HTTP REST endpoints
	- JSON request/response format
	- CORS enabled for frontend communication

## Project Structure

```
codespaces-django/
├── Elmosyar-back/              # Main Django project
│   ├── core/                   # Core authentication app
│   │   ├── models.py           # User model with custom fields
│   │   ├── views.py            # API endpoints
│   │   ├── urls.py             # URL routing
│   │   ├── migrations/         # Database migrations
│   │   └── __init__.py
│   ├── static/                 # Static files (CSS, JS, images)
│   ├── templates/              # HTML templates
│   │   └── index.html          # Testing interface
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   ├── wsgi.py                 # WSGI configuration
│   ├── asgi.py                 # ASGI configuration
│   └── __init__.py
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── db.sqlite3                  # SQLite database (development)
├── README.md                   # This file
└── .env.example               # Environment variables template
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation & Setup Guide

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd codespaces-django
```

### Step 2: Create and Activate Virtual Environment (Recommended)

```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

The default settings should work for local development:
```
SECRET_KEY=my_secret_key
DEBUG=True
ALLOWED_HOSTS=*
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Step 5: Run Database Migrations

First, ensure the database is clean:

```bash
# Remove old database (if exists)
rm db.sqlite3

# Run migrations
python manage.py migrate
```

### Step 6: Create Superuser/Admin Account

```bash
python manage.py createsuperuser --username kasra_fouladi --email kasra_fouladi@mathdep.iust.ac.ir --noinput
```

Then set the password:

```bash
python set_password.py
```

**Admin Credentials:**
- Username: `kasra_fouladi`
- Email: `kasra_fouladi@mathdep.iust.ac.ir`
- Password: `Bachegore1_`

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

The server will be available at:
- **Frontend Testing Interface:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **API Base URL:** http://localhost:8000/api/

## Quick Start for Testing

1. Go to http://localhost:8000/ in your browser
2. Use the navigation buttons to test different features
3. Check Django console for email verification tokens
4. Use tokens to verify email and reset passwords

## API Endpoints

### Authentication

#### Sign Up
```
POST /api/signup/
```
**Request:**
```json
{
	"username": "john_doe",
	"email": "john@iust.ac.ir",
	"password": "SecurePass123",
	"password_confirm": "SecurePass123"
}
```

#### Verify Email
```
GET /api/verify-email/<token>/
```

#### Login
```
POST /api/login/
```
**Request:**
```json
{
	"username_or_email": "john@iust.ac.ir",
	"password": "SecurePass123"
}
```

#### Logout
```
POST /api/logout/
```

### Profile

#### Get Profile
```
GET /api/profile/
```

#### Update Profile
```
POST /api/profile/update/
```
**Request:**
```json
{
	"first_name": "John",
	"last_name": "Doe",
	"student_id": "123456",
	"bio": "Optional biography"
}
```

### Password Reset

#### Request Reset
```
POST /api/password-reset/request/
```
**Request:**
```json
{
	"email": "john@iust.ac.ir"
}
```

#### Reset Password
```
POST /api/password-reset/<token>/
```
**Request:**
```json
{
	"password": "NewSecurePass123",
	"password_confirm": "NewSecurePass123"
}
```

## User Model

### Required Fields
- `username` - Unique username
- `email` - Unique email (@iust.ac.ir domain required)
- `password` - Hashed password (min 8 characters)

### Optional Fields
- `first_name` - User's first name
- `last_name` - User's last name
- `student_id` - Student ID number
- `bio` - User biography
- `profile_picture` - Profile image

### System Fields
- `is_email_verified` - Email verification status
- `email_verification_token` - 24-hour expiring token
- `password_reset_token` - 1-hour expiring token
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

## Common Commands

```bash
# Run development server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Create migrations
python manage.py makemigrations core

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Reset database completely
rm db.sqlite3
python manage.py migrate
```

## Email Configuration

**Development Mode:** Emails are printed to console

**Production Mode:** Update `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

## Troubleshooting

### Database Errors
```bash
rm db.sqlite3
python manage.py migrate
```

### Module Not Found Errors
Ensure you're in the correct directory and virtual environment is activated.

### CORS Errors
Add your frontend URL to `CORS_ALLOWED_ORIGINS` in `settings.py`

### Port Already in Use
```bash
python manage.py runserver 8001
```

## Security

- ⚠️ Change default admin credentials in production
- Email verification required before login
- Tokens expire automatically (email: 24h, password: 1h)
- Passwords hashed using PBKDF2
- CSRF protection enabled
- CORS configured for development

## Dependencies

See `requirements.txt`:
- Django ~5.2.2
- djangorestframework ~3.14.0
- django-cors-headers ~4.3.1
- python-decouple ~3.8
- Pillow ~10.1.0

## File Structure

```
Elmosyar-back/
├── core/
│   ├── models.py              # User model definition
│   ├── views.py               # API endpoints (350+ lines)
│   ├── urls.py                # URL routing
│   └── migrations/
├── settings.py                # Django configuration
├── urls.py                    # Main URL config
├── wsgi.py                    # WSGI entry point
└── asgi.py                    # ASGI entry point

templates/
└── index.html                 # Testing interface (HTML + JS, no CSS)

manage.py                       # Django management
requirements.txt                # Python packages
```

## Features Implemented

✅ User Registration with validation
✅ Email verification (24-hour tokens)
✅ User Login/Logout
✅ Profile View & Edit
✅ Password Reset (1-hour tokens)
✅ CORS enabled for frontend
✅ JSON API responses
✅ Session-based authentication
✅ Custom User model
✅ Testing interface

## Notes

- All text and code is in English only
- No external CSS framework used
- Simple HTML + vanilla JavaScript for testing
- SQLite database for development
- Full REST API ready for frontend integration

## Support

For documentation:
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- IUST: Use @iust.ac.ir email domain
