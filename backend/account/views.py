from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from account.forms import RegistrationForm
from account.models import User
from employeeApp.models import employee_model
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_admin)
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = 'EMPLOYEE'
            user.is_active = True
            user.save()

            # Registration only knows name/email/role, so create a minimal
            # employee profile. HR can complete the remaining fields later.
            employee_model.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.name,
                    'email': user.email,
                    'role': 'EMPLOYEE',
                },
            )

            messages.success(request, 'Registration successful.')
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'account/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Both fields are required.')
            return redirect('login')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

        if not user.is_active:
            messages.error(request, 'Your account is inactive.')
            return redirect('login')

        authenticated_user = authenticate(
            request,
            email=user.email,
            password=password,
        )

        if authenticated_user is None:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

        login(request, authenticated_user)

        if authenticated_user.role == 'HR':
            return redirect('home')
        if authenticated_user.role == 'MANAGER':
            return redirect('manager_dashboard')
        return redirect('employee_dashboard')

    return render(request, 'account/login.html')
