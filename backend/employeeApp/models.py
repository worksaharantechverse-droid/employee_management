from django.db import models


class department_model(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class employee_model(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    EMPLOYEE_TYPE = [
        ('EMPLOYEE', 'Employee'),
        ('INTERN', 'Intern'),
        ('HR', 'HR'),
        ('MANAGER', 'Manager'),
    ]

    # Connect the employee profile to the login account.
    # Nullable so existing employee rows can survive the migration.
    user = models.OneToOneField(
        'account.User',
        on_delete=models.SET_NULL,
        related_name='employee_profile',
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, default='')
    Date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=15, blank=True, default='')
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, default='')
    role = models.CharField(max_length=100, choices=EMPLOYEE_TYPE, default='EMPLOYEE')

    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
    )

    department = models.ForeignKey(
        department_model,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )

    designation = models.CharField(max_length=100, null=True, blank=True)
    status = models.BooleanField(default=True)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.CharField(max_length=99, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    Emergency_contact = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class team_model(models.Model):
    name = models.CharField(max_length=100)

    department = models.ForeignKey(
        department_model,
        on_delete=models.CASCADE,
        related_name='teams',
    )

    # A manager owns/manages one or more teams.
    manager = models.ForeignKey(
        employee_model,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_teams',
    )

    description = models.TextField(blank=True, null=True)

    members = models.ManyToManyField(
        employee_model,
        blank=True,
        related_name='teams',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.department.name}"
