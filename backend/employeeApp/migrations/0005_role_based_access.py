from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('account', '0002_user_role_alter_user_city'),
        ('employeeApp', '0004_remove_employee_model_employee_type'),
    ]

    def normalize_roles(apps, schema_editor):
        Employee = apps.get_model('employeeApp', 'employee_model')
        mapping = {
            'Employee': 'EMPLOYEE',
            'Intern': 'INTERN',
            'MANAGER': 'MANAGER',
            'HR': 'HR',
        }
        for old, new in mapping.items():
            Employee.objects.filter(role=old).update(role=new)

    operations = [
        migrations.AddField(
            model_name='employee_model',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='employee_profile',
                to='account.user',
            ),
        ),
        migrations.AddField(
            model_name='team_model',
            name='manager',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='managed_teams',
                to='employeeApp.employee_model',
            ),
        ),
        migrations.RunPython(normalize_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee_model',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='employee_model',
            name='city',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
        migrations.AlterField(
            model_name='employee_model',
            name='gender',
            field=models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='employee_model',
            name='role',
            field=models.CharField(choices=[('EMPLOYEE', 'Employee'), ('INTERN', 'Intern'), ('HR', 'HR'), ('MANAGER', 'Manager')], default='EMPLOYEE', max_length=100),
        ),
        migrations.AlterField(
            model_name='employee_model',
            name='joining_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
