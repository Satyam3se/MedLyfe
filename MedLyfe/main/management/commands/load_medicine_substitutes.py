import json
import os
from django.core.management.base import BaseCommand
from main.models import Medicine, Substitute

class Command(BaseCommand):
    help = 'Loads sample medicine and substitute data into the database from a JSON file'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load medicine and substitute data from JSON...'))

        json_file_path = os.path.join(os.path.dirname(__file__), 'medicine_data.json')

        if not os.path.exists(json_file_path):
            self.stderr.write(self.style.ERROR(f'Error: JSON data file not found at {json_file_path}'))
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            medicine_data = json.load(f)

        for med_entry in medicine_data:
            medicine, created = Medicine.objects.get_or_create(
                search_tag=med_entry['search_tag'],
                defaults={
                    'name': med_entry['name'],
                    'manufacturer': med_entry['manufacturer'],
                    'composition': med_entry['composition'],
                    'price': med_entry['price']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Medicine: {medicine.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Medicine already exists: {medicine.name}'))
            
            for sub_data in med_entry['substitutes']:
                Substitute.objects.get_or_create(
                    original_medicine=medicine,
                    name=sub_data['name'],
                    manufacturer=sub_data['manufacturer'],
                    composition=sub_data['composition'],
                    price=sub_data['price']
                )
                self.stdout.write(self.style.SUCCESS(f'  Added Substitute: {sub_data["name"]} for {medicine.name}'))

        self.stdout.write(self.style.SUCCESS('Finished loading medicine and substitute data from JSON.'))
