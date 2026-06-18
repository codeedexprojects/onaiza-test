# django libraries
import datetime
# standard libraries
import json

from api.v1.delivery_agent.serializers import DeliveryAgentExportSerializer
# local libraries
from api.v1.users.functions import encrypt_message, decrypt_message
from delivery_agent.delivery_agent_utils import DeliveryAgentUtils
from delivery_agent.forms import *
from delivery_agent.functions import get_all_delivery_agents
from delivery_agent.models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from main.functions import generate_form_errors, get_auto_id
from main.utils.export_to_excel import ExportToExcelUtils
from customers.models import UserOtpData


class DeliveryAgentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = DeliveryAgents.objects.filter(is_deleted=False).order_by('name', 'auto_id')
        if self.q:
            items = items.filter(Q(auto_id__iexact=self.q) | Q(name__icontains=self.q))

        return items


@login_required
def create_delivery_agent(request):
    if request.method == "POST":
        form = DeliveryAgentForm(request.POST, request.FILES)

        if form.is_valid():
            phone1 = form.cleaned_data['phone1']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if not DeliveryAgents.objects.filter(user__username=phone1, is_deleted=False).exists():
                if User.objects.filter(username=phone1).exists():
                    user_data = User.objects.get(username=phone1)

                    if User.objects.filter(email=email).exclude(pk=user_data.pk).exists():
                        pass
                        user_data.set_password(password)
                    else:
                        user_data.set_password(password)
                        user_data.email = email
                    user_data.save()

                    UserOtpData.objects.filter(phone=phone1).update(password=str(encrypt_message(password)))

                else:
                    user_data = User.objects.create_user(username=phone1, email=email, password=password)

                if Group.objects.filter(name="delivery_agent").exists():
                    group = Group.objects.get(name="delivery_agent")
                else:
                    group = Group.objects.create(name="delivery_agent")

                user_data.groups.add(group)

                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = get_auto_id(DeliveryAgents)

                data.password = encrypt_message(password)
                data.user = user_data

                data.save()

                return JsonResponse({
                    "status": "true",
                    'error': False,
                    "title": "Successfully Created",
                    'message': 'Delivery Agent Successfully Created',
                    "redirect": 'true',
                    "redirect_url": reverse('delivery_agent:delivery_agent', kwargs={"pk": data.pk})
                })
            else:
                return JsonResponse({
                    "status": "false",
                    "title": "Form validation failed",
                    'message': 'Delivery Agent with this phone number already exist',
                })
        else:

            return JsonResponse({'error': True, 'errors': form.errors})

    else:
        form = DeliveryAgentForm()
        context = {"form": form, "title": "Create Delivery Agent", "redirect": True,
                   "url": reverse("delivery_agent:create_delivery_agent"), "is_category": True, "is_product": True, }

        return render(request, 'delivery/agents/entry.html', context)


@login_required
def delivery_agent(request, pk):
    instance = get_object_or_404(DeliveryAgents.objects.filter(pk=pk))
    password = decrypt_message(instance.password)

    context = {"title": "Delivery Agent : " + instance.name, "instance": instance, "password": password}

    return render(request, 'delivery/agents/agent.html', context)


@login_required
def delivery_agents(request):
    instances = DeliveryAgents.objects.filter(is_deleted=False)

    query = request.GET.get('q')
    if query:
        instances = instances.filter(Q(name__icontains=query))

    context = {"title": "Delivery Agents", "instances": instances, }

    return render(request, 'delivery/agents/agents.html', context)


@login_required
def delete_delivery_agent(request, pk):
    reason = request.GET.get('reason')
    DeliveryAgents.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Agent Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('delivery_agent:delivery_agents')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def edit_delivery_agent(request, pk):
    instance = get_object_or_404(DeliveryAgents, pk=pk)

    if request.method == "POST":
        form = DeliveryAgentForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.date_updated = datetime.datetime.now()
            data.save()

            return JsonResponse(
                {"status": "true", 'error': False, 'message': 'Agent Updated Successfully', "redirect": 'true',
                 "redirect_url": reverse('delivery_agent:delivery_agent', kwargs={"pk": pk})})

        else:
            print("FORM +=?>>>>", form.data)
            message = generate_form_errors(form, formset=False)
            return JsonResponse({
                'error': True,
                'status': "false",
                'stable': "true",
                'title': "Form Validation Failed",
                'message': message,
            })

    else:
        form = DeliveryAgentForm(instance=instance)
        # form.fields.pop('password')

        context = {"form": form, "title": "Edit Agent", "redirect": True,
                   "url": reverse("delivery_agent:edit_delivery_agent", kwargs={"pk": pk}), "pk": pk, "is_edit": True,
                   "instance": instance, }

    return render(request, 'delivery/agents/entry.html', context)


@login_required
def get_delivery_agents(request):
    data = []
    if DeliveryAgents.objects.filter(is_deleted=False, ).exists():
        instances = DeliveryAgents.objects.filter(is_deleted=False, ).order_by('name').values_list('name', 'pk')

        for i in instances:
            obj = {'name': i[0], 'pk': str(i[1])}
            data.append(obj)

        response_data = {"status": "true", "model": 'DeliveryAgent', "instances": data}
    else:
        response_data = {"status": "false", "message": "No delivery agents found"}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def delivery_agent_export(request):
    instances = get_all_delivery_agents()

    export_to_excel_utils = ExportToExcelUtils(instances, DeliveryAgentExportSerializer, request, "delivery_agents")

    returned_file_url = export_to_excel_utils.export_to_excel()
    return HttpResponseRedirect(returned_file_url)


@login_required
def view_detail_report(request, pk):
    delivery_agent_utils = DeliveryAgentUtils(agent_pk=pk)
    instances = delivery_agent_utils.get_all_order_including_distance()

    context = {"instances": instances, }

    return render(request, 'delivery/agents/agent_report.html', context)


@login_required
def hand_over_details(request):
    delivery_agent = request.GET.get('delivery_agent', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    delivery_agent_utils = DeliveryAgentUtils()

    instances = delivery_agent_utils.handover_details(delivery_agent=delivery_agent, start_date=start_date,
                                                      end_date=end_date)
    delivery_agents = delivery_agent_utils.get_all_agents()

    context = {"instances": instances, "agents": delivery_agents}

    return render(request, 'delivery/agents/agent_hand_over.html', context)


@login_required
def approve_hand_over(request, pk):
    delivery_agent_utils = DeliveryAgentUtils()
    delivery_agent_utils.approve_hand_over(pk)

    response_data = {"status": "true", "title": "Successfully Approved",
                     "message": "Amount handover successfully approved !", "redirect": "true",
                     "redirect_url": reverse('delivery_agent:hand_over_details')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def decline_hand_over(request, pk):
    reason = request.GET.get('reason')
    delivery_agent_utils = DeliveryAgentUtils()
    delivery_agent_utils.decline_decline_hand_over(pk, reason)

    response_data = {"status": "true", "title": "Successfully Declined",
                     "message": "Amount handover successfully declined !", "redirect": "true",
                     "redirect_url": reverse('delivery_agent:hand_over_details')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')