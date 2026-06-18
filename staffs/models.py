from __future__ import unicode_literals
import uuid
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from decimal import Decimal
from django.core.validators import MinValueValidator
from versatileimagefield.fields import VersatileImageField


STAFF_ROLE = (
    ('warehouse_manager', 'Warehouse Manager'),
    ('normal_staff', 'Normal Staff'),
    ('billing_staff', 'Billing Staff')
)
SALARY_STATUS = (
    ('paid', 'Paid'),
    ('un_paid', 'Un paid')
)
STATUS = (
    ('yes', 'yes'),
    ('no', 'no'),
)
SERVICE_STATUS = (
    ('project', 'Service'),
    ('service', 'Product'),
)
GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
)
ALLOWANCE_CHOICES = (
    ('over time', 'Over Time'),
    ('working on holiday', 'Working On Holiday')
)
THEME_CHOICES = (
    ('teal', 'Teal'),
    ('blue', 'Blue'),
    ('bluegrey', 'Blue Grey'),
    ('cyan-600', 'Cyan'),
    ('green', 'Green'),
    ('lightgreen', 'Light Green'),
    ('purple-400', 'Purple'),
    ('red-400', 'Red'),
    ('pink-400', 'Pink'),
    ('brown', 'Brown'),
    ('grey-600', 'Grey'),
    ('orange', 'Orange')
)


class Designation(BaseModel):
    name = models.CharField(max_length=128)

    class Meta:
        db_table = 'designation'
        verbose_name = _('designation')
        verbose_name_plural = _('designations')
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


class Staff(BaseModel):
    user = models.OneToOneField("auth.user", blank=True, null=True, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    permission = models.ManyToManyField('users.Permission', blank=True)
    designation = models.ForeignKey("staffs.Designation", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    staff_id = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=128, blank=True, null=True)
    gender = models.CharField(max_length=40, choices=GENDER_CHOICES, default="other")
    staff_role = models.CharField(max_length=40, choices=STAFF_ROLE, default="normal_staff")
    photo = VersatileImageField('photo', upload_to="staffs/photo/", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    joining_date = models.DateTimeField(blank=True, null=True)
    staff_age = models.TextField(blank=True, null=True)
    current_salary = models.DecimalField(default=0, decimal_places=2, max_digits=8, validators=[MinValueValidator(Decimal('0.00'))])
    salary = models.DecimalField(default=0, decimal_places=0, max_digits=8, validators=[MinValueValidator(Decimal('0.00'))])

    bank_name = models.CharField(max_length=128, blank=True, null=True)
    branch = models.CharField(max_length=128, blank=True, null=True)
    bank_account_name = models.CharField(max_length=128, blank=True, null=True)
    ifsc_code = models.CharField(max_length=128, blank=True, null=True)
    account_num = models.CharField(max_length=128, blank=True, null=True)

    theme = models.CharField(max_length=40, choices=THEME_CHOICES, default="teal", blank=True, null=True)
    is_currently_working = models.BooleanField(default=False)

    normal_staff = models.BooleanField(default=False)
    super_admin = models.BooleanField(default=False)
    client_manager = models.BooleanField(default=False)
    staff_manager = models.BooleanField(default=False)

    advance_salary = models.DecimalField(default=0, decimal_places=2, blank=True, null=True, max_digits=8, validators=[MinValueValidator(Decimal('0.00'))])

    credit = models.DecimalField(default=0.0000, decimal_places=4, max_digits=15, validators=[MinValueValidator(Decimal('0.0000'))])
    debit = models.DecimalField(default=0.0000, decimal_places=4, max_digits=15, validators=[MinValueValidator(Decimal('0.0000'))])

    class Meta:
        db_table = 'staff'
        verbose_name = _('staff')
        verbose_name_plural = _('staffs')
        ordering = ('-auto_id',)

    def __str__(self):
        return str(self.name)

    def get_bank_details(self):
        details = ''
        if self.bank_name:
            details += self.bank_name + ' - '
        if self.branch:
            details += self.branch  # + ' - '

        return details

    def permissionlist(self):
        result = []
        permissions = self.permission.all()
        for perm in permissions:
            result.append(str(perm.code))
        return result


class StaffAttendance(BaseModel):
    date = models.DateField()
    staff = models.ForeignKey("staffs.Staff", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    half_leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    is_present = models.BooleanField(default=False)
    is_leave = models.BooleanField(default=False)
    is_halfday = models.BooleanField(default=False)
    is_excuseleave = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    is_work_at_home = models.BooleanField(default=False)

    class Meta:
        db_table = 'staff_attendence'
        verbose_name = _('staff_attendance')
        verbose_name_plural = _('staff_attendances')

    def __str__(self):
        return str(self.staff.name)


class StaffRecord(BaseModel):
    staff = models.ForeignKey("staffs.Staff", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    half_leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    salary = models.DecimalField(default=0.0, decimal_places=0, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    date = models.DateTimeField()
    is_paid = models.BooleanField(default=False)

    is_partially_paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    payment_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'techpe_staff_record'
        verbose_name = _('Techpe staff record')
        verbose_name_plural = _('Techpe staff records')
        ordering = ('staff',)

    def deduction(self):
        return (self.leave_count * 400) + (self.half_leave_count * 250)

    def __str__(self):
        return self.staff.first_name


class Pay(BaseModel):
    date = models.DateField(blank=True, null=True)
    staff = models.ForeignKey("staffs.Staff", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    half_leave_count = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    salary = models.DecimalField(default=0.0, decimal_places=0, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    is_paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(default=0, max_digits=15, decimal_places=0, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    class Meta:
        db_table = 'salary_pay'
        verbose_name = _('salary_pay')
        verbose_name_plural = _('salary_pays')

    def __str__(self):
        return str(self.staff.name)


class SalaryAllowance(BaseModel):
    staff = models.ForeignKey("staffs.Staff", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField()
    is_deleted = models.BooleanField(default=False)
    description = models.CharField(max_length=128, blank=True, null=True)
    allowance_type = models.CharField(max_length=128, choices=ALLOWANCE_CHOICES)

    days = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    hours = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    rate_per_day = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    rate_per_hour = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    is_paid = models.BooleanField(default=False)
    allowance = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    class Meta:
        db_table = 'staff_salary_allowance'
        verbose_name = _('Salary Allowance')
        verbose_name_plural = _('Salary Allowances')
        ordering = ('-auto_id',)

    def __str__(self):
        return str('%s - %s' % (self.staff.name, str(self.allowance)))
