from django.shortcuts import render, redirect
from .models import Medicine
from django.http import JsonResponse
import json
from .models import Room, Message
import uuid
from datetime import date, timedelta # Added for date calculations

def index_view(request):
    return render(request, 'index.html')

def virtual_view(request):
    return render(request, 'virtual1.html')

def fundraise_view(request):
    return render(request, 'fundraise.html')

# DELETED: Old health_tracker_view content.

def diagnose_view(request):
    return render(request, 'symptom_checker.html')

def government_scheme_view(request):
    return render(request, 'schemes.html')

def contact_view(request):
    return render(request, 'contact.html')

def login_view(request):
    return render(request, 'login.html')

def eih_view(request):
    return render(request, 'eih.html')

# New views for footer links
def about_us_view(request):
    return render(request, 'about.html')

def privacy_policy_view(request):
    return render(request, 'privacy.html')

def terms_of_service_view(request):
    return render(request, 'terms.html')

def create_room_view(request):
    room = Room.objects.create()
    return redirect('call_page', room_id=room.id)

def signaling_view(request, room_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = Room.objects.get(id=room_id)
            sender_session_id = request.session.session_key
            if not sender_session_id:
                request.session.save()
                sender_session_id = request.session.session_key

            Message.objects.create(
                room=room,
                sender_session_id=sender_session_id,
                message=json.dumps(data)
            )
            return JsonResponse({'status': 'ok'})
        except (Room.DoesNotExist, json.JSONDecodeError):
            return JsonResponse({'status': 'error'}, status=400)

    elif request.method == 'GET':
        try:
            room = Room.objects.get(id=room_id)
            sender_session_id = request.session.session_key
            messages = room.messages.exclude(sender_session_id=sender_session_id).order_by('created_at')
            
            message_list = []
            for msg in messages:
                try:
                    message_content = json.loads(msg.message)
                    message_list.append(message_content)
                except json.JSONDecodeError:
                    message_list.append(msg.message)

            messages.delete()

            return JsonResponse(message_list, safe=False)
        except Room.DoesNotExist:
            return JsonResponse([], safe=False)

def call_view(request, room_id):
    context = {
        'room_id': room_id
    }
    return render(request, 'call.html', context)

def consultation_view(request):
    return render(request, 'consultation.html')

def substitute_view(request):
    """This is the view for your substitute medicine page."""
    context = {}
    all_medicines = Medicine.objects.all().order_by('name') # Fetch all medicines, ordered alphabetically

    if request.method == 'POST':
        search_query = request.POST.get('medicine_name', '').lower()
        context['search_query'] = search_query

        if search_query:
            try:
                medicine = Medicine.objects.get(search_tag=search_query)
                context['results'] = {
                    'original': medicine,
                    'substitutes': medicine.substitutes.all()
                }
            except Medicine.DoesNotExist:
                context['error'] = f"Sorry, '{search_query}' not found in our database."
        else:
            context['error'] = "Please enter a medicine name to search."
            
    context['all_medicines'] = all_medicines # Always include all medicines in context
    return render(request, 'substitute1.html', context)

# (Your other imports like 'render' and 'Medicine' are already here)
from .models import Symptom, Disease  # <-- ADD Symptom & Disease to your imports
from django.db.models import Count     # <-- ADD this new import

#
# (Your index_view, call_page_view, and substitute_view functions are here)
#

# --- ADD THIS NEW FUNCTION AT THE BOTTOM ---

def symptom_checker_view(request):
    """
    This is the view for your AI Symptom Checker.
    """
    
    # First, get all symptoms from the database to display on the page
    all_symptoms = Symptom.objects.all()
    
    context = {
        'all_symptoms': all_symptoms,
        'results': None
    }

    if request.method == 'POST':
        # Get the list of symptom IDs that the user checked
        selected_symptom_ids = request.POST.getlist('symptom_ids')
        
        if selected_symptom_ids:
            # Convert IDs from strings to integers
            selected_symptom_ids = [int(id) for id in selected_symptom_ids]
            
            # This is the core logic:
            # 1. Find diseases that have at least one of the selected symptoms.
            # 2. Group them by the disease.
            # 3. Count how many of the selected symptoms each disease has.
            # 4. Order them so the best match (highest count) is first.
            matching_diseases = Disease.objects.filter(
                symptoms__id__in=selected_symptom_ids
            ).annotate(
                symptom_match_count=Count('id')
            ).order_by('-symptom_match_count')

            context['results'] = matching_diseases
            
            # This will help us re-check the boxes after the search
            context['selected_ids'] = selected_symptom_ids

    return render(request, 'symptom_checker.html', context)

# --- New Views for Health Tracker ---
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from users.models import Profile
from .forms import PrescriptionForm, PrescribedMedicineForm, AppointmentForm
from .models import Prescription, PrescribedMedicine, DosageLog, WeightEntry, BloodPressureEntry, GlucoseEntry, WeightGoal, BloodPressureGoal, GlucoseGoal, Activity, MealEntry, Appointment # MealEntry added
from django.db import transaction
from django.forms import inlineformset_factory
from functools import wraps

def doctor_required(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login') # Redirect to login if not authenticated
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'doctor':
            # You might want to render a 403 page or redirect to a more appropriate place
            return redirect('index') # Redirect to home if not a doctor
        return function(request, *args, **kwargs)
    return wrapper

def patient_required(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login') # Redirect to login if not authenticated
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'user':
            return redirect('index') # Redirect to home if not a patient
        return function(request, *args, **kwargs)
    return wrapper


@login_required
@doctor_required
def create_prescription_view(request):
    PrescribedMedicineFormSet = inlineformset_factory(
        Prescription, PrescribedMedicine, form=PrescribedMedicineForm, extra=1, can_delete=True
    )
    
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        # Pass instance=prescription to formset later
        formset = PrescribedMedicineFormSet(request.POST, request.FILES, instance=Prescription()) 

        if prescription_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                prescription = prescription_form.save(commit=False)
                prescription.doctor = request.user # The logged-in user is the doctor
                prescription.save()

                formset.instance = prescription # Link formset to the new prescription
                formset.save()
            
            # Redirect to a success page or doctor's dashboard
            return redirect('index') # Placeholder for now
    else:
        prescription_form = PrescriptionForm()
        formset = PrescribedMedicineFormSet(instance=Prescription())

    context = {
        'prescription_form': prescription_form,
        'formset': formset,
    }
    return render(request, 'create_prescription.html', context)


@login_required
@patient_required
def health_tracker_view(request):
    patient_prescriptions = Prescription.objects.filter(patient=request.user).order_by('-date_prescribed')
    
    prescriptions_data = []
    for prescription in patient_prescriptions:
        medicines_data = []
        for medicine in prescription.medicines.all(): # .medicines is the related_name from PrescribedMedicine
            
            # Calculate the duration of the dosage
            start_date = prescription.date_prescribed.date()
            end_date = start_date + timedelta(weeks=medicine.duration_weeks)
            
            # Generate dates for the tracking period
            dates_in_period = []
            current_date = start_date
            while current_date < end_date:
                # Check if a DosageLog entry exists for this date
                log_entry, created = DosageLog.objects.get_or_create(
                    prescribed_medicine=medicine,
                    patient=request.user,
                    date=current_date
                )
                dates_in_period.append({'date': current_date, 'taken': log_entry.taken})
                current_date += timedelta(days=1)

            medicines_data.append({
                'medicine_obj': medicine,
                'dates_in_period': dates_in_period,
            })
        prescriptions_data.append({
            'prescription_obj': prescription,
            'medicines': medicines_data,
        })
    
    weight_data = WeightEntry.objects.filter(user=request.user).order_by('date') # Order by date ascending for charts
    blood_pressure_data = BloodPressureEntry.objects.filter(user=request.user).order_by('date')
    glucose_data = GlucoseEntry.objects.filter(user=request.user).order_by('date')

    # Prepare data for Chart.js
    weight_dates = [entry.date.strftime('%Y-%m-%d') for entry in weight_data]
    weight_values = [float(entry.weight) for entry in weight_data]

    bp_dates = [entry.date.strftime('%Y-%m-%d') for entry in blood_pressure_data]
    bp_systolic_values = [entry.systolic for entry in blood_pressure_data]
    bp_diastolic_values = [entry.diastolic for entry in blood_pressure_data]

    glucose_dates = [entry.date.strftime('%Y-%m-%d') for entry in glucose_data]
    glucose_values = [float(entry.glucose_level) for entry in glucose_data]

    # Fetch active goals
    active_weight_goal = WeightGoal.objects.filter(user=request.user, is_active=True).first()
    active_blood_pressure_goal = BloodPressureGoal.objects.filter(user=request.user, is_active=True).first()
    active_glucose_goal = GlucoseGoal.objects.filter(user=request.user, is_active=True).first()

    # Fetch activity data
    activity_data = Activity.objects.filter(user=request.user).order_by('date')
    activity_dates = [entry.date.strftime('%Y-%m-%d') for entry in activity_data]
    activity_types = [entry.activity_type for entry in activity_data]
    activity_durations = [entry.duration_minutes for entry in activity_data]
    activity_calories = [entry.calories_burned if entry.calories_burned else 0 for entry in activity_data]

    # Fetch meal data
    meal_data = MealEntry.objects.filter(user=request.user).order_by('date')
    meal_dates = [entry.date.strftime('%Y-%m-%d') for entry in meal_data]
    meal_calories = [entry.calories if entry.calories else 0 for entry in meal_data]

    # BMI Calculation
    bmi = None
    user_height = request.user.profile.height_cm if hasattr(request.user, 'profile') and request.user.profile.height_cm else None
    
    if user_height and weight_data:
        latest_weight = weight_data.last().weight # Assuming weight_data is ordered by date ascending
        height_meters = float(user_height) / 100 # Convert cm to meters
        bmi = round(float(latest_weight) / (height_meters ** 2), 2)

    # BMI Calculation
    bmi = None
    user_height = request.user.profile.height_cm if hasattr(request.user, 'profile') and request.user.profile.height_cm else None
    
    if user_height and weight_data:
        latest_weight = weight_data.last().weight # Assuming weight_data is ordered by date ascending
        height_meters = float(user_height) / 100 # Convert cm to meters
        bmi = round(float(latest_weight) / (height_meters ** 2), 2)

    context = {
        'prescriptions_data': prescriptions_data,
        'weight_data': weight_data,
        'blood_pressure_data': blood_pressure_data,
        'glucose_data': glucose_data,
        'weight_chart_data': json.dumps({'dates': weight_dates, 'values': weight_values}),
        'bp_chart_data': json.dumps({'dates': bp_dates, 'systolic': bp_systolic_values, 'diastolic': bp_diastolic_values}),
        'glucose_chart_data': json.dumps({'dates': glucose_dates, 'values': glucose_values}),
        'active_weight_goal': active_weight_goal,
        'active_blood_pressure_goal': active_blood_pressure_goal,
        'active_glucose_goal': active_glucose_goal,
        'activity_data': activity_data,
        'activity_chart_data': json.dumps({
            'dates': activity_dates,
            'types': activity_types,
            'durations': activity_durations,
            'calories': activity_calories
        }),
        'meal_data': meal_data,
        'meal_chart_data': json.dumps({
            'dates': meal_dates,
            'calories': meal_calories
        }),
        'user_height': user_height,
        'bmi': bmi,
    }
    return render(request, 'tracker.html', context)


@login_required
@patient_required
def update_dosage_log_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            medicine_id = data.get('medicine_id')
            log_date_str = data.get('date')
            taken = data.get('taken')

            log_date = date.fromisoformat(log_date_str) # Convert string to date object

            prescribed_medicine = PrescribedMedicine.objects.get(id=medicine_id)
            
            # Ensure the medicine belongs to a prescription for this patient
            if prescribed_medicine.prescription.patient != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized access to medicine.'}, status=403)

            dosage_log, created = DosageLog.objects.get_or_create(
                prescribed_medicine=prescribed_medicine,
                patient=request.user,
                date=log_date
            )
            dosage_log.taken = taken
            dosage_log.save()

            return JsonResponse({'status': 'success', 'message': 'Dosage log updated.'})

        except PrescribedMedicine.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Medicine not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
@patient_required
def add_weight(request):
    if request.method == 'POST':
        weight = request.POST.get('weight')
        date_str = request.POST.get('date')
        if weight and date_str:
            try:
                date_obj = date.fromisoformat(date_str)
                WeightEntry.objects.create(user=request.user, weight=weight, date=date_obj)
            except ValueError:
                pass # Handle invalid date format
    return redirect('health_tracker')

@login_required
@patient_required
def delete_weight(request, pk):
    if request.method == 'POST':
        try:
            weight_entry = WeightEntry.objects.get(pk=pk, user=request.user)
            weight_entry.delete()
        except WeightEntry.DoesNotExist:
            pass
    return redirect('health_tracker')

@login_required
@patient_required
def add_blood_pressure(request):
    if request.method == 'POST':
        systolic = request.POST.get('systolic')
        diastolic = request.POST.get('diastolic')
        date_str = request.POST.get('date')
        if systolic and diastolic and date_str:
            try:
                date_obj = date.fromisoformat(date_str)
                BloodPressureEntry.objects.create(user=request.user, systolic=systolic, diastolic=diastolic, date=date_obj)
            except ValueError:
                pass
    return redirect('health_tracker')

@login_required
@patient_required
def delete_blood_pressure(request, pk):
    if request.method == 'POST':
        try:
            bp_entry = BloodPressureEntry.objects.get(pk=pk, user=request.user)
            bp_entry.delete()
        except BloodPressureEntry.DoesNotExist:
            pass
    return redirect('health_tracker')

@login_required
@patient_required
def add_glucose(request):
    if request.method == 'POST':
        glucose_level = request.POST.get('glucose_level')
        date_str = request.POST.get('date')
        if glucose_level and date_str:
            try:
                date_obj = date.fromisoformat(date_str)
                GlucoseEntry.objects.create(user=request.user, glucose_level=glucose_level, date=date_obj)
            except ValueError:
                pass
    return redirect('health_tracker')

@login_required
@patient_required
def delete_glucose(request, pk):
    if request.method == 'POST':
        try:
            glucose_entry = GlucoseEntry.objects.get(pk=pk, user=request.user)
            glucose_entry.delete()
        except GlucoseEntry.DoesNotExist:
            pass
    return redirect('health_tracker')

@login_required
@patient_required
def set_weight_goal(request):
    if request.method == 'POST':
        target_weight = request.POST.get('target_weight')
        if target_weight:
            # Deactivate any existing active weight goals for the user
            WeightGoal.objects.filter(user=request.user, is_active=True).update(is_active=False)
            # Create a new active weight goal
            WeightGoal.objects.create(user=request.user, target_weight=target_weight, is_active=True)
    return redirect('health_tracker')

@login_required
@patient_required
def set_blood_pressure_goal(request):
    if request.method == 'POST':
        target_systolic = request.POST.get('target_systolic')
        target_diastolic = request.POST.get('target_diastolic')
        if target_systolic and target_diastolic:
            # Deactivate any existing active BP goals for the user
            BloodPressureGoal.objects.filter(user=request.user, is_active=True).update(is_active=False)
            # Create a new active BP goal
            BloodPressureGoal.objects.create(user=request.user, target_systolic=target_systolic, target_diastolic=target_diastolic, is_active=True)
    return redirect('health_tracker')

@login_required
@patient_required
def set_glucose_goal(request):
    if request.method == 'POST':
        target_glucose_level = request.POST.get('target_glucose_level')
        if target_glucose_level:
            # Deactivate any existing active glucose goals for the user
            GlucoseGoal.objects.filter(user=request.user, is_active=True).update(is_active=False)
            # Create a new active glucose goal
            GlucoseGoal.objects.create(user=request.user, target_glucose_level=target_glucose_level, is_active=True)
    return redirect('health_tracker')


@login_required
@patient_required
def add_activity(request):
    if request.method == 'POST':
        activity_type = request.POST.get('activity_type')
        duration_minutes = request.POST.get('duration_minutes')
        calories_burned = request.POST.get('calories_burned')
        date_str = request.POST.get('date')

        if activity_type and duration_minutes and date_str:
            try:
                date_obj = date.fromisoformat(date_str)
                Activity.objects.create(
                    user=request.user,
                    activity_type=activity_type,
                    duration_minutes=duration_minutes,
                    calories_burned=calories_burned if calories_burned else None,
                    date=date_obj
                )
            except ValueError:
                pass # Handle invalid date/number format
    return redirect('health_tracker')

@login_required
@patient_required
def delete_activity(request, pk):
    if request.method == 'POST':
        try:
            activity_entry = Activity.objects.get(pk=pk, user=request.user)
            activity_entry.delete()
        except Activity.DoesNotExist:
            pass
    return redirect('health_tracker')

@login_required
@patient_required
def add_meal(request):
    if request.method == 'POST':
        meal_type = request.POST.get('meal_type')
        food_items = request.POST.get('food_items')
        calories = request.POST.get('calories')
        date_str = request.POST.get('date')

        if meal_type and food_items and date_str:
            try:
                date_obj = date.fromisoformat(date_str)
                MealEntry.objects.create(
                    user=request.user,
                    meal_type=meal_type,
                    food_items=food_items,
                    calories=calories if calories else None,
                    date=date_obj
                )
            except ValueError:
                pass
    return redirect('health_tracker')

@login_required
@patient_required
def delete_meal(request, pk):
    if request.method == 'POST':
        try:
            meal_entry = MealEntry.objects.get(pk=pk, user=request.user)
            meal_entry.delete()
        except MealEntry.DoesNotExist:
            pass
    return redirect('health_tracker')

@login_required
def appointment_list(request):
    if hasattr(request.user, 'profile'):
        if request.user.profile.user_type == 'doctor':
            appointments = Appointment.objects.filter(doctor=request.user).order_by('-date', '-start_time')
            template_name = 'doctor_appointments.html' # Create this template
        else: # user is a patient
            appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-start_time')
            template_name = 'patient_appointments.html' # Create this template
    else:
        appointments = Appointment.objects.none() # No profile, no appointments
        template_name = 'patient_appointments.html' # Default to patient view

    context = {
        'appointments': appointments
    }
    return render(request, template_name, context)

@login_required
@patient_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()
            return redirect('appointment_list') # Redirect to appointment list
    else:
        form = AppointmentForm()
    
    context = {
        'form': form
    }
    return render(request, 'create_appointment.html', context) # Create this template

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Ensure only patient or doctor involved in the appointment can see details
    if not (request.user == appointment.patient or request.user == appointment.doctor):
        return redirect('appointment_list') # Or render 403 Forbidden

    context = {
        'appointment': appointment
    }
    return render(request, 'appointment_detail.html', context) # Create this template


@login_required
@doctor_required
def update_appointment_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in Appointment.STATUS_CHOICES]:
            appointment.status = new_status
            appointment.save()
            # Add message framework for feedback if needed
    return redirect('appointment_detail', pk=pk)


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Only patient or doctor can cancel
    if not (request.user == appointment.patient or request.user == appointment.doctor):
        return redirect('appointment_list')

    if request.method == 'POST':
        # Prevent cancellation of completed appointments (optional)
        if appointment.status not in ['Completed', 'Cancelled']:
            appointment.status = 'Cancelled'
            appointment.save()
            # Add message framework for feedback if needed
    return redirect('appointment_list')

from django.http import HttpResponse
import csv
from django.shortcuts import get_object_or_404 # Added for appointment_detail view

@login_required
@patient_required
def export_health_data_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="health_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data Type', 'Date', 'Value1', 'Value2', 'Value3', 'Description']) # Header row

    # Weight Data
    weight_data = WeightEntry.objects.filter(user=request.user).order_by('date')
    for entry in weight_data:
        writer.writerow(['Weight', entry.date, entry.weight, '', '', ''])

    # Blood Pressure Data
    blood_pressure_data = BloodPressureEntry.objects.filter(user=request.user).order_by('date')
    for entry in blood_pressure_data:
        writer.writerow(['Blood Pressure', entry.date, entry.systolic, entry.diastolic, '', ''])

    # Glucose Data
    glucose_data = GlucoseEntry.objects.filter(user=request.user).order_by('date')
    for entry in glucose_data:
        writer.writerow(['Glucose', entry.date, entry.glucose_level, '', '', ''])
    
    # Activity Data
    activity_data = Activity.objects.filter(user=request.user).order_by('date')
    for entry in activity_data:
        writer.writerow(['Activity', entry.date, entry.duration_minutes, entry.calories_burned if entry.calories_burned else '', entry.activity_type, ''])

    # Meal Data
    meal_data = MealEntry.objects.filter(user=request.user).order_by('date')
    for entry in meal_data:
        writer.writerow(['Meal', entry.date, entry.calories if entry.calories else '', entry.meal_type, entry.food_items, ''])
        
    return response

@login_required
@patient_required
def update_height(request):
    if request.method == 'POST':
        height_cm = request.POST.get('height_cm')
        if height_cm:
            try:
                profile = request.user.profile
                profile.height_cm = float(height_cm)
                profile.save()
            except (ValueError, Profile.DoesNotExist):
                pass
    return redirect('health_tracker')
