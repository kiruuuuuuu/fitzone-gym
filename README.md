# FitZone Gym - Comprehensive Gym Management Platform

A full-featured gym management platform built with Django, Tailwind CSS, and Alpine.js.

## Features

### For Members
- User registration and authentication
- Subscription management with Stripe integration
- Class booking system
- Workout library with video guides
- Gamified tracking (points and streaks)
- QR code entry system
- Community feed and challenges

### For Administrators
- **Staff Portal** - Frontend dashboard for daily operations
- Member management with search and details
- Class and trainer management
- Subscription plan management
- Workout library management
- QR code check-in system
- Email communication tools

### For Trainers
- **Trainer Portal** - View assigned classes and rosters
- Mark class attendance (attended/no show)
- Track booking numbers
- Manage class schedules
- Create personalized workout plans
- Assign workout plans to members with custom notes

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=sqlite:///db.sqlite3
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Set up Tailwind CSS (already configured):
   - The theme app is already created and configured
   - Tailwind CSS has been installed and compiled
   - To rebuild CSS during development, run:
     ```bash
     python manage.py tailwind start  # Runs watch mode for CSS compilation (auto-rebuilds on template changes)
     ```
   - Or manually rebuild CSS:
     ```bash
     cd theme/static_src && npm run build
     ```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

- `core/` - User management, subscriptions, gamification (points, streaks, QR codes)
- `bookings/` - Class booking with race condition protection
- `workouts/` - Workout library and personalized plans
- `community/` - Social feed, challenges with auto-tracking
- `payments/` - Stripe integration with webhook handling
- `staff/` - Staff Portal (member/plan/class/workout/trainer/challenge management)
- `templates/` - HTML templates organized by app
- `static/` - Static assets (CSS, JS, images)
- `staticfiles/` - Compiled static files for production
- `media/` - User-uploaded files (workout thumbnails, trainer photos)
- `theme/` - Tailwind CSS configuration

## Stripe Setup

1. Create a Stripe account and get test API keys
2. Add keys to `.env` file
3. Set up webhook endpoint in Stripe Dashboard pointing to: `https://yourdomain.com/payments/webhook/`
4. Use Stripe CLI for local testing:
```bash
stripe listen --forward-to localhost:8000/payments/webhook/
```

## Testing

Use Stripe test cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

## Recent Enhancements (2025)

### Critical Bug Fixes
- ✅ Fixed booking race condition with atomic transactions
- ✅ Improved Stripe price validation
- ✅ Enhanced webhook error handling

### Gamification System
- ✅ Points awarded for workouts (10 pts), classes (15 pts), and check-ins (5 pts)
- ✅ Automatic streak tracking with daily validation
- ✅ Progress visualization on dashboard

### Staff & Trainer Portals
- ✅ Complete frontend for staff operations (replaces Admin-only access)
- ✅ Member management with search
- ✅ Class and workout management
- ✅ QR code check-in system
- ✅ Trainer attendance tracking

### Personalized Workout Plans
- ✅ Trainers create and assign custom plans to members
- ✅ Members view assigned plans on dashboard
- ✅ Custom trainer notes per member

See [IMPLEMENTATION_HISTORY.md](IMPLEMENTATION_HISTORY.md) for full details.

## User Roles

- **Members** - Access workouts, book classes, track progress, join challenges, view assigned workout plans
- **Trainers** - Manage classes, track attendance, create and assign workout plans
- **Staff** - Full operational access via Staff Portal (member/subscription/class/trainer management, QR check-in, reporting)
- **Superusers** - Django Admin access for system configuration

## Notes

- The platform uses SQLite for development (can be switched to PostgreSQL for production)
- Tailwind CSS is configured via django-tailwind
- Alpine.js is loaded via CDN for interactivity
- All payment processing uses Stripe Test Mode
- Staff portal accessible at `/staff/` for staff users (replaces most Admin operations)
- Trainer portal accessible at `/portal/` for trainers (class management and workout plans)

## License

This project is for educational purposes.

