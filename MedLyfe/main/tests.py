from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from datetime import date
from .models import WeightEntry, WeightGoal, BloodPressureEntry, GlucoseEntry, BloodPressureGoal, GlucoseGoal, Activity, MealEntry
from users.models import Profile

User = get_user_model()

class HealthTrackerModelsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        Profile.objects.create(user=self.user, user_type='user', height_cm=170) # Create profile for BMI test

    def test_weight_entry_creation(self):
        weight_entry = WeightEntry.objects.create(user=self.user, weight=70.5, date=date(2023, 1, 1))
        self.assertEqual(weight_entry.user, self.user)
        self.assertEqual(weight_entry.weight, 70.5)
        self.assertEqual(weight_entry.date, date(2023, 1, 1))
        self.assertEqual(str(weight_entry), 'testuser - 70.5 kg on 2023-01-01')

    def test_weight_goal_creation_and_active_status(self):
        # Create an initial active goal
        goal1 = WeightGoal.objects.create(user=self.user, target_weight=65.0, is_active=True)
        self.assertEqual(goal1.target_weight, 65.0)
        self.assertTrue(goal1.is_active)

        # Create a new active goal, which should deactivate the previous one
        goal2 = WeightGoal.objects.create(user=self.user, target_weight=60.0, is_active=True)
        self.assertTrue(goal2.is_active)
        # Re-fetch goal1 to check its active status
        goal1.refresh_from_db()
        self.assertFalse(goal1.is_active)

    def test_blood_pressure_entry_creation(self):
        bp_entry = BloodPressureEntry.objects.create(user=self.user, systolic=120, diastolic=80, date=date(2023, 1, 1))
        self.assertEqual(bp_entry.user, self.user)
        self.assertEqual(bp_entry.systolic, 120)
        self.assertEqual(bp_entry.diastolic, 80)
        self.assertEqual(bp_entry.date, date(2023, 1, 1))
        self.assertEqual(str(bp_entry), 'testuser - 120/80 on 2023-01-01')

    def test_glucose_entry_creation(self):
        glucose_entry = GlucoseEntry.objects.create(user=self.user, glucose_level=95.5, date=date(2023, 1, 1))
        self.assertEqual(glucose_entry.user, self.user)
        self.assertEqual(glucose_entry.glucose_level, 95.5)
        self.assertEqual(glucose_entry.date, date(2023, 1, 1))
        self.assertEqual(str(glucose_entry), 'testuser - 95.5 mg/dL on 2023-01-01')

    def test_activity_creation(self):
        activity = Activity.objects.create(user=self.user, activity_type='Running', duration_minutes=30, calories_burned=300, date=date(2023, 1, 1))
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.activity_type, 'Running')
        self.assertEqual(activity.duration_minutes, 30)
        self.assertEqual(activity.calories_burned, 300)
        self.assertEqual(activity.date, date(2023, 1, 1))
        self.assertEqual(str(activity), 'testuser - Running on 2023-01-01')

    def test_meal_entry_creation(self):
        meal = MealEntry.objects.create(user=self.user, meal_type='Breakfast', food_items='Oatmeal, Banana', calories=350, date=date(2023, 1, 1))
        self.assertEqual(meal.user, self.user)
        self.assertEqual(meal.meal_type, 'Breakfast')
        self.assertEqual(meal.food_items, 'Oatmeal, Banana')
        self.assertEqual(meal.calories, 350)
        self.assertEqual(meal.date, date(2023, 1, 1))
        self.assertEqual(str(meal), "testuser's Breakfast on 2023-01-01")


class HealthTrackerViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user, user_type='user', height_cm=170)

    def test_health_tracker_view_context_and_bmi(self):
        WeightEntry.objects.create(user=self.user, weight=70.0, date=date(2023, 1, 1))
        response = self.client.get('/tracker/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('weight_data', response.context)
        self.assertIn('bmi', response.context)
        self.assertAlmostEqual(response.context['bmi'], 70.0 / ((170/100)**2), places=2)

    def test_add_weight_view(self):
        response = self.client.post('/health_tracker/add_weight/', {'weight': 71.0, 'date': '2023-01-02'})
        self.assertEqual(response.status_code, 302) # Redirect
        self.assertEqual(WeightEntry.objects.filter(user=self.user).count(), 1)
        self.assertEqual(WeightEntry.objects.get(user=self.user).weight, 71.0)

    def test_set_weight_goal_view(self):
        response = self.client.post('/health_tracker/set_weight_goal/', {'target_weight': 68.0})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(WeightGoal.objects.filter(user=self.user, is_active=True).count(), 1)
        self.assertEqual(WeightGoal.objects.get(user=self.user, is_active=True).target_weight, 68.0)

        # Set another goal, previous should be inactive
        self.client.post('/health_tracker/set_weight_goal/', {'target_weight': 67.0})
        self.assertEqual(WeightGoal.objects.filter(user=self.user, is_active=True).count(), 1)
        self.assertEqual(WeightGoal.objects.get(user=self.user, is_active=True).target_weight, 67.0)
        self.assertEqual(WeightGoal.objects.filter(user=self.user, is_active=False).count(), 1)

    def test_export_health_data_csv_view(self):
        WeightEntry.objects.create(user=self.user, weight=70.0, date=date(2023, 1, 1))
        BloodPressureEntry.objects.create(user=self.user, systolic=120, diastolic=80, date=date(2023, 1, 1))
        response = self.client.get('/health_tracker/export_csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="health_data.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Weight,2023-01-01,70.00,,,\r\n', content)
        self.assertIn('Blood Pressure,2023-01-01,120,80,,\r\n', content)