# Django Admin URL Configuration - Explanation

## Issue

When accessing `/django-admin/auth/user/`, you get a 404 error.

## Root Cause

This project uses a **custom user model** (`CustomUser`), not Django's default `auth.User` model.

**In `gym_pranamya/settings.py`:**
```python
AUTH_USER_MODEL = 'core.CustomUser'
```

When you use a custom user model:
- The default `auth.User` model is **not available**
- Django's default admin URLs for `auth.User` will return 404
- You must use your custom user model instead

## Solution

### ✅ Correct URLs for Django Admin

Instead of `/django-admin/auth/user/`, use:

**For Users:**
- `/django-admin/core/customuser/` - List all users
- `/django-admin/core/customuser/add/` - Create new user
- `/django-admin/core/customuser/<id>/change/` - Edit user

**Other Admin URLs:**
- `/django-admin/` - Admin index page
- `/django-admin/core/` - Core app models (Users, Plans, Subscriptions, etc.)
- `/django-admin/bookings/` - Booking models
- `/django-admin/workouts/` - Workout models
- `/django-admin/community/` - Community models

### ✅ Alternative: Use Staff Portal

For managing users, you can also use the **Staff Portal** which is more user-friendly:

- **Staff User Management:** `/staff/staff-users/`
  - Create new staff users
  - Toggle staff status for existing users
  - Search and filter users
  - Better UI than Django admin

- **Member Management:** `/staff/members/`
  - View all members
  - Member details
  - Manage subscriptions
  - Add points manually

## URL Configuration

The Django admin is properly configured at:

```python
# gym_pranamya/urls.py
path('django-admin/', admin.site.urls, name='admin'),
```

This is correct and working. The 404 error is **expected behavior** when trying to access the default `auth.User` model that doesn't exist in this project.

## Summary

- ✅ Django admin is working correctly
- ✅ Custom user model is properly registered
- ❌ Default `auth.User` URLs will always return 404 (by design)
- ✅ Use `/django-admin/core/customuser/` instead
- ✅ Or use Staff Portal at `/staff/staff-users/` for better UX

