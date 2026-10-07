from django import forms
from django.contrib.auth.password_validation import (
    MinimumLengthValidator,
    CommonPasswordValidator,
    NumericPasswordValidator
)
from django.core.exceptions import ValidationError
from .models import User


class RegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'confirm_password']

    def clean_password(self):
        password = self.cleaned_data.get('password')

        validators = [
            MinimumLengthValidator(min_length=8),
            CommonPasswordValidator(),
            NumericPasswordValidator(),
        ]

        for validator in validators:
            try:
                validator.validate(password, self.instance)
            except ValidationError as error:
                raise forms.ValidationError(error.messages)

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error(
                'confirm_password',
                'Password and confirm password does not match'
            )

        cleaned_data['role'] = 'EMPLOYEE'

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email already exists')

        return email