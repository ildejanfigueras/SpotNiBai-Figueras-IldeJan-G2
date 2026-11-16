# SpotNiBai

SpotNiBai is a location-based web application for discovering, exploring and sharing interesting places around Cebu City.

## Tech stack
- Django (full stack, Django templates)
- PostgreSQL via Supabase

## Features

### Standard features (Project Development 1)
- Account registration with validation and hashed passwords
- Login and logout, with protected pages
- Role-based dashboards (Administrator and Registered User)
- User profile view and edit (own profile only)

### Core feature (Project Development 2): Spot Submission and Moderation
- Registered users submit spots (name, category, description, address, coordinates, optional cover photo)
- New spots start as **Pending** and are hidden until an administrator reviews them
- Registered users can view, edit and delete their own spots in **My Spots**; editing sends a spot back to Pending
- All logged-in users can browse approved spots, with search, category filter and pagination
- Administrators review pending spots in the **Review Queue** and approve or reject them
- Administrators can delete any spot
- Spot statistics and shortcuts appear on both role dashboards
- Validation: required fields, minimum text lengths, coordinates within Cebu, photo type and size (5 MB), and duplicate spot check

## Roles
| Role | Can do |
|---|---|
| Registered User | Submit, edit and delete own spots; browse approved spots; manage own profile |
| Administrator | Review (approve/reject) and delete spots; view user statistics |
| Guest (not logged in) | Redirected to login (guest browsing is planned for a later phase) |

## Setup
1. Clone the repository and open the folder.
2. Create and activate a virtual environment (Python 3.12 or newer):

       py -3.13 -m venv venv
       venv\Scripts\activate

3. Install the dependencies:

       pip install -r requirements.txt

4. Copy `.env.example` to `.env` and fill in your own database credentials.
5. Apply the database migrations (this also adds the default spot categories):

       python manage.py migrate

6. Create an administrator account:

       python manage.py createsuperuser

7. Start the server and open http://127.0.0.1:8000/:

       python manage.py runserver

## Branching
- `main`: stable code only
- `develop`: integration branch
- `feature/<name>`: one branch per feature, merged into `develop` by pull request

## Notes
- Uploaded photos are stored in the local `media/` folder, which is not tracked by Git.