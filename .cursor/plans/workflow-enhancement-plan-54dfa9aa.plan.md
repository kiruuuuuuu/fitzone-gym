<!-- 54dfa9aa-d14e-441a-934a-0507f2d86a54 fe2dbe7c-adad-421f-a243-d5bf38d39f45 -->
# Workflow Enhancement Plan

## Priority 1: Connect Gamification to Community Challenges

### Problem

UserChallenge progress is never updated when users earn points, making challenge leaderboards always empty.

### Solution

Modify `core/utils.py` to update active challenges when points are awarded.

**File: core/utils.py**

- Import `UserChallenge` from community.models
- In `award_points_and_update_streak()`, add logic after point creation:
- Query active UserChallenge objects for the user
- Match challenge.goal_type with point source:
  - 'visits' matches 'checkin'
  - 'workouts' matches 'workout'
  - 'points' matches any source (increment by points value)
- Update user_challenge.progress and save
- Note: 'streak' type requires separate handling (can be synced from UserStreak.current_streak)

## Priority 2: Validate Class Booking by Weekday

### Problem

Users can book classes on invalid days (e.g., book Monday Yoga on Tuesday).

### Solution

Add weekday validation in booking flow.

**File: bookings/views.py**

- In `book_class()` POST handler:
- Parse booking_date string to date object
- Extract weekday name (e.g., "monday")
- Split gym_class.schedule_days by comma
- Check if weekday_name is in valid_days list
- Return error message if invalid day selected
- Use parsed date object (not string) for Booking.objects.create()

## Priority 3: Complete Staff Portal with Trainer & Challenge CRUD

### Problem

Staff must still use Django Admin to create Trainers and Challenges.

### Solution

Add full CRUD operations for Trainer and Challenge models to staff portal.

**File: staff/views.py**

Add views:

- `TrainerListView` - Display all trainers
- `trainer_create()` - Create trainer (select from users without trainer_profile)
- `trainer_edit()` - Edit trainer details
- `ChallengeListView` - Display all challenges
- `challenge_create()` - Create new challenge with form validation
- `challenge_edit()` - Edit existing challenge

**File: staff/urls.py**

- Add URL patterns for trainer and challenge views

**New Template Files:**

- `templates/staff/trainer_list.html` - List trainers with edit links
- `templates/staff/trainer_form.html` - Create/edit trainer form
- `templates/staff/challenge_list.html` - List challenges with edit links
- `templates/staff/challenge_form.html` - Create/edit challenge form

**Update: templates/staff/dashboard.html**

- Add quick action buttons for "Create Trainer" and "Create Challenge"

## Priority 4: Add Manual Staff Actions to Member Detail

### Problem

Staff cannot take manual actions (award bonus points, manage subscriptions) from member detail page.

### Solution

Add action forms and handlers to member detail view.

**File: staff/views.py**

Add new views:

- `add_manual_points(request, user_id)` - POST handler to award manual points
- Call `award_points_and_update_streak()` with custom description
- Redirect back to member detail with success message
- `manage_subscription(request, user_id)` - Handle manual subscription changes
- Allow staff to create new subscription (for cash payments)
- Allow status changes (activate/cancel)
- Redirect back to member detail

**File: staff/urls.py**

- Add URL patterns for manual actions

**Create: templates/staff/member_detail.html**

- Display all member information (subscriptions, bookings, points, streak)
- Add "Award Bonus Points" form section with fields: points (number), description (text)
- Add "Manage Subscription" section with plan selector and status controls
- Both forms POST to respective handler views

## Priority 5: Add Reporting Dashboard

### Problem

No visualization of business metrics despite collecting extensive data.

### Solution

Create analytics dashboard with Chart.js visualizations.

**File: staff/views.py**

Add view:

- `reports_dashboard()` - Aggregate and prepare data:
- MRR: Sum of active subscription prices
- Member growth: Count by month
- Class popularity: Classes ordered by booking count
- Trainer performance: Classes taught and attendance rates
- Pass data as JSON to template

**File: staff/urls.py**

- Add URL pattern for reports page

**Create: templates/staff/reports.html**

- Include Chart.js CDN
- Create canvas elements for each chart
- Add JavaScript to render:
- Line chart: MRR over time
- Bar chart: Class popularity
- Bar chart: Trainer performance
- Pie chart: Active vs inactive members

**Update: templates/staff/dashboard.html**

- Add "View Reports" button in quick actions

## Implementation Order

1. Challenge integration (highest impact) - COMPLETED
2. Booking validation (user-facing bug fix) - COMPLETED
3. Trainer/Challenge CRUD (complete portal) - COMPLETED
4. Manual staff actions (operational necessity) - COMPLETED
5. Reporting dashboard (polish feature) - COMPLETED
6. **Personalized Workout Plans (capstone feature)** - NEW

## Priority 6: Personalized Workout Plans (Capstone Feature)

### Problem

Trainers cannot create personalized workout plans for members. Members can only browse the full workout library without guidance.

### Solution

Create a system for trainers to build workout plans from existing workouts and assign them to specific members.

**Step 1: Create New Models**

File: `workouts/models.py`

Add two new models:

- `WorkoutPlan` - Template created by trainer with name, description, and ManyToMany to Workout
- `UserWorkoutPlan` - Assignment linking user to plan with notes and assigned_at timestamp

**Step 2: Database Migration**

Run:

```bash
python manage.py makemigrations workouts
python manage.py migrate
```

**Step 3: Trainer Portal Enhancement**

File: `staff/urls_trainer.py`

Add URL patterns:

- `plans/` - List trainer's workout plans
- `plans/create/` - Create new plan
- `plans/<int:plan_id>/edit/` - Edit existing plan
- `plans/<int:plan_id>/assign/` - Assign plan to member

File: `staff/views.py`

Add views:

- `TrainerPlanListView` - Display trainer's workout plans
- `trainer_plan_create()` - Form with ModelMultipleChoiceField for workouts (CheckboxSelectMultiple widget)
- `trainer_plan_edit()` - Edit plan details and workout selection
- `trainer_plan_assign()` - Form to select member and add assignment notes

**Step 4: Member Dashboard Enhancement**

File: `core/views.py`

Update `dashboard()` view:

- Add `assigned_plans` to context: `UserWorkoutPlan.objects.filter(user=user).select_related('plan')`

File: `templates/dashboard.html`

Add section:

- "My Assigned Workout Plans" with cards showing:
  - Plan name and description
  - Trainer who assigned it
  - Trainer's notes
  - List of workouts in plan (linked to workout detail pages)

**New Template Files:**

- `templates/trainer/plan_list.html` - List trainer's plans
- `templates/trainer/plan_form.html` - Create/edit plan form
- `templates/trainer/plan_assign.html` - Assign plan to member form

## Key Files to Modify

### Already Modified (Priorities 1-5)

- core/utils.py
- bookings/views.py
- staff/views.py
- staff/urls.py
- templates/staff/dashboard.html
- templates/staff/member_detail.html (created)
- templates/staff/trainer_list.html (created)
- templates/staff/trainer_form.html (created)
- templates/staff/challenge_list.html (created)
- templates/staff/challenge_form.html (created)
- templates/staff/reports.html (created)

### To Modify (Priority 6)

- workouts/models.py (add WorkoutPlan and UserWorkoutPlan)
- staff/views.py (add 4 trainer plan views)
- staff/urls_trainer.py (add plan URLs)
- core/views.py (update dashboard context)
- templates/dashboard.html (add assigned plans section)
- templates/trainer/plan_list.html (create)
- templates/trainer/plan_form.html (create)
- templates/trainer/plan_assign.html (create)

### To-dos

- [ ] Connect gamification to challenge progress tracking in core/utils.py
- [ ] Add weekday validation to class booking in bookings/views.py
- [ ] Add Trainer CRUD views and templates to staff portal
- [ ] Add Challenge CRUD views and templates to staff portal
- [ ] Add manual points and subscription management to member detail page
- [ ] Create analytics dashboard with Chart.js visualizations