from django.contrib import admin

from django.contrib import admin
from .models import employee_model, department_model, team_model

admin.site.register(employee_model)
admin.site.register(department_model)
admin.site.register(team_model)
