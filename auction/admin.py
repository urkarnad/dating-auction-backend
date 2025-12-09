from django.contrib import admin
from user.models import Gender, Year
from .models import Role, Faculty, Major, Lot


admin.site.register(Gender)
admin.site.register(Year)
admin.site.register(Faculty)
admin.site.register(Major)
admin.site.register(Role)
admin.site.register(Lot)
