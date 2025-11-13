# FitZone Gym - Comprehensive Gym Management Platform

A full-featured gym management platform built with Django, Tailwind CSS, and Alpine.js with modern, professional UI design.

## Features

### For Members
- User registration and authentication
- **Instant Subscription Management** - Subscribe to plans instantly (Stripe bypassed for testing)
- **Personal Trainer System** - Select and subscribe to personal trainers for personalized guidance
- **Enhanced Class Booking System** - Book classes with specific date/time slots, view location (online/offline), and see pricing
- **Workout Library** - Browse free and premium workouts with category filtering
- **"What Will You Do Today?"** - Category-based workout selection with two-column layout showing free/paid workouts and completed workouts
- **Trainer-Assigned Workouts** - View and complete workouts assigned by your personal trainer
- **Privacy-Protected Paid Workouts** - Free users see only workout names for paid workouts (descriptions hidden)
- Gamified tracking (points and streaks)
- QR code entry system
- Community feed and challenges
- Mark workouts as completed for daily tracking

### For Administrators
- **Staff Portal** - Frontend dashboard for daily operations
- **Enhanced Class Management** - Create classes with:
  - Paid/Free options with pricing in rupees
  - Location type (Online/Offline) with details
  - Multiple date/time schedules (up to 3 sessions per class)
  - Trainer assignment
  - Capacity management
- **Bulk Workout Creation** - Create multiple workouts at once within a category:
  - Category-first selection workflow
  - Multiple workout entry form
  - Sets-based tracking (replaced duration)
  - Difficulty levels (1-3)
  - Free/Paid access control
  - Video URL and thumbnail upload
- **Trainer Management** - Create trainers with:
  - Option to create new user accounts with username/password
  - Option to assign existing users as trainers
  - Trainer profiles with bio and specializations
- Member management with search and details
- Subscription plan management
- Workout library management
- QR code check-in system
- Email communication tools
- **Modern Professional UI** - All templates enhanced with gradients, animations, and modern design

### For Trainers
- **Trainer Portal** - View assigned classes and rosters
- **Full Workout Access** - Access to all free and paid workouts in the library
- **Individual Workout Assignment** - Assign specific workouts to clients who have subscribed to you as their personal trainer
- **Client Management** - View and manage clients who have selected you as their personal trainer
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

3. Create a `.env` file in the project root (optional - Stripe keys not required):
```
SECRET_KEY=your-secret-key-here
DEBUG=True
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

**Note for Windows PowerShell users:** If you encounter activation issues, use:
```powershell
.\venv\Scripts\python.exe manage.py runserver
```
Or set execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

## Project Structure

- `core/` - User management, subscriptions, gamification (points, streaks, QR codes)
- `bookings/` - Enhanced class booking system with:
  - ClassSchedule model for individual class sessions
  - Paid/Free class options
  - Location tracking (online/offline)
  - Multiple date/time scheduling
- `workouts/` - Workout library with:
  - Category-based bulk creation
  - Sets-based tracking (replaced duration)
  - Difficulty levels 1-3
  - Free/Paid access control
  - "What Will You Do Today?" interface
- `community/` - Social feed, challenges with auto-tracking
- `payments/` - Payment processing (Stripe bypassed - instant subscriptions)
- `staff/` - Staff Portal with enhanced management interfaces
- `templates/` - Modern HTML templates with professional design:
  - Gradient backgrounds and animations
  - Card-based layouts
  - Responsive design
  - Visual status indicators
- `static/` - Static assets (CSS, JS, images)
- `staticfiles/` - Compiled static files for production
- `media/` - User-uploaded files (workout thumbnails, trainer photos, class materials)
- `theme/` - Tailwind CSS configuration

## Key Features & Enhancements

### Class Management System
- **Paid/Free Classes**: Set classes as free or paid with pricing in rupees
- **Location Types**: Specify if classes are online (with video link) or offline (with address)
- **Multiple Schedules**: Create up to 3 specific date/time sessions per class
- **Capacity Management**: Track available spots per session
- **Visual Booking Interface**: Modern card-based booking with location indicators

### Workout Management System
- **Category-First Creation**: Select category, then create multiple workouts at once
- **Sets-Based Tracking**: Workouts use sets instead of duration
- **Difficulty Levels**: Simple 1-3 level system (replaced beginner/intermediate/advanced)
- **Bulk Creation**: Add multiple workouts in a single form submission
- **Access Control**: Free workouts for all, paid workouts require subscription

### User Workout Interface
- **"What Will You Do Today?"**: Category-based workout selection
- **Two-Column Layout**:
  - Left: Free workouts (top) and Paid workouts (bottom) with lock indicators
  - Right: Completed workouts for today
- **Payment Integration**: Direct links to upgrade for locked paid workouts
- **Daily Tracking**: Mark workouts as completed with one-click

### Visual Design Enhancements
- **Modern UI**: All templates redesigned with:
  - Gradient backgrounds and text effects
  - Card-based layouts with shadows
  - Smooth hover animations and transforms
  - Color-coded status indicators
  - Professional iconography
  - Responsive grid layouts
  - Enhanced empty states

## Payment System

**Note:** Stripe integration has been bypassed for testing purposes. All subscriptions are created instantly when users click "Subscribe Now" on any plan. No payment processing occurs - subscriptions are automatically activated.

- Users can subscribe to any plan instantly
- Subscriptions are created immediately with active status
- Period dates are calculated based on plan duration
- Existing active subscriptions are automatically cancelled when a new one is created

## Recent Enhancements (2025)

### Class System Overhaul
- ✅ Added paid/free class options with pricing in rupees
- ✅ Location tracking (online/offline) with details
- ✅ ClassSchedule model for individual sessions with specific dates/times
- ✅ Multiple schedule creation (up to 3 per class)
- ✅ Enhanced booking interface with location and schedule display
- ✅ Fixed available_spots calculation to filter by date

### Workout System Redesign
- ✅ Category-first bulk workout creation workflow
- ✅ Replaced duration with sets field
- ✅ Simplified difficulty to 1-3 levels
- ✅ Enhanced workout library with modern card design
- ✅ "What Will You Do Today?" interface for daily workout selection
- ✅ Two-column layout: workouts vs completed today
- ✅ Visual lock indicators for paid workouts

### UI/UX Enhancements
- ✅ Complete visual redesign of all templates
- ✅ Gradient backgrounds and modern styling
- ✅ Card-based layouts replacing tables
- ✅ Smooth animations and hover effects
- ✅ Professional color scheme and typography
- ✅ Enhanced empty states and loading indicators
- ✅ Responsive design improvements

### Critical Bug Fixes
- ✅ Fixed booking race condition with atomic transactions
- ✅ Fixed available_spots to filter by specific date
- ✅ Improved Stripe price validation
- ✅ Enhanced webhook error handling

### Gamification System
- ✅ Points awarded for workouts (10 pts), classes (15 pts), and check-ins (5 pts)
- ✅ Automatic streak tracking with daily validation
- ✅ Progress visualization on dashboard

### Staff & Trainer Portals
- ✅ Complete frontend for staff operations (replaces Admin-only access)
- ✅ Enhanced member management with search
- ✅ Modern class and workout management interfaces
- ✅ QR code check-in system
- ✅ Trainer attendance tracking

### Personalized Workout Plans
- ✅ Trainers create and assign custom plans to members
- ✅ Members view assigned plans on dashboard
- ✅ Custom trainer notes per member

### Personal Trainer System
- ✅ Users can select and subscribe to personal trainers
- ✅ Instant subscription activation (payment bypassed)
- ✅ Trainers have full access to all workouts (free and paid)
- ✅ Trainers can assign individual workouts to their subscribed clients
- ✅ Clients see trainer-assigned workouts on their dashboard
- ✅ Staff can create trainers with new user accounts (username/password) or assign existing users

### Workout Privacy & Access Control
- ✅ Free users see only workout names for paid workouts
- ✅ Descriptions, sets, difficulty, and thumbnails hidden for locked paid workouts
- ✅ Visual lock indicators on all locked content
- ✅ Trainers bypass all restrictions - full access to all workouts

## Database Models

### Classes
- `GymClass`: Main class model with paid/free, location, pricing
- `ClassSchedule`: Individual class sessions with date/time
- `Booking`: User bookings linked to specific schedules

### Workouts
- `Workout`: Workout model with sets, difficulty (1-3), category, free/paid
- `UserWorkoutCompletion`: Daily workout completion tracking
- `WorkoutPlan`: Trainer-created workout plans
- `UserWorkoutPlan`: Assigned plans to members
- `TrainerAssignedWorkout`: Individual workouts assigned by trainers to clients

### Personal Trainers
- `Trainer`: Trainer profiles linked to user accounts
- `PersonalTrainerSubscription`: User subscriptions to personal trainers with status, dates, and pricing

## User Roles

- **Members** - Access workouts, book classes, track progress, join challenges, view assigned workout plans, subscribe to personal trainers, view trainer-assigned workouts, use "What Will You Do Today?" interface
- **Trainers** - Manage classes, track attendance, create and assign workout plans, assign individual workouts to subscribed clients, full access to all workouts (free and paid)
- **Staff** - Full operational access via Staff Portal (member/subscription/class/trainer management, create trainers with new user accounts, QR check-in, reporting, bulk workout creation)
- **Superusers** - Django Admin access for system configuration

## Key URLs & Routes

### Public Pages
- `/` - Homepage with featured workouts
- `/register/` - User registration
- `/login/` - User login
- `/pricing/` - Membership plans
- `/about/` - About page
- `/contact/` - Contact page

### Member Pages (Login Required)
- `/dashboard/` - Member dashboard with subscriptions, bookings, and trainer info
- `/trainers/` - Select and subscribe to personal trainers
- `/workouts/` - Workout library
- `/workouts/today/` - "What Will You Do Today?" - Category-based workout selection
- `/bookings/` - Book classes
- `/bookings/my-bookings/` - View upcoming and past bookings
- `/community/` - Community feed and challenges
- `/qr-code/` - QR code for gym entry

### Staff Portal (Staff Login Required)
- `/staff/` - Staff dashboard
- `/staff/members/` - Member management
- `/staff/classes/` - Class management
- `/staff/workouts/` - Workout management
- `/staff/trainers/` - Trainer management (create trainers with new accounts)
- `/staff/plans/` - Subscription plan management
- `/staff/checkin/` - QR code check-in system

### Trainer Portal (Trainer Login Required)
- `/portal/schedule/` - View assigned classes
- `/portal/plans/` - Create and manage workout plans
- `/portal/assign-workout/` - Assign individual workouts to clients
- `/portal/classes/<id>/roster/` - View class roster and mark attendance

## Notes

- The platform uses SQLite for development (can be switched to PostgreSQL for production)
- Tailwind CSS is configured via django-tailwind
- Alpine.js is loaded via CDN for interactivity
- Payment processing bypassed - subscriptions activate instantly (for testing)
- Classes now support multiple schedules - use ClassSchedule model instead of schedule_days
- Workouts use sets instead of duration - difficulty levels are 1, 2, or 3
- **Payment System**: Stripe has been bypassed - all subscriptions activate instantly when users click "Subscribe Now"
- **Personal Trainer System**: Users can subscribe to trainers at `/trainers/` - subscriptions activate instantly (payment bypassed)
- **Trainer Workout Assignment**: Trainers can assign individual workouts to clients at `/portal/assign-workout/`
- **Workout Privacy**: Free users see only names for paid workouts - descriptions and details are hidden until they subscribe
- **Trainer Access**: Trainers automatically have full access to all workouts (free and paid) without subscription

## License

This project is for educational purposes.
