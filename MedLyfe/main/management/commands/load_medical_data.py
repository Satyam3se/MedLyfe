from django.core.management.base import BaseCommand
from main.models import Symptom, Disease

class Command(BaseCommand):
    help = 'Loads a predefined set of medical data (symptoms and diseases) into the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to load medical data...'))

        # Data structure: { 'disease_name': { 'symptoms': [], 'description': '...', 'precautions': '...' } }
        medical_data = {
            'Common Cold': {
                'symptoms': ['Runny or stuffy nose', 'Sore throat', 'Cough', 'Sneezing', 'Mild body aches'],
                'description': 'A common viral infection of the nose and throat.',
                'precautions': 'Rest, drink plenty of fluids, and use over-the-counter medications to relieve symptoms. Wash hands frequently to prevent spreading.'
            },
            'Influenza (Flu)': {
                'symptoms': ['Fever', 'Chills', 'Muscle aches', 'Headache', 'Fatigue', 'Cough', 'Sore throat'],
                'description': 'A contagious respiratory illness caused by influenza viruses.',
                'precautions': 'Get an annual flu shot. Rest, stay hydrated, and take antiviral medications if prescribed by a doctor.'
            },
            'Migraine': {
                'symptoms': ['Severe throbbing pain', 'Nausea', 'Vomiting', 'Sensitivity to light and sound'],
                'description': 'A type of headache that can cause severe throbbing pain or a pulsing sensation, usually on one side of the head.',
                'precautions': 'Identify and avoid triggers. Rest in a dark, quiet room during an attack. Medications can help manage symptoms.'
            },
            'Gastroenteritis (Stomach Flu)': {
                'symptoms': ['Diarrhea', 'Vomiting', 'Stomach cramps', 'Nausea', 'Fever'],
                'description': 'An inflammation of the stomach and intestines, typically caused by a viral or bacterial infection.',
                'precautions': 'Stay hydrated by drinking plenty of fluids like water or oral rehydration solutions. Gradually reintroduce bland foods. Wash hands thoroughly.'
            },
            'Allergic Rhinitis (Hay Fever)': {
                'symptoms': ['Sneezing', 'Runny or stuffy nose', 'Itchy or watery eyes', 'Itchy throat'],
                'description': 'An allergic response to airborne allergens, like pollen, dust mites, or pet dander.',
                'precautions': 'Avoid known allergens. Use antihistamines or nasal corticosteroid sprays as recommended by a doctor.'
            },
            'Asthma': {
                'symptoms': ['Shortness of breath', 'Chest tightness or pain', 'Wheezing when exhaling', 'Coughing attacks'],
                'description': 'A chronic disease that affects your airways, causing them to narrow and swell and to produce extra mucus.',
                'precautions': 'Avoid triggers like smoke and allergens. Use inhalers as prescribed by your doctor. Have an action plan for attacks.'
            },
            'Conjunctivitis (Pink Eye)': {
                'symptoms': ['Redness in one or both eyes', 'Itchiness in one or both eyes', 'A gritty feeling in one or both eyes', 'Discharge from the eyes'],
                'description': 'Inflammation or infection of the transparent membrane (conjunctiva) that lines your eyelid and covers the white part of your eyeball.',
                'precautions': 'Avoid touching your eyes. Wash hands frequently. Do not share towels or eye makeup. See a doctor for appropriate treatment (antibiotic or antiviral drops).'
            },
            'Hypertension (High Blood Pressure)': {
                'symptoms': ['Headaches', 'Shortness of breath', 'Nosebleeds', 'Chest pain', 'Dizziness'],
                'description': 'A common condition in which the long-term force of the blood against your artery walls is high enough that it may eventually cause health problems, such as heart disease.',
                'precautions': 'Maintain a healthy weight, eat a balanced diet, reduce sodium intake, exercise regularly, and limit alcohol. Take prescribed medications as directed.'
            },
            'Type 2 Diabetes': {
                'symptoms': ['Increased thirst', 'Frequent urination', 'Increased hunger', 'Unintended weight loss', 'Fatigue', 'Blurred vision', 'Slow-healing sores'],
                'description': 'A chronic condition that affects the way your body processes blood sugar (glucose).',
                'precautions': 'Manage diet, exercise regularly, monitor blood sugar levels, and take prescribed medications. Regular check-ups are essential.'
            },
            'Osteoarthritis': {
                'symptoms': ['Joint pain', 'Stiffness', 'Tenderness', 'Loss of flexibility', 'Grating sensation', 'Bone spurs'],
                'description': 'The most common form of arthritis, affecting millions of people worldwide. It occurs when the protective cartilage on the ends of your bones wears down over time.',
                'precautions': 'Maintain a healthy weight, exercise regularly (low-impact activities), use pain relievers as needed, and consider physical therapy. Avoid activities that worsen joint pain.'
            },
            'Anxiety Disorder': {
                'symptoms': ['Feeling nervous, restless or tense', 'Having a sense of impending danger, panic or doom', 'Increased heart rate', 'Hyperventilation', 'Sweating', 'Trembling'],
                'description': 'A mental health disorder characterized by feelings of worry, anxiety, or fear that are strong enough to interfere with one\'s daily activities.',
                'precautions': 'Practice stress management techniques (meditation, deep breathing), ensure adequate sleep, limit caffeine and alcohol, and seek professional help (therapy, medication) if symptoms are severe.'
            },
            'Dengue Fever': {
                'symptoms': ['High fever', 'Severe headache', 'Pain behind the eyes', 'Muscle and joint pains', 'Nausea', 'Vomiting', 'Swollen glands', 'Rash'],
                'description': 'A mosquito-borne tropical disease caused by the dengue virus.',
                'precautions': 'Prevent mosquito bites by using repellent, wearing protective clothing, and eliminating breeding sites. Seek medical attention immediately if symptoms appear.'
            }
        }

        for disease_name, data in medical_data.items():
            # Check if disease already exists
            if Disease.objects.filter(name=disease_name).exists():
                self.stdout.write(self.style.WARNING(f'Disease "{disease_name}" already exists. Skipping.'))
                continue

            # Create Disease object
            disease = Disease.objects.create(
                name=disease_name,
                description=data['description'],
                precautions=data['precautions']
            )
            self.stdout.write(f'  Created disease: {disease.name}')

            # Get or create Symptom objects and add them to the disease
            symptom_objects = []
            for symptom_name in data['symptoms']:
                symptom, created = Symptom.objects.get_or_create(name=symptom_name)
                symptom_objects.append(symptom)
                if created:
                    self.stdout.write(f'    - Created new symptom: {symptom.name}')
                else:
                    self.stdout.write(f'    - Found existing symptom: {symptom.name}')
            
            disease.symptoms.set(symptom_objects)
            self.stdout.write(self.style.SUCCESS(f'Successfully added symptoms to "{disease_name}".\n'))

        self.stdout.write(self.style.SUCCESS('Finished loading all medical data.'))