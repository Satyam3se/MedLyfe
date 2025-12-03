from django.db import models
from django.contrib.auth.models import User
import uuid

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True, blank=True)

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender_session_id = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    composition = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    # This is for the search. We'll store a simple, lowercase name.
    search_tag = models.CharField(max_length=100, unique=True, help_text="A simple lowercase name for searching, e.g., 'crocin'")

    def __str__(self):
        return self.name

class Substitute(models.Model):
    # This links every substitute back to ONE original medicine
    original_medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='substitutes')
    
    # The substitute's own details
    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    composition = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # This is the precautions field you asked for
    precautions = models.TextField(help_text="Precautions and advice for this condition.")
    
    # This links a disease to many symptoms
    symptoms = models.ManyToManyField(Symptom) 

    def __str__(self):
        return self.name

# --- New Models for Health Tracker ---

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions_given')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions_received')
    advice = models.TextField(blank=True)
    date_prescribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.patient.username} from Dr. {self.doctor.username} on {self.date_prescribed.date()}"

class PrescribedMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    duration_weeks = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.name} for {self.prescription.patient.username}"

class DosageLog(models.Model):
    prescribed_medicine = models.ForeignKey(PrescribedMedicine, on_delete=models.CASCADE, related_name='logs')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dosage_logs')
    date = models.DateField()
    taken = models.BooleanField(default=False)

    class Meta:
        unique_together = ('prescribed_medicine', 'patient', 'date')

    def __str__(self):
        return f"Log for {self.prescribed_medicine.name} on {self.date} - Taken: {self.taken}"

class WeightEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_entries')
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.weight} kg on {self.date}"

class BloodPressureEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_pressure_entries')
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    date = models.DateField()

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.systolic}/{self.diastolic} on {self.date}"

class GlucoseEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='glucose_entries')
    glucose_level = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.glucose_level} mg/dL on {self.date}"

# --- New Models for Health Tracker Goals ---
class WeightGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_goals')
    target_weight = models.DecimalField(max_digits=5, decimal_places=2)
    set_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-set_date']
        unique_together = ('user', 'is_active') # Only one active goal at a time

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate any other active goals for this user
            WeightGoal.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Weight Goal: {self.target_weight} kg (Active: {self.is_active})"

class BloodPressureGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_pressure_goals')
    target_systolic = models.IntegerField()
    target_diastolic = models.IntegerField()
    set_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-set_date']
        unique_together = ('user', 'is_active')

    def save(self, *args, **kwargs):
        if self.is_active:
            BloodPressureGoal.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s BP Goal: {self.target_systolic}/{self.target_diastolic} (Active: {self.is_active})"

class GlucoseGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='glucose_goals')
    target_glucose_level = models.DecimalField(max_digits=5, decimal_places=2)
    set_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-set_date']
        unique_together = ('user', 'is_active')

    def save(self, *args, **kwargs):
        if self.is_active:
            GlucoseGoal.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Glucose Goal: {self.target_glucose_level} mg/dL (Active: {self.is_active})"

# --- New Model for Activity Tracking ---
class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} on {self.date}"

# --- New Model for Dietary Tracking ---
class MealEntry(models.Model):
    MEAL_TYPE_CHOICES = [
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
        ('Snack', 'Snack'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_entries')
    meal_type = models.CharField(max_length=50, choices=MEAL_TYPE_CHOICES)
    food_items = models.TextField(help_text="e.g., 1 apple, 2 slices of bread with butter")
    calories = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}'s {self.meal_type} on {self.date}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_patient')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_doctor')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('doctor', 'date', 'start_time') # Ensure a doctor can't have overlapping appointments

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.username} for {self.patient.username} on {self.date} at {self.start_time}"