# SpotNiBai

SpotNiBai is a location-based web application for discovering, exploring and sharing interesting places around Cebu City.

## Tech stack
- Django (full stack, Django templates)
- PostgreSQL via Supabase
- Supabase Storage (S3-compatible) for uploaded photos

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

### Hardening (Project Development 3)
No new features were added. The existing features were made reliable, secure and tested:
- **Access control:** every page requires login, roles are checked in the views, owners can only edit or delete their own spots (other users get a 404), pending spots are hidden from other users, and approve/reject are POST-only and only work on Pending spots
- **Validation:** server-side validation on every form, including photo format (JPG or PNG, 5 MB), contact number format, case-insensitive duplicate email and duplicate spot checks, and coordinates within Cebu
- **Data integrity:** database constraints (one spot per owner, name and address; one cover photo per spot; rating between 0 and 5), `PROTECT` on categories in use, `CASCADE` for spot photos and a user's own spots, and spot plus photo saves wrapped in `transaction.atomic()`
- **Error handling:** custom 403, 404 and 500 pages, `get_object_or_404`, redirect after every successful POST, and success or error messages for every action
- **Photo storage:** photos are stored in Supabase Storage so they appear on every computer, and a photo file is removed when its spot is deleted
- **Configuration:** secrets, `DEBUG` and `ALLOWED_HOSTS` come from `.env`
- **Tests:** 40 automated tests (see Running the tests)

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

4. Copy `.env.example` to `.env` and fill in your own values (see Environment variables below). For uploaded photos, create a **public** bucket named `spot-photos` in Supabase Storage and generate S3 access keys under Storage > S3 Configuration.
5. Apply the database migrations (this also adds the default spot categories):

       python manage.py migrate

6. Create an administrator account (superusers automatically get the Administrator role):

       python manage.py createsuperuser

7. Start the server and open http://127.0.0.1:8000/:

       python manage.py runserver

To see the custom 404 and 500 pages, set `DEBUG=False` in `.env` and start the server with `python manage.py runserver --insecure` so the CSS still loads.

## Branching
- `main`: stable code only, no direct commits
- `develop`: integration branch
- `feature/<name>`: one branch per feature (Project Development 2)
- `fix/<issue>`, `hardening/<area>` and `test/<area>`: work branches created from `develop` (Project Development 3)

Work branches are merged into `develop` by pull request, `develop` is merged into `main` by pull request when an increment is done, and merged branches are never deleted.

## Running the tests

The automated tests cover the spot submission and moderation feature (validation, access control, data integrity) and the account features (registration, login/logout, role dashboards, profile).

1. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
2. Make sure a `.env` file exists in the project root. Copy `.env.example` to `.env` and fill in your values.
3. Run all tests:
   ```
   python manage.py test
   ```
   To run one app only: `python manage.py test spots` or `python manage.py test accounts`.

Expected result: `Ran 40 tests` followed by `OK`.

Notes:
- Test runs use a temporary in-memory SQLite database, so your Supabase data is never touched.
- Photo uploads in tests are stored in memory, so nothing is uploaded to the Supabase Storage bucket.

## Environment variables

Copy `.env.example` to `.env` and set:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development, `False` otherwise |
| `ALLOWED_HOSTS` | Comma-separated hosts, e.g. `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_SSLMODE` | Supabase PostgreSQL connection |
| `SUPABASE_PROJECT_REF`, `SUPABASE_BUCKET`, `SUPABASE_REGION`, `SUPABASE_S3_ACCESS_KEY`, `SUPABASE_S3_SECRET_KEY` | Supabase Storage bucket for uploaded photos |

## Notes
- Uploaded photos (spot cover photos and profile photos) are stored in the Supabase Storage bucket, not in the repository.
- Known limitation: when a user replaces their profile photo, the old file stays in the bucket.
