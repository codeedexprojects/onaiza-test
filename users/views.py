from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, time
from main.functions import get_auto_id, generate_form_errors, get_otp, get_ip, sendSMS
from main.decorators import ajax_required
import json
from users import forms
from django.contrib.auth import login as auth_login
from users.forms import *
from main.forms import *
from django.http import JsonResponse
from django.conf import settings
import datetime
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model, login, logout, authenticate, update_session_auth_hash
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.shortcuts import resolve_url
from users import models

from general.functions import render_to_pdf


def get_success_url_allowed_hosts(request):
    success_url_allowed_hosts = set()
    return {request.get_host(), *success_url_allowed_hosts}


def get_redirect_url(request):
    redirect_field_name = REDIRECT_FIELD_NAME
    redirect_to = request.POST.get(
        redirect_field_name,
        request.GET.get(redirect_field_name, '')
    )
    url_is_safe = url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts=get_success_url_allowed_hosts(request),
        require_https=request.is_secure(),
    )
    return redirect_to if url_is_safe else ''


def login_enter(request):
    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            next_login = request.POST.get('next_login')
            user_type = request.POST.get('user_type')
            redirect_url = reverse('web:index')

            if next_login:
                redirect_url = next_login

            user = authenticate(username=username, password=password)

            if not user:
                user = authenticate(email=username, password=password)

            if not user:
                message = "Customer with this username and password does not exist."
                if user_type == "lawyer":
                    message = "Lawyer with this username and password does not exist."
                response_data = {
                    'status': 'false',
                    'stable': 'true',
                    "redirect": 'true',
                    'redirect_url': reverse('web:index'),
                    'title': "User not exists",
                    "message": message
                }
            else:
                auth_login(request, user)
                response_data = {

                    'status': 'true',
                    'stable': 'true',
                    "redirect": 'true',
                    "reload": 'true',
                    'redirect_url': reverse('web:index'),
                }

        else:
            username = request.POST.get('username')
            message = ""
            if not username:
                message += "Email field is required "

            password = request.POST.get('password')
            if not password:
                message += "| password field is required"

            response_data = {
                'status': 'false',
                'stable': 'false',
                'title': "Invalid Credential",
                "message": message,
                "redirect": 'false',
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        next_login = request.GET.get('next_login')
        form = LoginForm()
        context = {
            "title": "Login",
            "next_login": next_login,
            "form": form,
        }
        return render(request, 'registration/login.html', context)


def registration(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            if Group.objects.filter(name="customer_user").exists():
                group = Group.objects.get(name="customer_user")
            else:
                group = Group.objects.create(name="customer_user")

            user.groups.add(group)

            auto_id = get_auto_id(models.RegistrationProfile)
            profile = models.RegistrationProfile(
                phone=phone,
                auto_id=auto_id,
                user=user,
            )
            profile.save()

            auto_id = get_auto_id(models.UserLogin)
            otp = get_otp()
            login = models.UserLogin(
                auto_id=auto_id,
                ip=get_ip(request),
                user=user,
                otp=otp
            )
            login.save()

            # message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."

            msg = sendSMS('otp', phone, [otp])
            print('\n\n-------------', otp, '-------------\n\n')

            return HttpResponseRedirect(reverse("users:verify", kwargs={"pk": login.pk}))
        else:
            form = SignUpForm(request.POST)
            context = {
                'form': form,
            }
            return render(request, 'registration/registration_form.html', context)
    else:
        form = SignUpForm()
        context = {
            'form': form,
        }
        return render(request, 'registration/registration_form.html', context)


def user_logout(request):
    logout(request)
    context = {

    }
    return render(request, 'registration/logout.html', context)


def verify_success(request):
    context = {

    }
    return render(request, 'registration/verify-success.html', context)


@login_required
def change_password(request, pk):
    instance = get_object_or_404(User.objects.filter(pk=pk, is_active=True))

    if request.method == "POST":
        response_data = {}
        form = PasswordChangeForm(user=instance, data=request.POST)

        if form.is_valid():
            form.save()

            response_data = {
                'status': 'true',
                'title': "Successfully Changed",
                'redirect': 'false',
                'message': "Password Successfully Changed."
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
                "message": message,
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        title = "Change Password"
        change_password_form = PasswordChangeForm(user=instance)

        for item in change_password_form.fields:
            change_password_form.fields[item].widget.attrs['class'] = 'form-control'

        context = {
            "change_password_form": change_password_form,
            "title": title,
            "instance": instance,
        }
        return render(request, 'users/change_password.html', context)


@login_required
def notifications(request):
    title = "Notifications"
    instances = Notification.objects.filter(is_deleted=False,user=request.user)
    query = request.GET.get("q")

    if query:
        instances = instances.filter(Q(subject__name__icontains=query) | Q(message__istartswith=query))
        title = "Notifications - %s" %query

    context = {
        'title' : title,
        "instances" : instances,
    }
    return render(request,"users/notifications.html",context)


@login_required
def notification_redirect_view(request, pk):
    reverse_url = reverse('users:notifications')
    instance = get_object_or_404(Notification, pk=pk)

    instance.is_read = True
    # instance.is_active = False
    # instance.is_visited = True
    instance.save()

    if instance.subject.code == 'product_low_stock':
        reverse_url = reverse('products:product_low_stock_report')

    elif instance.subject.code == 'batch_expiry_date_reached':
        reverse_url = reverse('products:product_expiry_report')

    return HttpResponseRedirect(reverse_url)


@login_required
@ajax_required
def read_notification(request, pk):
    Notification.objects.filter(pk=pk).update(is_read=True)

    response_data = {
        "status": "true",
        "title": "Successfully Readed",
        "message": "Notification Readed successfully.",
        "redirect": "true",
        "redirect_url": reverse('users:notifications')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
def read_selected_notification(request):
    pks = request.GET.get('pk')

    if pks:
        pks = pks[:-1]
        pks = pks.split(',')

        for pk in pks:
            instance = get_object_or_404(
                Notification.objects.filter(pk=pk, is_read=False))
            Notification.objects.filter(pk=pk).update(
                is_read=True)

        response_data = {
            "status": "true",
            "title": "Successfully Readed",
            "message": "Selected Notification Successfully Readed.",
            "redirect": "true",
            "redirect_url": reverse('users:notifications')
        }
    else:

        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



