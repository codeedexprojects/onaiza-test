from django.shortcuts import render
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.translation import activate
from main.functions import get_current_role
from main.models import Mode
from staffs.models import Staff
import json
from customers.models import Customer


def ajax_required(function):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return render(request, 'error/400.html', {})
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def role_required(roles):
    def _method_wrapper(view_method):
        def _arguments_wrapper(request, *args, **kwargs):
            current_role = get_current_role(request)

            if not current_role in roles:
                if request.is_ajax():
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Permission Denied",
                        "message": "You have no permission to do this action."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    # pass
                    is_user = False
                    title = "Internal Server Error"

                    if not request.user.is_superuser:
                        is_user = True
                        title = "Access Denied !"

                    context = {
                        "title": title,
                        "is_user": is_user,
                    }
                    return render(request, 'error/500.html', context)

            return view_method(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper


def check_mode(function):
    def wrap(request, *args, **kwargs):
        mode = Mode.objects.get(id=1)
        readonly = mode.readonly
        maintenance = mode.maintenance
        down = mode.down

        # if down:
        #     if request.is_ajax():
        #         response_data = {}
        #         response_data['status'] = 'false'
        #         response_data['message'] = "Application currently down. Please try again later."
        #         response_data['static_message'] = "true"
        #         return HttpResponse(json.dumps(response_data), content_type='application/javascript')
        #     else:
        #         return HttpResponseRedirect(reverse('down'))
        # elif readonly:
        #     if request.is_ajax():
        #         response_data = {}
        #         response_data['status'] = 'false'
        #         response_data['message'] = "Application now readonly mode. please try again later."
        #         response_data['static_message'] = "true"
        #         return HttpResponse(json.dumps(response_data), content_type='application/javascript')
        #     else:
        #         return HttpResponseRedirect(reverse('read_only'))

        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def permissions_required(permissions, roles=['staff', 'customer'], all_permissions=False, all_roles=False, both_check=True, super_user_ok=True, allow_self=False, model=None):

    def _method_wrapper(view_method):

        def _arguments_wrapper(request, *args, **kwargs):
            has_permission = False
            if request.user.is_superuser:
                has_permission = True
            elif Staff.objects.filter(is_deleted=False, user=request.user).exists():
                staff = Staff.objects.get(is_deleted=False, user=request.user)
                staff_permissions = staff.permission.all()
                for p in staff_permissions:
                    if p.code in permissions:
                        has_permission = True

            if not has_permission:
                if request.is_ajax():
                    response_data = {}
                    response_data['status'] = 'false'
                    response_data['stable'] = 'true'
                    response_data['title'] = 'Permission Denied'
                    response_data['message'] = "You have no permission to do this action."
                    response_data['static_message'] = "true"
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    context = {
                    }
                    return render(request, 'error/permission_denied.html', context)

            return view_method(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper



def customer_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.is_ajax():
                next_login = request.META['HTTP_REFERER']
                response_data = {}
                response_data['status'] = 'redirect'
                response_data['redirect_url'] = f'{reverse("web:login")}?next_login={next_login}'
                response_data['message'] = "Login First"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                next_login = request.path
                return HttpResponseRedirect(f'{reverse("web:login")}?next_login={next_login}')
        elif not Customer.objects.filter(user=request.user).exists():
            if request.is_ajax():
                response_data = {}
                next_login = request.META['HTTP_REFERER']
                response_data['status'] = 'redirect'
                response_data['redirect_url'] = f'{reverse("web:userlogin")}?next_login={next_login}'
                response_data['message'] = "Login First"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                next_login = request.path
                return HttpResponseRedirect(f'{reverse("web:userlogin")}?next_login={next_login}')
        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap