from django import forms
from django.contrib.auth.models import User
from .models import Prescription, PrescribedMedicine, Appointment
from users.models import Profile

class PrescriptionForm(forms.ModelForm):
    # Filter patients to only show users with 'user_type' == 'user'
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__user_type='user'),
        empty_label="Select Patient",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Prescription
        fields = ['patient', 'advice']
        widgets = {
            'advice': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PrescribedMedicineForm(forms.ModelForm):
    class Meta:
        model = PrescribedMedicine
        fields = ['name', 'dosage', 'duration_weeks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__user_type='doctor'),
        empty_label="Select Doctor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'start_time', 'end_time', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        doctor = cleaned_data.get('doctor')

        if start_time and end_time:
            if start_time >= end_time:
                self.add_error('end_time', "End time must be after start time.")

        if date and start_time and end_time and doctor:
            # Check for overlapping appointments for the selected doctor
            overlapping_appointments = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk if self.instance else None) # Exclude self when updating

            if overlapping_appointments.exists():
                self.add_error(None, "This doctor has an overlapping appointment at the requested time.")

        return cleaned_data
