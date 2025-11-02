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
- Comprehensive admin dashboard
- Member management
- Class and trainer management
- Subscription plan management
- Email communication tools
- Analytics and metrics

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

- `core/` - User management, subscriptions, gamification
- `bookings/` - Class booking functionality
- `workouts/` - Workout library
- `community/` - Social hub and challenges
- `payments/` - Stripe integration
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `media/` - User-uploaded files

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

## Notes

- The platform uses SQLite for development (can be switched to PostgreSQL for production)
- Tailwind CSS is configured via django-tailwind
- Alpine.js is loaded via CDN for interactivity
- All payment processing uses Stripe Test Mode

## License

This project is for educational purposes.

