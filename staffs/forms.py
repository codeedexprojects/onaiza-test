from django import forms
from staffs.models import Staff, Designation, StaffAttendance, Pay, SalaryAllowance
from django.forms.widgets import Select, TextInput, Textarea, CheckboxInput, HiddenInput, DateInput
from django.forms.fields import Field
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete


class DesignationForm(forms.ModelForm):

    class Meta:
        model = Designation
        fields = ['name']

        widgets = {
            'name': TextInput(attrs={"class": "required form-control", "placeholder": "Name"}),

        }
        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
        }


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        exclude = ['creator', 'credit', 'debit', 'updater','deleted_reason', 'auto_id', 'is_deleted',
                   'current_salary', 'user', 'advance_salary', 'is_currently_working', 'theme']

        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),

            'staff_id': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Staff ID', 'readonly': ''}),
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone/Mobile'}),
            'address': TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'designation': autocomplete.ModelSelect2(url='staffs:designation_autocomplete', attrs={'data-placeholder': 'Designation', 'data-minimum-input-length': 0},),
            'joining_date': TextInput(attrs={'class': 'date-picker form-control 111', 'placeholder': 'Joining Date'}),
            'staff_age': TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff Age'}),
            'gender': Select(attrs={'class': 'form-control', 'placeholder': 'Staff Gender'}),
            'staff_role': Select(attrs={'class': 'form-control', 'placeholder': 'Staff Role'}),
            'salary': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Salary'}),
            'bank_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'branch': TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch'}),
            'bank_account_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Account Name'}),
            'ifsc_code': TextInput(attrs={'class': 'form-control', 'placeholder': 'IFSC'}),
            'account_num': TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Num'}),

        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'email': {
                'required': _("Email field is required."),
            },
            'phone': {
                'required': _("Phone field is required."),
            },
            'address': {
                'required': _("Address field is required."),
            },
            'staff_age': {
                'required': _("Staff Age field is required."),
            },
            'salary': {
                'required': _("Salary field is required."),
            }
        }

        labels = {
            'phone': "Phone/Mobile",
            'user_type': "Designation",
        }


class StaffFormCreate(forms.ModelForm):
    class Meta:
        model = Staff
        exclude = ['creator', 'credit', 'debit', 'updater','deleted_reason', 'auto_id', 'is_deleted',
                   'current_salary', 'user', 'advance_salary', 'is_currently_working', 'theme']

        widgets = {
            'staff_id': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Staff ID', 'readonly': ''}),
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone/Mobile'}),
            'address': TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'designation': autocomplete.ModelSelect2(url='staffs:designation_autocomplete', attrs={'data-placeholder': 'Designation', 'data-minimum-input-length': 0},),
            'joining_date': TextInput(attrs={'class': 'date-picker form-control 111', 'placeholder': 'Joining Date'}),
            'staff_age': TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff Age'}),
            'gender': Select(attrs={'class': 'form-control', 'placeholder': 'Staff Gender'}),
            'staff_role': Select(attrs={'class': 'form-control', 'placeholder': 'Staff Gender'}),

            'salary': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Salary'}),
            'bank_name': TextInput(attrs={'class': ' form-control', 'placeholder': 'Bank Name'}),
            'branch': TextInput(attrs={'class': ' form-control', 'placeholder': 'Branch'}),
            'bank_account_name': TextInput(attrs={'class': ' form-control', 'placeholder': 'Bank Account Name'}),
            'ifsc_code': TextInput(attrs={'class': ' form-control', 'placeholder': 'IFSC'}),
            'account_num': TextInput(attrs={'class': ' form-control', 'placeholder': 'Account Num'}),
            # 'report_to': autocomplete.ModelSelect2(url='staffs:staff_autocomplete', attrs={'data-placeholder': 'Select Staff', 'data-minimum-input-length': 0},),

        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'email': {
                'required': _("Email field is required."),
            },
            'phone': {
                'required': _("Phone field is required."),
            },
            'address': {
                'required': _("Address field is required."),
            },
            'staff_age': {
                'required': _("Staff Age field is required."),
            },
            'salary': {
                'required': _("Salary field is required."),
            }
        }

        labels = {
            'phone': "Phone/Mobile",
            'user_type': "Designation",
        }


class StaffAttendanceForm(forms.ModelForm):

    class Meta:
        model = StaffAttendance
        exclude = ['creator', 'updater','deleted_reason', 'auto_id',
                   'is_deleted', 'staff', 'half_leave_count', 'leave_count']
        widgets = {
            "date": TextInput(attrs={'class': 'required form-control', 'placeholder': 'DATE'}),
        }

        error_messages = {
            'date': {
                'required': _("Date field is required."),
            }
        }


class StaffAttendanceEditForm(forms.ModelForm):

    staff_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'disabled': 'disabled'}))

    class Meta:
        model = StaffAttendance
        exclude = ['creator', 'staff', 'updater','deleted_reason',
                   'auto_id', 'is_deleted', 'date']
        widgets = {
            "is_present": CheckboxInput(attrs={'class': 'checkbox'})

        }
        error_messages = {

        }


class AttendanceFemaleForm(forms.ModelForm):

    staff_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'disabled': 'disabled'}))

    class Meta:
        model = StaffAttendance
        exclude = ['creator', 'updater','deleted_reason', 'auto_id',
                   'is_deleted', 'date', 'half_leave_count', 'leave_count']
        widgets = {
            'staff': HiddenInput(),
            # 'is_present': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
            # 'is_leave': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
            # 'is_halfday': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
            # 'is_excuseleave': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
            # 'is_holiday': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
            # 'is_work_at_home': forms.TextInput(
            #     attrs={
            #         'class': 'custom-control-input',
            #         'type': 'checkbox'
            #     }
            # ),
        }
        error_messages = {
            "staff": {
                "required": _("staff field is required.")
            },
        }


class PayEditForm(forms.ModelForm):

    staff_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'disabled': 'disabled'}))

    class Meta:
        model = Pay
        exclude = ['creator', 'staff', 'updater','deleted_reason',
                   'auto_id', 'is_deleted', 'date']
        widgets = {
            "leave_count": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Leave Count'}),
            "half_leave_count": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Half Leave Count'}),
            "salary": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Salary'}),
            "is_paid": CheckboxInput(attrs={'class': 'checkbox'})

        }
        error_messages = {

        }


class PayForm(forms.ModelForm):

    class Meta:
        model = Pay
        exclude = ['creator', 'updater','deleted_reason',  'auto_id', 'is_deleted', 'total_time',
                   'staff', 'cant_take_excuseleave', 'half_leave_count', 'leave_count']
        widgets = {
            "date": TextInput(attrs={'class': 'required form-control', 'placeholder': 'DATE'}),
        }

        error_messages = {
            'date': {
                'required': _("Date field is required."),
            }
        }


class PayStaffForm(forms.ModelForm):

    allowance = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    staff_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'disabled': 'disabled'}))

    class Meta:
        model = Pay
        exclude = ['creator', 'updater','deleted_reason',  'auto_id', 'is_deleted']
        widgets = {
            'staff': HiddenInput(),
            "salary": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Salary'}),
            "leave_count": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Leave Count'}),
            "half_leave_count": TextInput(attrs={'class': 'required form-control', 'placeholder': 'HAlf Leave Count'}),
            "is_paid": CheckboxInput(attrs={'class': 'checkbox'})
        }
        error_messages = {
            "staff": {
                "required": _("staff field is required.")
            },
        }


class SalaryAllowanceForm(forms.ModelForm):
    class Meta:
        model = SalaryAllowance
        # fields = ['staff','date','allowance_type','description','hours','rate_per_hour','days','rate_per_day','allowance']
        exclude = ['creator', 'updater','deleted_reason',  'auto_id', 'is_deleted']
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staffs:staff_autocomplete', attrs={'data-placeholder': 'Select Staff', 'data-minimum-input-length': 0},),
            "date": TextInput(attrs={'class': 'required date-picker form-control', 'placeholder': 'DATE'}),
            "allowance_type": Select(attrs={'class': 'required selectpicker form-control', 'placeholder': 'Allowance Type'}),
            "hours": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Hours'}),
            "rate_per_hour": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Rate Per Hour'}),
            "days": TextInput(attrs={'class': 'required form-control', 'placeholder': 'days'}),
            "rate_per_day": TextInput(attrs={'class': 'required form-control', 'placeholder': 'Rate Per Day'}),
            "allowance": TextInput(attrs={'class': 'required form-control', 'readonly': '', 'placeholder': 'allowance'}),
        }
