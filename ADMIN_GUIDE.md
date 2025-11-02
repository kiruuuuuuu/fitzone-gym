# Admin Guide - FitZone Gym

## Accessing Admin Panel

When logged in as a staff/superuser, you'll see an "Admin" link in the navigation bar. Click it to access Django Admin at `/admin/`.

Alternatively, go directly to: `http://127.0.0.1:8000/admin/`

## Creating Membership Plans

1. Navigate to Admin Panel (`/admin/`)
2. Under "CORE" section, click **"Membership Plans"**
3. Click **"Add Membership Plan"** (top right)
4. Fill in the form:
   - **Name**: e.g., "Basic Plan", "Premium Plan"
   - **Price**: Monthly price (e.g., 49.99)
   - **Features**: List features (one per line):
     ```
     Access to all equipment
     Group classes included
     24/7 facility access
     Personal trainer sessions
     ```
   - **Stripe Price ID**: Leave empty for now (or add test Stripe Price ID if configured)
   - **Is active**: Check this box
5. Click **"Save"**

## Creating Gym Classes

1. Navigate to Admin Panel (`/admin/`)
2. Under "BOOKINGS" section, click **"Gym Classes"**
3. Click **"Add Gym Class"** (top right)
4. Fill in the form:
   - **Name**: e.g., "Morning Yoga", "HIIT Training"
   - **Description**: Class description
   - **Trainer**: Select a trainer (create trainers first if needed)
   - **Duration**: Minutes (e.g., 60)
   - **Max capacity**: Maximum participants (e.g., 20)
   - **Schedule time**: e.g., 08:00 AM
   - **Schedule days**: Comma-separated days (e.g., `monday,wednesday,friday` or `tuesday,thursday`)
   - **Is active**: Check this box
5. Click **"Save"**

## Creating Trainers

1. Navigate to Admin Panel (`/admin/`)
2. Under "CORE" section, click **"Trainers"**
3. Click **"Add Trainer"** (top right)
4. Fill in the form:
   - **User**: Select an existing user or create one first
   - **Bio**: Trainer biography
   - **Specializations**: Comma-separated (e.g., `Yoga, Pilates, Strength Training`)
   - **Profile picture**: Upload optional image
5. Click **"Save"**

## Quick Notes

- All models are registered in Django Admin
- You need to be logged in as a superuser (created via `python manage.py createsuperuser`)
- The "Admin" link appears in navigation only for staff users
- Membership plans and classes must be marked "Is active" to appear on public pages

