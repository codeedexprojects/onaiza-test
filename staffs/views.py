# Standard libraries
import datetime
import decimal
import json
from calendar import monthrange
from django.contrib.auth.models import Group
# third party libraries
import xlwt
from dal import autocomplete
from num2words import num2words
# django libraries
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum, Q
from django.forms.models import inlineformset_factory, formset_factory
from django.contrib.auth.decorators import login_required
# local libraries
from main.functions import generate_form_errors, get_auto_id
from main.decorators import check_mode, ajax_required, permissions_required
from main.functions import get_date_updated_request
from users.forms import UserForm
from users.models import Permission
from sales.models import Sale
from customers.models import Customer
from staffs.models import Designation, Staff, StaffAttendance, StaffRecord, Pay, SalaryAllowance
from staffs.forms import DesignationForm, StaffForm, StaffAttendanceForm, AttendanceFemaleForm, \
    StaffAttendanceEditForm, PayEditForm, PayForm, PayStaffForm, SalaryAllowanceForm


class DesignationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = []
        user = self.request.user

        if user.is_superuser or Staff.objects.filter(user=user).exists():
            items = Designation.objects.filter(
                is_deleted=False)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items

    def create_object(self, text):
        text = text.title()
        if not Designation.objects.filter(is_deleted=False, name=text):
            auto_id = get_auto_id(Designation)

            return Designation.objects.create(
                auto_id=auto_id,
                name=text,
                creator=self.request.user,
                updater=self.request.user
            )


class StaffAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Staff.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items


class WarehouseManagerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Staff.objects.filter(
            is_deleted=False, staff_role="warehouse_manager")

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items


@check_mode
@login_required
@permissions_required(['can_create_staff_designation'])
def create_designation(request):
    instances = Designation.objects.filter(is_deleted=False)

    if request.method == 'POST':
        form = DesignationForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Designation)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.creator = request.user
            data.updater = request.user

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Designation created successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:designation', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = DesignationForm()

        context = {
            "title": "Create Designation",
            "form": form,
            "redirect": True,
        }
        return render(request, 'staffs/create_designation.html', context)


@check_mode
@login_required
@permissions_required(['can_modify_staff_designation'])
def edit_designation(request, pk):
    instance = get_object_or_404(
        Designation.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':

        form = DesignationForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Designation Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('staffs:designation', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = DesignationForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Designation : " + instance.name,
            "instance": instance,
            "url": reverse('staffs:edit_designation', kwargs={'pk': instance.pk}),
            "redirect": True,
            "purchases": True,
        }
        return render(request, 'staffs/create_designation.html', context)


@check_mode
@login_required
@permissions_required(['can_view_staff_designation'])
def designation(request, pk):
    instance = get_object_or_404(
        Designation.objects.filter(pk=pk, is_deleted=False))

    context = {
        'instance': instance,
        'title': 'Designation',
        "products": True,
    }
    return render(request, "staffs/designation.html", context)


@check_mode
@login_required
@permissions_required(['can_manage_staff_designation'])
def designations(request):
    instance = []
    user = request.user
    if user.is_superuser or Staff.objects.filter(user=user).exists():
        instances = Designation.objects.filter(
            is_deleted=False)

    query = request.GET.get("q")
    if query:
        print("query", query)
        instances = instances.filter(Q(name__icontains=query))

    context = {
        'instances': instances,
        "title": 'designations',
    }
    return render(request, "staffs/designations.html", context)


@login_required
@permissions_required(['can_delete_staff_designation'])
def delete_designation(request, pk):
    instance = get_object_or_404(
        Designation.objects.filter(pk=pk, is_deleted=False))
    instance.is_deleted = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Designation Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('staffs:designations')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@permissions_required(['superadmin'])
def create_staff(request):
    auto_id = get_auto_id(Staff)
    if auto_id < 10:
        staff_id = 'ONZ000%s' % (str(auto_id))
    elif auto_id < 100:
        staff_id = 'ONZ00%s' % (str(auto_id))
    elif auto_id < 1000:
        staff_id = 'ONZ0%s' % (str(auto_id))
    else:
        staff_id = 'ONZ%s' % (str(auto_id))

    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES)
        user_form = UserForm(request.POST)

        if form.is_valid() and user_form.is_valid():
            auto_id = get_auto_id(Staff)
            salary = form.cleaned_data['salary']
            staff_role = form.cleaned_data['staff_role']
            data = form.save(commit=False)
            user_data = user_form.save()
            instance = user_data
            data.creator = request.user
            data.updater = request.user
            data.staff_id = staff_id
            data.auto_id = auto_id
            data.user = user_data
            data.current_salary = salary
            data.save()

            group = Group.objects.get(name=staff_role)
            user_data.groups.add(group)

            permissions = request.POST.getlist('permission')
            for item in permissions:
                p = Permission.objects.get(pk=item)
                data.permission.add(p)

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Staff created successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:set_permissions', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(user_form, formset=False)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StaffForm(initial={'staff_id': staff_id})
        user_form = UserForm()

        context = {
            "form": form,
            "user_form": user_form,
            "title": "Create Staff",
        }
        return render(request, 'staffs/create_staff.html', context)


@check_mode
@login_required
@permissions_required(['superadmin'])
def set_permissions(request, pk):
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        permissions = request.POST.getlist('permission')
        instance.permission.clear()

        for item in permissions:
            p = Permission.objects.get(pk=item)
            instance.permission.add(p)

        response_data = {
            "status": "true",
            "title": "Successfully Updated",
            "message": "Staff updated successfully.",
            "redirect": "true",
            "redirect_url": reverse('staffs:view_staff', kwargs={'pk': instance.pk})
        }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        array_p = list(instance.permission.all().values_list('pk', flat=True))

        permissions = Permission.objects.all()
        admin_permissions = permissions.filter(app="admin")
        sales_permissions = permissions.filter(app="sales")
        staffs_permissions = permissions.filter(app="staffs")
        report_permissions = permissions.filter(app="reports")
        offers_permissions = permissions.filter(app="offers")
        vendors_permissions = permissions.filter(app="vendors")
        account_permissions = permissions.filter(app="accounts")
        supplier_permissions = permissions.filter(app="suppliers")
        products_permissions = permissions.filter(app="products")
        purchase_permissions = permissions.filter(app="purchases")
        warehouse_permissions = permissions.filter(app="warehouses")
        customers_permissions = permissions.filter(app="customers")

        context = {
            "is_edit": True,
            "array_p": array_p,
            "instance": instance,
            "title": "Set Permissions : " + instance.name,
            "url": reverse('staffs:set_permissions', kwargs={'pk': instance.pk}),
            "admin_permissions": admin_permissions,
            "sales_permissions": sales_permissions,
            "report_permissions": report_permissions,
            "staffs_permissions": staffs_permissions,
            "offers_permissions": offers_permissions,
            "account_permissions": account_permissions,
            "vendors_permissions": vendors_permissions,
            "purchase_permissions": purchase_permissions,
            "products_permissions": products_permissions,
            "supplier_permissions": supplier_permissions,
            "warehouse_permissions": warehouse_permissions,
            "customers_permissions": customers_permissions,
        }
        return render(request, 'staffs/set_permissions.html', context)


@check_mode
@login_required
@permissions_required(['superadmin'])
def edit_staff(request, pk):
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['joining_date'])
        form = StaffForm(ModifiedRequest, request.FILES, instance=instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            permissions = request.POST.getlist('permission')
            instance.permission.clear()
            for item in permissions:
                p = Permission.objects.get(pk=item)
                data.permission.add(p)

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Staff updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:view_staff', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = StaffForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Staff : " + instance.name,
            "instance": instance,
            "url": reverse('staffs:edit_staff', kwargs={'pk': instance.pk}),
            "redirect": True,
            "is_edit": True,
        }

        return render(request, 'staffs/create_staff.html', context)


@check_mode
@login_required
@permissions_required(['superadmin'])
def view_staff(request, pk):
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Staff : " + str(instance.name),
        "single_page": True,
    }
    return render(request, 'staffs/staff.html', context)


@check_mode
@login_required
@permissions_required(['superadmin'])
def staffs(request):
    instances = Staff.objects.filter(is_deleted=False)
    title = " Staffs"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
        title = " Staffs - %s" % query
    context = {
        "instances": instances,
        'title': title,
    }

    return render(request, 'staffs/staffs.html', context)


@check_mode
@login_required
@permissions_required(['can_manage_staff'])
def staffs_report(request):
    staffs = Staff.objects.filter(is_deleted=False).order_by('auto_id')

    title = " Staffs"
    instance = None
    allowance = 0
    paid_amount = 0
    salary_items = None
    attendance_data = None

    pk = request.GET.get('staff')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if not from_date:
        from_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%m/%d/%Y')

    if not to_date:
        to_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%m/%d/%Y')

    form_filter = {
        "staff": pk,
        "from_date": from_date,
        "to_date": to_date,
    }

    if pk:
        try:
            instance = get_object_or_404(Staff, pk=pk)
        except:
            pass

    if instance:
        title = "Staff #%s" % instance.staff_id
        from_date = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date = datetime.datetime.strptime(to_date, '%m/%d/%Y')

        if SalaryAllowance.objects.filter(staff_id=pk, is_deleted=False, date__range=[from_date, to_date]).exists():
            allowance = SalaryAllowance.objects.filter(staff_id=pk, is_deleted=False, date__range=[
                                                       from_date, to_date]).aggregate(allowance=Sum('allowance')).get('allowance', 0)

        if Pay.objects.filter(staff_id=pk, is_deleted=False, date__range=[from_date, to_date]).exists():
            paid_amount = Pay.objects.filter(staff_id=pk, is_deleted=False, date__range=[
                                             from_date, to_date]).aggregate(paid_amount=Sum('paid_amount')).get('paid_amount', 0)

        if StaffRecord.objects.filter(staff_id=pk, is_deleted=False, date__range=[from_date, to_date]).exists():
            salary_items = StaffRecord.objects.filter(
                staff_id=pk, is_deleted=False, date__range=[from_date, to_date])

        if StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_deleted=False).exists():
            present_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_present=True, is_deleted=False).count()
            leave_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_leave=True, is_deleted=False).count()
            halfday_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_halfday=True, is_deleted=False).count()
            excuseleave_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_excuseleave=True, is_deleted=False).count()
            holiday_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_holiday=True, is_deleted=False).count()
            work_at_home_count = StaffAttendance.objects.filter(staff_id=pk, date__range=[from_date, to_date], is_work_at_home=True, is_deleted=False).count()

            attendance_data = {
                'present_count': present_count,
                'halfday_count': halfday_count,
                'leave_count': leave_count,
                'excuseleave_count': excuseleave_count,
                'work_at_home_count': work_at_home_count,
                'holiday_count': holiday_count,
            }

    context = {
        'title': title,
        "staffs": staffs,
        "instance": instance,
        "allowance": allowance,
        "paid_amount": paid_amount,
        "form_filter": form_filter,
        "salary_items": salary_items,
        "attendance_data": attendance_data,
    }

    return render(request, 'staffs/staff_report.html', context)


@check_mode
@login_required
@permissions_required(['superadmin'])
def delete_staff(request, pk):
    instance = get_object_or_404(Staff.objects.filter(pk=pk, is_deleted=False))
    instance.is_deleted = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    user = instance.user
    instance.save()

    username = user.username + str(instance.pk) + "deactivated"
    mail = user.email + str(instance.pk) + "deactivated"
    user.is_active = False
    user.email = mail
    user.username = username
    user.save()

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Staff Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('staffs:staffs')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@permissions_required(['superadmin'])
def delete_selected_staffs(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Staff.objects.filter(pk=pk, is_deleted=False))
            instance.is_deleted = True
            instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Staff(s) Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('staffs:staffs')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@permissions_required(['can_view_staff'])
def staff_about(request, pk):
    date = datetime.datetime.now()

    staff = None
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)

    context = {
        "title": "Staff About",
        "staff_data": staff,
        "is_dashboard": True

    }
    return render(request, "staffs/staff_about.html", context)


@permissions_required(['can_create_staff_attendance'])
def create_staff_attendance(request):
    selected_date = datetime.date.today()
    date = request.GET.get("date")

    if date:
        date_error = False
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = True
        if not date_error:
            selected_date = date

    staffs = Staff.objects.filter(is_deleted=False)
    AttendanceFormset = formset_factory(AttendanceFemaleForm, extra=0)

    if request.method == 'POST':
        attendance_formset = AttendanceFormset(request.POST, prefix='attendance_formset')
        attendance_date_form = StaffAttendanceForm(request.POST)

        if attendance_date_form.is_valid() and attendance_formset.is_valid():
            date = attendance_date_form.cleaned_data['date']
            no_days = monthrange(date.year, date.month)[1]

            formset_errors = []

            for attendance in attendance_formset:
                print(
                    attendance.cleaned_data['is_present'],
                    attendance.cleaned_data['staff'],
                    attendance.cleaned_data['is_excuseleave'],
                    attendance.cleaned_data['is_leave'],
                    attendance.cleaned_data['is_halfday'],
                    attendance.cleaned_data['is_work_at_home'],
                "HALOOOI")

                try:
                    is_present = attendance.cleaned_data['is_present']
                    staff = attendance.cleaned_data['staff']
                    is_excuseleave = attendance.cleaned_data['is_excuseleave']
                    is_leave = attendance.cleaned_data['is_leave']
                    is_halfday = attendance.cleaned_data['is_halfday']
                    is_work_at_home = attendance.cleaned_data['is_work_at_home']
                    # leave_count = attendance.cleaned_data['leave_count']
                    # half_leave_count = attendance.cleaned_data['half_leave_count']
                    print("Leave Count")
                except:
                    print("POOOOI")
                    pass

                if not is_present:
                    is_excuseleave = attendance.cleaned_data['is_excuseleave']

                auto_id = get_auto_id(StaffAttendance)

                if not StaffAttendance.objects.filter(date=date, staff=staff, is_deleted=False).exists():
                    print("no exist")
                    if is_excuseleave:
                        if StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                            excuse_leave_count = StaffAttendance.objects.filter(date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).count()

                            if excuse_leave_count >= 12:
                                formset_errors.append(staff.name)
                                # response_data = {
                                #     "status" : "false",
                                #     "stable" : "true",
                                #     "title" : "Form validation error",
                                #     "message" : " %s cant take an excuse leave on this year" % (staff,),
                                # }
                                # return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                            if excuse_leave_count < 12:
                                StaffAttendance.objects.create(
                                    date=date,
                                    staff=staff,
                                    is_present=is_present,
                                    is_excuseleave=is_excuseleave,
                                    is_leave=is_leave,
                                    is_halfday=is_halfday,
                                    auto_id=get_auto_id(StaffAttendance),
                                    creator=request.user,
                                    updater=request.user,
                                )
                        elif not StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                            StaffAttendance.objects.create(
                                date=date,
                                staff=staff,
                                is_present=is_present,
                                is_excuseleave=is_excuseleave,
                                is_leave=is_leave,
                                is_halfday=is_halfday,
                                auto_id=get_auto_id(StaffAttendance),
                                creator=request.user,
                                updater=request.user,
                            )

                        if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.create(
                                date=date,
                                staff=staff,
                                leave_count=0,
                                half_leave_count=0,
                                salary=staff.salary,
                                is_paid=False,
                                auto_id=get_auto_id(StaffRecord),
                                creator=request.user,
                                updater=request.user,
                            )

                    elif is_present or is_leave or is_halfday or is_work_at_home:
                        StaffAttendance.objects.create(
                            date=date,
                            staff=staff,
                            is_present=is_present,
                            is_excuseleave=is_excuseleave,
                            is_leave=is_leave,
                            is_halfday=is_halfday,
                            is_work_at_home=is_work_at_home,
                            auto_id=get_auto_id(StaffAttendance),
                            creator=request.user,
                            updater=request.user,
                        )

                        if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.create(
                                date=date,
                                staff=staff,
                                leave_count=0,
                                half_leave_count=0,
                                salary=staff.salary,
                                is_paid=False,
                                auto_id=get_auto_id(StaffRecord),
                                creator=request.user,
                                updater=request.user,
                            )

                        total_allowance = 0
                        allowances = SalaryAllowance.objects.filter(is_deleted=False, staff=staff, date__month=date.month, date__year=date.year)

                        for item in allowances:
                            total_allowance += item.allowance

                        leaves = StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False)
                        old_leave_count = leaves.filter(is_leave=True).count()
                        half_leave_count = leaves.filter(is_halfday=True).count()

                        salary = staff.salary
                        total_subtract = old_leave_count * (staff.salary / no_days) - half_leave_count * (staff.salary / (no_days * 2))

                        leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        Staff.objects.filter(pk=staff.pk).update(current_salary=salary - total_subtract + total_allowance)

                        if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(
                                date=date,
                                leave_count=old_leave_count,
                                half_leave_count=half_leave_count,
                                salary=salary - total_subtract + total_allowance
                            )

                        # if is_present:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = staff.salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        # elif is_work_at_home:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = staff.salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        # elif is_leave:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = staff.salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        # elif is_halfday:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(half_leave_count=half_leave_count,leave_count=old_leave_count)
                        #     salary = staff.salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))

                elif StaffAttendance.objects.filter(date=date, staff=staff, is_deleted=False).exists():
                    attendance = StaffAttendance.objects.get(date=date, staff=staff, is_deleted=False)
                    if attendance.is_present or attendance.is_work_at_home:
                        pass
                    elif attendance.is_leave:
                        old_leave_count = StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_leave=True).count()
                        half_leave_count = StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_halfday=True).count()
                        salary = Staff.objects.get(pk=staff.pk).salary

                        new_leave_count = old_leave_count - 1

                        StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False).update(
                            leave_count=new_leave_count,
                            half_leave_count=half_leave_count
                        )

                        Staff.objects.filter(pk=staff.pk).update(
                            current_salary = salary - (new_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2)))
                        )

                        if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(date=date, leave_count=new_leave_count, half_leave_count=half_leave_count, salary=salary - (new_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                    elif attendance.is_halfday:
                        old_half_leave_count = StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_halfday=True).count()
                        leave_count = StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_leave=True).count()
                        salary = Staff.objects.get(pk=staff.pk).salary

                        new_half_leave_count = old_half_leave_count - 1

                        StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False).update(leave_count=leave_count, half_leave_count=new_half_leave_count)
                        Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (leave_count*(staff.salary/no_days)) - (new_half_leave_count*(staff.salary/(no_days*2))))

                        if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(date=date, leave_count=leave_count, half_leave_count=new_half_leave_count, salary=salary - (leave_count*(staff.salary/no_days)) - (new_half_leave_count*(staff.salary/(no_days*2))))
                    elif attendance.is_excuseleave:
                        print("excuse leave")
                    StaffAttendance.objects.filter(pk=attendance.pk, is_deleted=False).update(is_deleted=True)

                    # get_object_or_404(Holiday.objects.filter(pk=pk,is_deleted=False))
                    if is_excuseleave:
                        if StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                            excuse_leave_count = 0
                            excuse_leave_count = StaffAttendance.objects.filter(
                                date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).count()
                            if excuse_leave_count >= 12:
                                formset_errors.append(staff.name)
                                # response_data = {
                                #     "status" : "false",
                                #     "stable" : "true",
                                #     "title" : "Form validation error",
                                #     "message" : " %s cant take an excuse leave on this year" % (staff,),
                                # }
                                # return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                            if excuse_leave_count < 12:
                                StaffAttendance.objects.create(
                                    date=date,
                                    staff=staff,
                                    is_present=is_present,
                                    is_excuseleave=is_excuseleave,
                                    is_leave=is_leave,
                                    is_halfday=is_halfday,
                                    auto_id=get_auto_id(StaffAttendance),
                                    creator=request.user,
                                    updater=request.user,
                                )
                        elif not StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                            StaffAttendance.objects.create(
                                date=date,
                                staff=staff,
                                is_present=is_present,
                                is_excuseleave=is_excuseleave,
                                is_leave=is_leave,
                                is_halfday=is_halfday,
                                auto_id=get_auto_id(StaffAttendance),
                                creator=request.user,
                                updater=request.user,
                            )

                        if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.create(
                                date=date,
                                staff=staff,
                                leave_count=0,
                                half_leave_count=0,
                                salary=staff.salary,
                                is_paid=False,
                                auto_id=get_auto_id(StaffRecord),
                                creator=request.user,
                                updater=request.user,
                            )
                    elif is_present or is_leave or is_halfday or is_work_at_home:
                        StaffAttendance.objects.create(
                            date=date,
                            staff=staff,
                            is_present=is_present,
                            is_excuseleave=is_excuseleave,
                            is_leave=is_leave,
                            is_halfday=is_halfday,
                            is_work_at_home=is_work_at_home,
                            auto_id=get_auto_id(StaffAttendance),
                            creator=request.user,
                            updater=request.user,
                        )
                        if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.create(
                                date=date,
                                staff=staff,
                                leave_count=0,
                                half_leave_count=0,
                                salary=staff.salary,
                                is_paid=False,
                                auto_id=get_auto_id(StaffRecord),
                                creator=request.user,
                                updater=request.user,
                            )

                        total_allowance = 0
                        allowances = SalaryAllowance.objects.filter(
                            is_deleted=False, staff=staff, date__month=date.month, date__year=date.year)
                        for item in allowances:
                            total_allowance += item.allowance

                        leaves = StaffAttendance.objects.filter(
                            date__month=date.month, date__year=date.year, staff=staff, is_deleted=False)
                        old_leave_count = leaves.filter(is_leave=True).count()
                        half_leave_count = leaves.filter(
                            is_halfday=True).count()

                        salary = Staff.objects.get(pk=staff.pk).salary
                        total_subtract = old_leave_count * \
                            (staff.salary/no_days) + half_leave_count * \
                            (staff.salary/(no_days*2))

                        leaves.update(leave_count=old_leave_count,
                                      half_leave_count=half_leave_count)
                        Staff.objects.filter(pk=staff.pk).update(
                            current_salary=salary - total_subtract + total_allowance)
                        if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                            StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(
                                date=date,
                                leave_count=old_leave_count,
                                half_leave_count=half_leave_count,
                                salary=salary - total_subtract + total_allowance
                            )

                        # if is_present:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = Staff.objects.get(pk=staff.pk).salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        # elif is_work_at_home:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = Staff.objects.get(pk=staff.pk).salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        # elif is_leave:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(leave_count=old_leave_count,half_leave_count=half_leave_count)
                        #     salary = Staff.objects.get(pk=staff.pk).salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))

                        # elif is_halfday:
                        #     leaves = StaffAttendance.objects.filter(date__month=date.month,date__year=date.year,staff=staff,is_deleted=False)
                        #     old_leave_count = leaves.filter(is_leave=True).count()
                        #     half_leave_count = leaves.filter(is_halfday=True).count()
                        #     leaves.update(half_leave_count=half_leave_count,leave_count=old_leave_count)
                        #     salary = Staff.objects.get(pk=staff.pk).salary
                        #     Staff.objects.filter(pk=staff.pk).update(current_salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))

                        #     if StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).exists():
                        #         StaffRecord.objects.filter(staff=staff,date__month=date.month,date__year=date.year).update(date=date,leave_count=old_leave_count,half_leave_count=half_leave_count,salary=salary - (old_leave_count*(staff.salary/no_days)) - (half_leave_count*(staff.salary/(no_days*2))))
            if formset_errors:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": " %s can't take an excuse leave on this year" % (', '.join(formset_errors),),
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Attendance created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('staffs:staff_attendances')
                }

        else:
            message = generate_form_errors(attendance_date_form, formset=False)
            message += generate_form_errors(attendance_formset, formset=True)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        initial = []

        month = selected_date.month

        for staff in staffs:
            selected_date_attendance = None
            is_present = False
            is_excuseleave = False
            is_leave = False
            is_halfday = False
            is_work_at_home = False

            if StaffAttendance.objects.filter(date=selected_date, staff=staff, is_deleted=False).exists():
                selected_date_attendance = StaffAttendance.objects.filter(
                    date=selected_date, staff=staff, is_deleted=False)[0]
                is_present = selected_date_attendance.is_present
                is_excuseleave = selected_date_attendance.is_excuseleave
                is_leave = selected_date_attendance.is_leave
                is_halfday = selected_date_attendance.is_halfday
                is_work_at_home = selected_date_attendance.is_work_at_home
            attendance_dict = {
                'staff': staff,
                'staff_name': str(staff.name),
                'is_present': is_present,
                'is_excuseleave': is_excuseleave,
                'is_leave': is_leave,
                'is_halfday': is_halfday,
                'is_work_at_home': is_work_at_home,
            }
            initial.append(attendance_dict)

        attendance_formset = AttendanceFormset(
            prefix='attendance_formset', initial=initial)
        attendance_date_form = StaffAttendanceForm(
            initial={"date": selected_date})
        for i in attendance_formset:
            i.fields['is_excuseleave'].queryset = StaffAttendance.objects.filter(
                is_excuseleave=False)
        context = {
            "title": "Create Attendance",
            "attendance_formset": attendance_formset,
            "attendance_date_form": attendance_date_form,
            "url": reverse('staffs:create_staff_attendance'),
            "today": selected_date,
            "staffs": staffs,
            "redirect": True,

            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_grid_system": True,
            "is_need_animations": True,
            "is_need_datetime_picker": True,
        }
        return render(request, 'staffs/create_staff_attendance.html', context)


@login_required
@permissions_required(['can_manage_staff_attendance'])
def staff_attendances(request):
    today = datetime.date.today()
    instances = StaffAttendance.objects.filter(is_deleted=False, date=today)

    context = {
        "instances": instances,
        "title": "Indograce Staff Attendance",

        "is_need_calender": True,
        "single_page": True,

    }
    return render(request, 'staffs/attendances.html', context)


@check_mode
@login_required
@permissions_required(['can_view_staff_attendance'])
def staff_attendance(request):
    today = datetime.date.today()
    date_string = today
    instances_today = StaffAttendance.objects.filter(
        is_deleted=False, date=today)
    date = request.GET.get("date")
    date_error = False
    present_students = 0
    absent_students = 0
    leave_students = 0
    half_leave_students = 0
    excuse_leave_students = 0
    work_at_home_students = 0
    attendance_item_formset = StaffAttendance.objects.none()

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
            title = "Attendances %s" % (date)
            date_string = date
        except ValueError:
            date_error = True

    if not date_error and date:
        instances_today = []
        attendance_item_formset = StaffAttendance.objects.filter(
            is_deleted=False, date=date_string)

    present_students = StaffAttendance.objects.filter(
        is_deleted=False, is_present=True, date=date_string).count()
    absent_students = StaffAttendance.objects.filter(
        is_deleted=False, is_present=False, is_work_at_home=False, date=date_string).count()
    leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_leave=True, date=date_string).count()
    half_leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_halfday=True, date=date_string).count()
    excuse_leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_excuseleave=True, date=date_string).count()
    work_at_home_students = StaffAttendance.objects.filter(
        is_deleted=False, is_work_at_home=True, date=date_string).count()

    present = request.GET.get("present")
    absent = request.GET.get("absent")
    leave = request.GET.get("leave")
    half_leave = request.GET.get("half_leave")
    excuse_leave = request.GET.get("excuse_leave")
    work_at_home = request.GET.get("work_at_home")

    if present:
        attendance_item_formset = attendance_item_formset.filter(
            is_present=present, date=date_string)

    if absent:
        attendance_item_formset = attendance_item_formset.filter(
            is_present=absent, date=date_string)

    if leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_leave=leave, date=date_string)

    if excuse_leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_excuseleave=excuse_leave, date=date_string)

    if half_leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_halfday=half_leave, date=date_string)
    if work_at_home:
        attendance_item_formset = attendance_item_formset.filter(
            is_work_at_home=work_at_home, date=date_string)

    context = {
        "attendance_item_formset": attendance_item_formset,
        "title": "Staff Attendance ",
        "instances_today": instances_today,
        "present_students": present_students,
        "absent_students": absent_students,
        "excuse_leave_students": excuse_leave_students,
        "half_leave_students": half_leave_students,
        "leave_students": leave_students,
        "work_at_home_students": work_at_home_students,
        "date": date,
        "date_string": date_string,

        "single_page": True,

    }
    return render(request, 'staffs/attendance.html', context)


@check_mode
@login_required
@permissions_required(['can_modify_staff_attendance'])
def edit_staff_attendance(request, pk):
    instance = get_object_or_404(
        StaffAttendance.objects.filter(pk=pk, is_deleted=False))
    url = reverse('staffs:edit_staff_attendance', kwargs={'pk': pk})
    if request.method == "POST":
        previous_attendance_status = instance.is_present

        form = StaffAttendanceEditForm(request.POST, instance=instance)

        if form.is_valid():
            staff = instance.staff
            is_present = form.cleaned_data['is_present']
            date = instance.date
            is_leave = form.cleaned_data['is_leave']
            is_halfday = form.cleaned_data['is_halfday']
            is_excuseleave = form.cleaned_data['is_excuseleave']
            is_work_at_home = form.cleaned_data['is_work_at_home']
            attendance = StaffAttendance.objects.get(
                date=instance.date, staff=instance.staff, is_deleted=False)
            current_salary = 0

            no_days = monthrange(date.year, date.month)[1]

            attendance = StaffAttendance.objects.get(
                date=instance.date, staff=instance.staff, is_deleted=False)

            if attendance.is_work_at_home or attendance.is_present:
                print("yeah present")
            elif attendance.is_leave:
                old_leave_count = StaffAttendance.objects.filter(
                    date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False, is_leave=True).count()
                half_leave_count = StaffAttendance.objects.filter(
                    date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False, is_halfday=True).count()
                new_leave_count = old_leave_count - 1
                StaffAttendance.objects.filter(date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False).update(
                    leave_count=new_leave_count, half_leave_count=half_leave_count)

                staff_record = StaffRecord.objects.get(
                    staff=staff, date__month=instance.date.month, date__year=instance.date.year)
                current_leave_count = staff_record.leave_count
                current_half_leave = staff_record.half_leave_count
                current_salary = staff_record.salary

                StaffRecord.objects.filter(staff=staff, date__month=instance.date.month, date__year=instance.date.year).update(
                    leave_count=current_leave_count-1, half_leave_count=current_half_leave, salary=current_salary+(staff.salary/no_days))
            elif attendance.is_halfday:
                print("Okay")
                old_half_leave_count = StaffAttendance.objects.filter(
                    date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False, is_halfday=True).count()
                print("Okay2")
                leave_count = StaffAttendance.objects.filter(
                    date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False, is_leave=True).count()
                print("Okay3")
                new_half_leave_count = old_half_leave_count - 1
                print("Okay4")
                StaffAttendance.objects.filter(date__month=instance.date.month, date__year=instance.date.year, staff=instance.staff, is_deleted=False).update(
                    leave_count=leave_count, half_leave_count=new_half_leave_count)
                print("Okay5")
                # StaffAttendance.objects.filter(date__month=instance.date.month,date__year=instance.date.year,staff=instance.staff,is_deleted=False).update(leave_count=leave_count,half_leave_count=new_half_leave_count,salary=current_salary+(staff.salary/60))
                staff_record = StaffRecord.objects.get(
                    staff=staff, date__month=instance.date.month, date__year=instance.date.year)
                current_leave_count = staff_record.leave_count
                current_half_leave = staff_record.half_leave_count
                current_salary = staff_record.salary

                StaffRecord.objects.filter(staff=staff, date__month=instance.date.month, date__year=instance.date.year).update(
                    leave_count=current_leave_count, half_leave_count=current_half_leave-1, salary=current_salary+(staff.salary/(no_days*2)))
            elif attendance.is_excuseleave:
                print("excuse leave")

            if is_excuseleave:
                if StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                    excuse_leave_count = 0
                    excuse_leave_count = StaffAttendance.objects.filter(
                        date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).count()
                    if excuse_leave_count >= 12:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Selected staff cant take an excuse leave on this year"
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                    if excuse_leave_count < 12:
                        instance.date = date
                        instance.staff = staff
                        instance.is_present = is_present
                        instance.is_leave = is_leave
                        instance.is_halfday = is_halfday
                        instance.is_excuseleave = is_excuseleave
                        instance.is_work_at_home = is_work_at_home
                        instance.save()
                elif not StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=staff, is_deleted=False, is_excuseleave=True).exists():
                    instance.date = date
                    instance.staff = staff
                    instance.is_present = is_present
                    instance.is_leave = is_leave
                    instance.is_halfday = is_halfday
                    instance.is_excuseleave = is_excuseleave
                    instance.is_work_at_home = is_work_at_home
                    instance.save()

                if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                    StaffRecord.objects.create(
                        date=date,
                        staff=staff,
                        leave_count=0,
                        half_leave_count=0,
                        salary=staff.salary,
                        is_paid=False,
                        auto_id=get_auto_id(StaffRecord),
                        creator=request.user,
                        updater=request.user,
                    )
            elif is_present or is_leave or is_halfday or is_work_at_home:
                print(is_work_at_home)
                print("is_work_at_home")
                instance.date = date
                instance.staff = staff
                instance.is_present = is_present
                instance.is_leave = is_leave
                instance.is_halfday = is_halfday
                instance.is_excuseleave = is_excuseleave
                instance.is_work_at_home = is_work_at_home
                instance.save()
                if is_present or is_work_at_home:
                    leaves = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False)
                    old_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_leave=True).count()
                    half_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_halfday=True).count()
                    leaves.update(leave_count=old_leave_count,
                                  half_leave_count=half_leave_count)
                elif is_leave:
                    leaves = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False)
                    old_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_leave=True).count()
                    half_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_halfday=True).count()
                    leaves.update(leave_count=old_leave_count,
                                  half_leave_count=half_leave_count)
                    staff_record = StaffRecord.objects.get(
                        staff=staff, date__month=instance.date.month, date__year=instance.date.year)
                    current_leave_count = staff_record.leave_count
                    current_half_leave = staff_record.half_leave_count
                    current_salary = staff_record.salary
                    StaffRecord.objects.filter(staff=staff, date__month=instance.date.month, date__year=instance.date.year).update(
                        leave_count=current_leave_count+1,
                        half_leave_count=current_half_leave,
                        salary=current_salary-(staff.salary/no_days))
                elif is_halfday:
                    leaves = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False)
                    old_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_leave=True).count()
                    half_leave_count = StaffAttendance.objects.filter(
                        date__month=instance.date.month, date__year=instance.date.year, staff=staff, is_deleted=False, is_halfday=True).count()
                    leaves.update(half_leave_count=half_leave_count,
                                  leave_count=old_leave_count)
                    staff_record = StaffRecord.objects.get(
                        staff=staff, date__month=instance.date.month, date__year=instance.date.year)
                    current_leave_count = staff_record.leave_count
                    current_half_leave = staff_record.half_leave_count
                    current_salary = staff_record.salary
                    StaffRecord.objects.filter(staff=staff, date__month=instance.date.month, date__year=instance.date.year).update(
                        leave_count=current_leave_count, half_leave_count=current_half_leave, salary=current_salary-(staff.salary/(no_days*2)))
            response_data = {
                "status": "true",
                "title": "Successfully updated",
                "message": "Attendance successfully updated.",
                "redirect": "true",
                "redirect_url": reverse('staffs:staff_attendances')
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StaffAttendanceEditForm(instance=instance)
        # print(instance)
        date = instance.date
        context = {
            "title": "Edit Attendance",
            "form": form,
            "instance": instance,
            "url": url,
            "date": date,
            "is_need_popup_box": True,
            "is_need_wave_effect": True,
            "is_need_select_picker": True,
            "is_need_bootstrap_growl": True,
            "is_need_custom_scroll_bar": True,
            "is_need_datetime_picker": True,
            "is_need_grid_system": True,
            "is_need_file_input": True,
            "redirect": True,
        }
        return render(request, 'staffs/edit_staff_attendance.html', context)


@check_mode
@login_required
@ajax_required
def get_staff_designation(request):

    if request.method == 'GET':
        pk = request.GET.get('id')
        print(pk)
        if Designation.objects.filter(pk=pk, is_deleted=False).exists():
            instance = get_object_or_404(
                Designation.objects.filter(pk=pk, is_deleted=False))

            response_data = {
                "status": "true",
                'designaton': instance.name,
            }

        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": "Can't find Any Designation"
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def staff_records(request):
    instance = StaffRecord.objects.filter(is_deleted=False)

    context = {
        "instances": instance,
        "title": "Staff Records",

        "single_page": True,
    }
    return render(request, 'staffs/staff_records.html', context)


@check_mode
@login_required
def create_pay(request):
    selected_date = datetime.date.today()
    date = request.GET.get("date")

    if date:
        date_error = False
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date_error = True
        if not date_error:
            selected_date = date

    today = datetime.date.today()
    # date = request.GET.get("date")
    staffs = Staff.objects.filter(is_deleted=False)

    PayStaffFormset = formset_factory(PayStaffForm, extra=0)

    if request.method == 'POST':
        pay_form = PayForm(request.POST)
        pay_staff_formset = PayStaffFormset(
            request.POST, prefix='pay_staff_formset')

        if pay_form.is_valid() and pay_staff_formset.is_valid():
            date = pay_form.cleaned_data['date']

            is_bank_ok = True

            if is_bank_ok:
                for i in pay_staff_formset:
                    staff = i.cleaned_data['staff']
                    salary = i.cleaned_data['salary']
                    is_paid = i.cleaned_data['is_paid']
                    leave_count = i.cleaned_data['leave_count']
                    half_leave_count = i.cleaned_data['half_leave_count']

                    if is_paid:
                        creator = request.user

                        data = Pay.objects.create(
                            date=date,
                            staff=staff,
                            leave_count=leave_count,
                            half_leave_count=half_leave_count,
                            salary=salary,
                            is_paid=True,
                            auto_id=get_auto_id(Pay),
                            creator=request.user,
                            updater=creator,
                        )
                        StaffRecord.objects.filter(
                            date__month=date.month, date__year=date.year, staff=staff).update(is_paid=True)
                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Pay Slip created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('staffs:pays')
                }

            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please choose a Bank account first..!"
                }

        else:
            # message += generate_form_errors(pay_staff_formset,formset=True)
            message = generate_form_errors(pay_form, formset=False)
            print(pay_staff_formset.errors)
            print(pay_form.errors)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        initial = []
        month = selected_date.month

        for staff in staffs:
            if StaffRecord.objects.filter(date__month=selected_date.month, date__year=selected_date.year, staff=staff, is_paid=False).exists():
                pay = StaffRecord.objects.filter(
                    date__month=selected_date.month, date__year=selected_date.year, staff=staff, is_paid=False)[0]
                leave_count = pay.leave_count
                half_leave_count = pay.half_leave_count
                salary = pay.salary

                total_allowance = 0
                allowances = SalaryAllowance.objects.filter(
                    is_deleted=False, staff=staff, date__month=selected_date.month, date__year=selected_date.year)

                for item in allowances:
                    total_allowance += item.allowance

                pay_dict = {
                    'staff': staff,
                    'staff_name': str(staff.name),
                    'leave_count': leave_count,
                    'allowance': total_allowance,
                    'half_leave_count': half_leave_count,
                    'salary': round(salary, 0),
                }
                initial.append(pay_dict)

        pay_staff_formset = PayStaffFormset(
            prefix='pay_staff_formset', initial=initial)
        pay_form = PayForm(initial={"date": selected_date})

        context = {
            "staffs": staffs,
            "redirect": True,
            'initial': initial,
            "pay_form": pay_form,
            "today": selected_date,
            "title": "Create Pay Slip",
            "pay_staff_formset": pay_staff_formset,

            "is_need_popup_box": True,
            "is_need_wave_effect": True,
            "is_need_select_picker": True,
            "is_need_datetime_picker": True,
            "is_need_custom_scroll_bar": True,
            "is_need_bootstrap_growl": True,
            "is_need_chosen_select": True,
            "is_need_grid_system": True,
            "is_need_animations": True,
        }

        return render(request, 'staffs/create_pay.html', context)


@check_mode
@login_required
def pays(request):
    today = datetime.date.today()
    instances = Pay.objects.filter(is_deleted=False, date=today)

    context = {
        "instances": instances,
        "title": "Pay Slips",

        "single_page": True,

    }
    return render(request, 'staffs/pays.html', context)


@check_mode
@login_required
def pay(request):
    today = datetime.date.today()
    date_string = today
    instances_today = Pay.objects.filter(is_deleted=False, date=today)
    date = request.GET.get("date")
    date_error = False
    present_students = 0
    absent_students = 0
    leave_students = 0
    half_leave_students = 0
    excuse_leave_students = 0
    pay_staff_formset = Pay.objects.none()

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
            title = "Pay Slip %s" % (date)
            date_string = date
        except ValueError:
            date_error = True
    total_amount_paid = 0
    if not date_error and date:
        instances_today = []
        pay_staff_formset = Pay.objects.filter(
            is_deleted=False, is_paid=True, date__month=date_string.month, date__year=date_string.year)
        for i in pay_staff_formset:
            print(i.salary)
        print(pay_staff_formset)
        print('pay_staff_formset')
        pays = Pay.objects.filter(
            is_deleted=False, date__month=date_string.month, date__year=date_string.year)
        for k in pays:
            total_amount_paid += k.salary

    context = {
        "pay_staff_formset": pay_staff_formset,
        "title": "Pay Slip ",
        "instances_today": instances_today,
        "date": date,
        "date_string": date_string,
        "total_amount_paid": total_amount_paid,


        "single_page": True,

    }
    return render(request, 'staffs/pay.html', context)


@check_mode
@login_required
def edit_pay(request, pk):
    instance = get_object_or_404(Pay.objects.filter(pk=pk, is_deleted=False))
    url = reverse('staffs:edit_pay', kwargs={'pk': pk})

    if request.method == "POST":
        # previous_attendance_status = instance.is_present
        form = PayEditForm(request.POST, instance=instance)

        if form.is_valid():
            staff = instance.staff
            leave_count = form.cleaned_data['leave_count']
            date = instance.date
            half_leave_count = form.cleaned_data['half_leave_count']
            salary = form.cleaned_data['salary']
            is_paid = form.cleaned_data['is_paid']

            pay = Pay.objects.get(date=instance.date,
                                  staff=instance.staff, is_deleted=False)

            if pay.is_paid:
                Pay.objects.filter(date=instance.date, staff=instance.staff, is_deleted=False).update(
                    is_paid=False, is_deleted=True)
                StaffRecord.objects.filter(
                    date__month=pay.date.month, date__year=pay.date.year, staff=pay.staff).update(is_paid=False)

            if is_paid:
                instance.is_paid = True,
                instance.leave_count = leave_count,
                instance.half_leave_count = half_leave_count,
                instance.salary = salary,
                instance.staff = staff,
                instance.date = date,
                instance.save()
                StaffRecord.objects.filter(
                    date__month=pay.date.month, date__year=pay.date.year, staff=pay.staff).update(is_paid=True)
            response_data = {
                "status": "true",
                "title": "Successfully updated",
                "message": "Pay Slip successfully updated.",
                "redirect": "true",
                "redirect_url": reverse('staffs:pays')
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PayEditForm(instance=instance)
        print(instance)
        date = instance.date
        context = {
            "title": "Edit Pay",
            "form": form,
            "instance": instance,
            "url": url,
            "date": date,
            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "redirect": True,
            "is_need_grid_system": True,
            "is_need_file_input": True,
            "is_need_datetime_picker": True,
        }
        return render(request, 'staffs/edit_pay.html', context)


@check_mode
@login_required
def print_pay_slip(request, pk):
    instance = get_object_or_404(Pay.objects.filter(pk=pk, is_deleted=False))
    staff_data = get_object_or_404(Staff.objects.filter(pk=instance.staff.pk))
    print(instance.leave_count)
    days_worked = 0
    date = instance.date
    if StaffAttendance.objects.filter(date__month=date.month, date__year=date.year, staff=instance.staff).exists():
        days_worked = StaffAttendance.objects.filter(
            date__month=date.month, date__year=date.year, is_present=True, staff=instance.staff).count()

    days_in_month = monthrange(date.year, date.month)[1]

    print(instance.staff)
    leave_amount = 0
    leave_count = instance.leave_count
    leave_amount = leave_count * (instance.staff.salary/days_in_month)

    allowances = SalaryAllowance.objects.filter(
        date__month=date.month, date__year=date.year, staff=instance.staff, is_deleted=False)
    total_allowance = 0
    for item in allowances:
        total_allowance += item.allowance

    half_leave_amount = 0
    half_leave_count = instance.half_leave_count
    half_leave_amount = half_leave_count * \
        (instance.staff.salary/(days_in_month*2))

    total_earnings = 0
    total_earnings = instance.staff.salary + total_allowance
    total_deduction = 0
    total_deduction = half_leave_amount + leave_amount

    net_salary = 0
    net_salary = round((total_earnings - total_deduction), 0)
    two_decimal_net_salary = "{:10.2f}".format(net_salary)
    salary_in_words = num2words(two_decimal_net_salary)

    print(days_in_month)
    abscent_days = 0
    abscent_days = leave_count + decimal.Decimal(0.5) * half_leave_count

    context = {
        "instance": instance,
        "title": "Pay Slip",
        "days_worked": days_worked,
        "leave_amount": leave_amount,
        "half_leave_amount": half_leave_amount,
        "net_salary": net_salary,
        "total_deduction": total_deduction,
        "salary_in_words": salary_in_words,
        "days_in_month": days_in_month,
        "abscent_days": round(abscent_days, 2),
        "total_allowance": total_allowance,
        "staff_data": staff_data,

        "single_page": True,
    }
    return render(request, 'staffs/pay_slip.html', context)


@check_mode
@login_required
@permissions_required(['can_view_staff_attendance'])
def staff_attendance_single(request, pk):
    print("single View")
    today = datetime.date.today()
    instances = StaffAttendance.objects.filter(
        is_deleted=False, date=today, staff=pk)
    # for r in instances:
    #     print(r.staff.first_name)
    #     print(r.date)
    staff = None
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)

    context = {
        "instances": instances,
        "title": "Indograce Staff Attendance",
        "staff_data": staff,

        "single_page": True,
    }
    return render(request, 'staffs/staff_attendance.html', context)


@login_required
@permissions_required(['can_view_staff_attendance'])
def staff_attendance_single_view(request, pk):
    today = datetime.date.today()
    date_string = today
    instances_today = StaffAttendance.objects.filter(
        is_deleted=False, date=today, staff=pk)
    date = request.GET.get("date")
    date_error = False
    present_students = 0
    absent_students = 0
    leave_students = 0
    half_leave_students = 0
    excuse_leave_students = 0
    work_at_home_students = 0
    attendance_item_formset = StaffAttendance.objects.none()

    if date:
        try:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
            title = "Attendances %s" % (date)
            date_string = date
        except ValueError:
            date_error = True

    if not date_error and date:
        instances_today = []
        attendance_item_formset = StaffAttendance.objects.filter(
            is_deleted=False, date=date_string, staff=pk)

    present_students = StaffAttendance.objects.filter(
        is_deleted=False, is_present=True, date=date_string).count()
    absent_students = StaffAttendance.objects.filter(
        is_deleted=False, is_present=False, is_work_at_home=False, date=date_string).count()
    leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_leave=True, date=date_string).count()
    half_leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_halfday=True, date=date_string).count()
    excuse_leave_students = StaffAttendance.objects.filter(
        is_deleted=False, is_excuseleave=True, date=date_string).count()
    work_at_home_students = StaffAttendance.objects.filter(
        is_deleted=False, is_work_at_home=True, date=date_string).count()

    present = request.GET.get("present")
    absent = request.GET.get("absent")
    leave = request.GET.get("leave")
    half_leave = request.GET.get("half_leave")
    excuse_leave = request.GET.get("excuse_leave")
    work_at_home = request.GET.get("work_at_home")

    if present:
        attendance_item_formset = attendance_item_formset.filter(
            is_present=present, date=date_string, staff=pk)

    if absent:
        attendance_item_formset = attendance_item_formset.filter(
            is_present=absent, date=date_string, staff=pk)

    if leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_leave=leave, date=date_string, staff=pk)

    if excuse_leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_excuseleave=excuse_leave, date=date_string, staff=pk)

    if half_leave:
        attendance_item_formset = attendance_item_formset.filter(
            is_halfday=half_leave, date=date_string, staff=pk)
    if work_at_home:
        attendance_item_formset = attendance_item_formset.filter(
            is_work_at_home=work_at_home, date=date_string, staff=pk)

    staff = None
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)

    context = {
        "attendance_item_formset": attendance_item_formset,
        "title": "Staff Attendance ",
        "instances_today": instances_today,
        "present_students": present_students,
        "absent_students": absent_students,
        "excuse_leave_students": excuse_leave_students,
        "half_leave_students": half_leave_students,
        "leave_students": leave_students,
        "work_at_home_students": work_at_home_students,
        "date": date,
        "date_string": date_string,
        "staff_data": staff,
        "single_page": True,
    }
    return render(request, 'staffs/staff_single_attendance.html', context)


@check_mode
@login_required
@permissions_required(['can_view_staff_salary'])
def staff_salary(request, pk):
    date = datetime.datetime.now()
    instances = Pay.objects.filter(
        is_deleted=False, is_paid=True, staff__pk=pk)

    staff = None
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)

    context = {
        "title": "Dashboard",
        "instances": instances,
        "staff_data": staff,

        "is_dashboard": True

    }
    return render(request, "staffs/staff_salary.html", context)


@check_mode
@login_required
@permissions_required(['can_view_staff'])
def staff_permissions(request, pk):
    date = datetime.datetime.now()
    staff = Staff.objects.get(pk=pk)

    permissions = staff.permission.all()
    sales_permissions = permissions.filter(app="sales")
    admin_permissions = permissions.filter(app="admin")
    staffs_permissions = permissions.filter(app="staffs")
    report_permissions = permissions.filter(app="reports")
    vendors_permissions = permissions.filter(app="vendors")
    finance_permissions = permissions.filter(app="finance")
    account_permissions = permissions.filter(app="accounts")
    products_permissions = permissions.filter(app="products")
    purchase_permissions = permissions.filter(app="purchases")
    customers_permissions = permissions.filter(app="customers")
    crm_permissions = permissions.filter(
        Q(app="quotations") | Q(app="client_relation"))

    context = {
        "staff_data": staff,
        "title": "Staff Permissions",
        "sales_permissions": sales_permissions,
        "admin_permissions": admin_permissions,
        "staffs_permissions": staffs_permissions,
        "report_permissions": report_permissions,
        "vendors_permissions": vendors_permissions,
        "finance_permissions": finance_permissions,
        "account_permissions": account_permissions,
        "products_permissions": products_permissions,
        "purchase_permissions": purchase_permissions,
        "customers_permissions": customers_permissions,
        "crm_permissions": crm_permissions,

    }

    return render(request, "staffs/staff_permissions.html", context)


@check_mode
@login_required
def export_staff_report(request):
    instances = Staff.objects.filter(is_deleted=False)
    title = "Staff Report"

    wb = xlwt.Workbook()
    ws = wb.add_sheet(title)

    ws.write(0, 0, "Staff Id")
    ws.write(0, 1, "Name")
    ws.write(0, 2, "Designation")
    ws.write(0, 3, "Phone")
    ws.write(0, 4, "Email Id")
    ws.write(0, 5, "Salary")

    print("instances")
    print(instances)
    if instances:
        count = 1
        for instance in instances:
            if instance.auto_id:
                ws.write(count, 0, instance.auto_id)
            if instance.name:
                ws.write(count, 1, instance.name)
            if instance.designation:
                ws.write(count, 2, instance.designation.name)
            if instance.phone:
                ws.write(count, 3, instance.phone)
            if instance.email:
                ws.write(count, 4, instance.email)
            if instance.salary:
                ws.write(count, 5, instance.salary)
            count += 1

    media_root = settings.MEDIA_ROOT + '/excel_report.xls'
    wb.save(media_root)
    protocol = "http://"
    if request.is_secure():
        protocol = "https://"

    host_name = request.get_host()
    full_url = protocol + host_name + '/media/excel_report.xls'

    response_data = {
        "status": "true",
        "file_url": full_url
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def salary_report(request):
    instances = Pay.objects.filter(is_deleted=False).order_by('auto_id')

    filter_date = request.GET.get('date')

    if not filter_date:
        filter_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%m/%d/%Y')

    date = datetime.datetime.strptime(filter_date, '%m/%d/%Y')

    instances = instances.filter(date__month=date.month, date__year=date.year)

    month_name = datetime.datetime.strftime(date, '%B %Y')
    title = "Salary Report of " + month_name

    context = {
        'title': title,
        "instances": instances,
        'filter_date': filter_date,
        "allowed_roles": ['main-operating_officer', 'superadmin']
    }

    return render(request, 'staffs/salary_report.html', context)


@check_mode
@login_required
def export_staff_salary_report(request):
    instances = Pay.objects.filter(is_deleted=False)
    title = "Salary Report"

    wb = xlwt.Workbook()
    ws = wb.add_sheet(title)

    ws.write(0, 0, "Id")
    ws.write(0, 1, "Staff")
    ws.write(0, 2, "Leave Count")
    ws.write(0, 3, "Half Leave Count")
    ws.write(0, 4, "Salary")
    ws.write(0, 5, "Date of Payment")

    if instances:
        print("instances")
        print(instances)
        count = 1
        for instance in instances:
            if instance.auto_id:
                ws.write(count, 0, instance.auto_id)
            if instance.staff:
                ws.write(count, 1, instance.staff.name)
            if instance.leave_count:
                ws.write(count, 2, instance.leave_count)
            if instance.half_leave_count:
                ws.write(count, 3, instance.half_leave_count)
            if instance.salary:
                ws.write(count, 4, instance.salary)
            if instance.date:
                ws.write(count, 5, instance.date)
            count += 1

    media_root = settings.MEDIA_ROOT + '/excel_report.xls'
    wb.save(media_root)
    protocol = "http://"
    if request.is_secure():
        protocol = "https://"

    host_name = request.get_host()
    full_url = protocol + host_name + '/media/excel_report.xls'

    response_data = {
        "status": "true",
        "file_url": full_url
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_staff_details(request):
    pk = request.GET.get('id')
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)
        response_data = {
            "status": "true",
            'salary': staff.salary,
        }
    else:
        response_data = {
            "status": "false",
            "message": "Staff not found"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_staff_salary_to_pay(request):
    pk = request.GET.get('id')
    if Staff.objects.filter(pk=pk).exists():
        staff = Staff.objects.get(pk=pk)
        total = 0
        if StaffRecord.objects.filter(is_deleted=False, is_paid=False, staff=staff).exists():
            records = StaffRecord.objects.filter(
                is_deleted=False, is_paid=False, staff=staff)
            for i in records:
                amount = i.salary - i.paid_amount
                total += amount

        total -= staff.advance_salary

        response_data = {
            "status": "true",
            'payable': str(round(total, 0)),
        }
    else:
        response_data = {
            "status": "false",
            "message": "Staff not found"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def create_salary_allowance(request):
    if request.method == 'POST':
        form = SalaryAllowanceForm(request.POST)
        if form.is_valid():
            staff = form.cleaned_data['staff']
            date = form.cleaned_data['date']

            data = form.save(commit=False)
            data.auto_id = get_auto_id(SalaryAllowance)
            data.creator = request.user
            data.updater = request.user
            data.save()

            days = monthrange(date.year, date.month)[1]

            if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                StaffRecord.objects.create(
                    date=date,
                    staff=staff,
                    leave_count=0,
                    half_leave_count=0,
                    salary=staff.salary,
                    is_paid=False,
                    auto_id=get_auto_id(StaffRecord),
                    creator=request.user,
                    updater=request.user,
                )
            if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                leaves = StaffAttendance.objects.filter(
                    date__month=date.month, date__year=date.year, staff=staff, is_deleted=False)

                old_leave_count = leaves.filter(is_leave=True).count()
                half_leave_count = leaves.filter(is_halfday=True).count()
                leaves.update(leave_count=old_leave_count,
                              half_leave_count=half_leave_count)
                salary = staff.salary

                amount = 0
                allowances = SalaryAllowance.objects.filter(
                    is_deleted=False, staff=staff, date__month=date.month, date__year=date.year)
                for item in allowances:
                    amount += item.allowance

                total_subtractions = old_leave_count * \
                    (salary/days) + half_leave_count * (salary/(days * 2))

                total_salary = salary - total_subtractions + amount

                StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(
                    date=date,
                    leave_count=old_leave_count,
                    half_leave_count=half_leave_count,
                    salary=total_salary
                )
            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Allowance created successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:allowance', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status": "false",
                "stable": 'true',
                "title": "Form Validation Error",
                "message": message,
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SalaryAllowanceForm(initial={'allowance_type': 'over time'})
        context = {
            'form': form,
            'date': datetime.datetime.now(),
            "title": 'Create Salary Allowance',
        }
        return render(request, 'staffs/allowance/entry_allowance.html', context)


@check_mode
@login_required
def allowances(request):
    instances = SalaryAllowance.objects.filter(is_deleted=False)

    query = request.GET.get("q")
    print("query", query)
    if query:
        instances = instances.filter(Q(staff__name__icontains=query))

    staff = request.GET.get("staff")
    if staff:
        instances = instances.filter(staff=staff)

    context = {
        'instances': instances,
        "title": 'Salary Allowances',

    }
    return render(request, "staffs/allowance/allowances.html", context)


@check_mode
@login_required
def delete_salary_allowance(request, pk):
    instance = SalaryAllowance.objects.get(pk=pk)
    instance.is_deleted = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()
    date = instance.date
    staff = instance.staff

    if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
        leaves = StaffAttendance.objects.filter(
            date__month=date.month, date__year=date.year, staff=staff, is_deleted=False)

        old_leave_count = leaves.filter(is_leave=True).count()
        half_leave_count = leaves.filter(is_halfday=True).count()
        leaves.update(leave_count=old_leave_count,
                      half_leave_count=half_leave_count)
        salary = staff.salary

        amount = 0
        allowances = SalaryAllowance.objects.filter(
            is_deleted=False, staff=staff, date__month=date.month, date__year=date.year)
        for item in allowances:
            amount += item.allowance

        days = monthrange(date.year, date.month)[1]
        total_subtractions = old_leave_count * \
            (salary/days) + half_leave_count * (salary/(days * 2))

        total_salary = salary - total_subtractions + amount

        StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(
            date=date,
            leave_count=old_leave_count,
            half_leave_count=half_leave_count,
            salary=total_salary
        )

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Allowance Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('staffs:allowances')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def allowance(request, pk):
    instance = SalaryAllowance.objects.get(is_deleted=False, pk=pk)

    context = {
        'instance': instance,
        "title": 'Salary Allowance',
    }
    return render(request, "staffs/allowance/allowance.html", context)


@check_mode
@login_required
def edit_salary_allowance(request, pk):
    instance = SalaryAllowance.objects.get(pk=pk)
    if request.method == 'POST':
        form = SalaryAllowanceForm(request.POST, instance=instance)
        if form.is_valid():
            staff = form.cleaned_data['staff']
            date = form.cleaned_data['date']

            data = form.save(commit=False)
            data.date_updated = datetime.datetime.now()
            data.updater = request.user
            data.save()

            days = monthrange(date.year, date.month)[1]

            if not StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                StaffRecord.objects.create(
                    date=date,
                    staff=staff,
                    leave_count=0,
                    half_leave_count=0,
                    salary=staff.salary,
                    is_paid=False,
                    auto_id=get_auto_id(StaffRecord),
                    creator=request.user,
                    updater=request.user,
                )
            if StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).exists():
                leaves = StaffAttendance.objects.filter(
                    date__month=date.month, date__year=date.year, staff=staff, is_deleted=False)

                old_leave_count = leaves.filter(is_leave=True).count()
                half_leave_count = leaves.filter(is_halfday=True).count()
                leaves.update(leave_count=old_leave_count,
                              half_leave_count=half_leave_count)
                salary = staff.salary

                amount = 0
                allowances = SalaryAllowance.objects.filter(
                    is_deleted=False, staff=staff, date__month=date.month, date__year=date.year)
                for item in allowances:
                    amount += item.allowance

                total_subtractions = old_leave_count * \
                    (salary/days) + half_leave_count * (salary/(days * 2))

                total_salary = salary - total_subtractions + amount

                StaffRecord.objects.filter(staff=staff, date__month=date.month, date__year=date.year).update(
                    date=date,
                    leave_count=old_leave_count,
                    half_leave_count=half_leave_count,
                    salary=total_salary
                )
            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Allowance Updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('staffs:allowance', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {
                "status": "false",
                "stable": 'true',
                "title": "Form Validation Error",
                "message": message,
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SalaryAllowanceForm(instance=instance)
        context = {
            'form': form,
            'instance': instance,
            'date': instance.date,
            "title": 'Update Salary Allowance',
        }
        return render(request, 'staffs/allowance/entry_allowance.html', context)
