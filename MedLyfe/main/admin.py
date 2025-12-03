from django.contrib import admin
from .models import Medicine, Substitute, Symptom, Disease

# This class allows you to add substitutes directly on the medicine page
class SubstituteInline(admin.TabularInline):
    model = Substitute
    extra = 1 # Shows one extra blank substitute form

# This class customizes how the Medicine admin page looks
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'composition', 'price', 'search_tag')
    inlines = [SubstituteInline] # Adds the substitute form to this page

# Register your models with the admin site
admin.site.register(Medicine, MedicineAdmin)
admin.site.register(Substitute)

class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    # This makes the 'symptoms' field much easier to use
    filter_horizontal = ('symptoms',) 

admin.site.register(Symptom)
admin.site.register(Disease, DiseaseAdmin)
