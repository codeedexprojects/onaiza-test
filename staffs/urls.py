from django.urls import path, re_path
from django.contrib import admin
from django.urls import reverse
from staffs import views
from dal import autocomplete
from staffs.views import DesignationAutocomplete, StaffAutocomplete, WarehouseManagerAutocomplete

app_name = 'staffs'


urlpatterns = [
    re_path(r'^warehouse-manager-autocomplete/$', WarehouseManagerAutocomplete.as_view(),name='warehouse_manager_autocomplete'),
    re_path(r'^staff-autocomplete/$', StaffAutocomplete.as_view(),name='staff_autocomplete'),
    re_path(r'^designation-autocomplete/$', DesignationAutocomplete.as_view(create_field='name'), name='designation_autocomplete'),

    re_path(r'^designation/create/$', views.create_designation,name='create_designation'),
    re_path(r'^designation/edit/(?P<pk>.*)/$',views.edit_designation, name='edit_designation'),
    re_path(r'^designation/view/(?P<pk>.*)/$',views.designation, name='designation'),
    re_path(r'^designations-delete/(?P<pk>.*)/$',views.delete_designation, name='delete_designation'),
    re_path(r'^designations/$', views.designations, name='designations'),
    re_path(r'^get-designation-details/$', views.get_staff_designation,name='get_staff_designation'),

    re_path(r'^$', views.staffs, name='staffs'),
    re_path(r'^create/$', views.create_staff, name='create_staff'),
    re_path(r'^staff/view/(?P<pk>.*)/$', views.view_staff, name='view_staff'),
    re_path(r'^edit/staff/(?P<pk>.*)/$', views.edit_staff, name='edit_staff'),
    re_path(r'^delete-selected-staffs', views.delete_selected_staffs,name='delete_selected_staffs'),
    re_path(r'^staff/delete/(?P<pk>.*)/$',views.delete_staff, name='delete_staff'),

    re_path(r'^staffs', views.staffs_report, name='staffs_report'),
    re_path(r'^set-permissions/(?P<pk>.*)/$',views.set_permissions, name='set_permissions'),
    re_path(r'^staff-about/(?P<pk>.*)/$',views.staff_about, name='staff_about'),
    re_path(r'^staff-records/$', views.staff_records, name='staff_records'),

    re_path(r'^create/staff-attendance/$', views.create_staff_attendance,name='create_staff_attendance'),
    re_path(r'^edit/staff-attendence/(?P<pk>.*)/$',views.edit_staff_attendance, name='edit_staff_attendance'),
    re_path(r'^staff-attendances/$', views.staff_attendances, name='staff_attendances'),
    re_path(r'^staff-attendance/view/$', views.staff_attendance, name='staff_attendance'),

    re_path(r'^print-pay-slip/(?P<pk>.*)/$',views.print_pay_slip, name='print_pay_slip'),
    re_path(r'^pay/create/$', views.create_pay, name='create_pay'),
    re_path(r'^pays/$', views.pays, name='pays'),
    re_path(r'^pay/$', views.pay, name='pay'),
    re_path(r'^pay/edit/(?P<pk>.*)/$', views.edit_pay, name='edit_pay'),

    re_path(r'^staff/staff-attendance-single/(?P<pk>.*)/$',views.staff_attendance_single, name='staff_attendance_single'),
    re_path(r'^staff/staff-attendance-single-view/(?P<pk>.*)/$',views.staff_attendance_single_view, name='staff_attendance_single_view'),
    re_path(r'^staff/staff-salary/(?P<pk>.*)/$',views.staff_salary, name='staff_salary'),
    re_path(r'^staff-permissions/(?P<pk>.*)/$',views.staff_permissions, name='staff_permissions'),

    re_path(r'^export-staff-report/$', views.export_staff_report,name='export_staff_report'),
    re_path(r'^salary-report/$', views.salary_report, name='salary_report'),
    re_path(r'^export-staff-salary-report/$', views.export_staff_salary_report,name='export_staff_salary_report'),

    re_path(r'^get-staff-details/$', views.get_staff_details, name='get_staff_details'),
    re_path(r'^get-staff-salary/$', views.get_staff_salary_to_pay,name='get_staff_salary_to_pay'),

    re_path(r'^salary-allowances/$', views.allowances, name='allowances'),
    re_path(r'^salary-allowance-create/$', views.create_salary_allowance,name='create_salary_allowance'),
    re_path(r'^salary-allowance-view/(?P<pk>.*)/$',views.allowance, name='allowance'),
    re_path(r'^salary-allowance-delete/(?P<pk>.*)/$',views.delete_salary_allowance, name='delete_salary_allowance'),
    re_path(r'^salary-allowance/edit/(?P<pk>.*)/$',views.edit_salary_allowance, name='edit_salary_allowance'),
]
