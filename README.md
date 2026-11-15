# SpotNiBai

IM2 Phase 1: Account Feature (registration, login/logout, role-based dashboards, user profile).

## Tech stack
- Django (full stack, Django templates)
- PostgreSQL via Supabase

## Features
- Account registration with validation and hashed passwords
- Login and logout, with protected pages
- Role-based dashboards (Administrator and Member)
- User profile view and edit (own profile only)

## Setup
1. Clone the repository and open the folder.
2. Create and activate a virtual environment (Python 3.13):

       py -3.13 -m venv venv
       venv\Scripts\activate

3. Install the dependencies:

       pip install -r requirements.txt

4. Copy `.env.example` to `.env` and fill in your own database credentials.
5. Apply the database migrations:

       python manage.py migrate

6. Create an administrator account:

       python manage.py createsuperuser

7. Start the server and open http://127.0.0.1:8000/:

       python manage.py runserver

## Roles
- **Administrator:** admin dashboard
- **Member:** member dashboard (default for new sign-ups)
