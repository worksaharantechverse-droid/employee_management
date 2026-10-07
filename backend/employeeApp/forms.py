from django import forms
from django.contrib.auth import get_user_model
from .models import employee_model
from django.db.models import Q


class employee_form(forms.ModelForm):
    class Meta:
        model = employee_model
        # user is deliberately excluded: it is controlled by authentication.
        fields = [
            'name',
            'employee_id',
            'email',
            'phone',
            'Date_of_birth',
            'address',
            'city',
            'gender',
            'role',
            'manager',
            'department',
            'designation',
            'status',
            'joining_date',
            'salary',
            'Emergency_contact',
        ]
        widgets = {
            'Date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }


# Only accounts whose role is MANAGER may be selected as an employee's manager.
# This queryset is also applied to edit forms.
employee_form.base_fields['manager'].queryset = employee_model.objects.filter(Q(role ='MANAGER') | Q(user__role='MANAGER')).distinct().order_by('name')
