import json
import datetime
from itertools import chain
from operator import attrgetter, itemgetter
from icecream import ic as printing
# ------------------------
from django.db.models import Q, F, Sum, Count, Max
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, HttpResponseRedirect
from django.forms.models import inlineformset_factory,formset_factory
from django.forms.widgets import Select, TextInput
# ------------------------
from main.functions import generate_form_errors, get_auto_id, get_date_updated_request
from main.decorators import check_mode, ajax_required, role_required
from users.functions import get_warehouse
from finance.models import *
from finance.forms import *
from customers.functions import update_customer_credit_debit
from customers.models import Customer
from vendors.functions import update_vendor_credit_debit
from vendors.models import Vendor
from general.models import Batch
from products.models import Product, ProductVariant
from suppliers.models import Supplier
from purchases.models import Purchase
from warehouses.models import Warehouse
from sales.models import SaleReturn


''' Autocomplete '''
class AccountGroupAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = AccountGroup.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(Q(name__istartswith=self.q))
        return items


class AccountHeadAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = AccountHead.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(Q(name__istartswith=self.q))
        return items


class BankaccountAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = BankAccount.objects.filter(is_deleted=False)

        if self.q:
            query = self.q
            items = items.filter(Q(name__icontains=query))
        return items


''' Financial year '''
@check_mode
@login_required
def create_financial_year(request):
    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['start_date', 'end_date'])
        form = FinancialYearForm(ModifiedRequest)

        if form.is_valid():
            is_active = form.cleaned_data['is_active']

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = get_auto_id(FinancialYear)
            data.save()

            # if financial year added is active, then deactivate previous entries
            if FinancialYear.objects.filter(is_deleted=False).exists():
                if is_active:
                    FinancialYear.objects.filter(is_deleted=False).exclude(pk=data.pk).update(is_active=False)
            else:
                data.is_active = True

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Financial Year created successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:financial_years')
            }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')
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
        form = FinancialYearForm()

        context = {
            "title": "Create Financial Year",
            "form": form,
            "url": reverse('finance:create_financial_year'),
            "redirect": True,
        }

        return render(request, 'finance/financial_year/financial_year_entry.html', context)


@check_mode
@login_required
def financial_years(request):
    instances = FinancialYear.objects.filter(is_deleted=False)

    title = "Financial Years"
    query = request.GET.get("q")

    if query:
        instances = instances.filter(
            Q(start_date__icontains=query) |
            Q(end_date__icontains=query)
        )

    context = {
        "instances": instances,
        'title': title,
    }

    return render(request, 'finance/financial_year/financial_years.html', context)


@check_mode
@login_required
def financial_year(request, pk):
    instance = get_object_or_404(FinancialYear.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Financial Year",
    }

    return render(request, 'finance/financial_year/financial_year.html', context)


@check_mode
@login_required
def edit_financial_year(request, pk):
    instance = get_object_or_404(
        FinancialYear.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['start_date', 'end_date'])
        form = FinancialYearForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            if data.is_active:
                instances = FinancialYear.objects.filter(is_deleted=False).exclude(pk=pk).update(is_active=False)

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Financial Year Successfully Updated.",
                "redirect": "true",
                # "redirect_url": reverse('finance:financial_year', kwargs={'pk': data.pk})
                "redirect_url": reverse('finance:financial_years')
            }
        else:
            message = str(generate_form_errors(form, formset=False))

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = FinancialYearForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Financial Year",
            "instance": instance,
            "url": reverse('finance:edit_financial_year', kwargs={'pk': instance.pk}),
            "redirect": True,
        }

        return render(request, 'finance/financial_year/financial_year_entry.html', context)


@check_mode
@login_required
def delete_financial_year(request, pk):
    instance = get_object_or_404(FinancialYear.objects.filter(pk=pk, is_deleted=False))
    instance.is_deleted = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Financial Year Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('finance:financial_years')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


''' Account Account Group '''
@check_mode
@login_required
@role_required(['superadmin'])
def create_account_group(request):
    if request.method == 'POST':
        form = AccountGroupForm(request.POST)

        if form.is_valid():
            data = form.save(commit=False)
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Account Group created successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:account_groups')
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
        form = AccountGroupForm()

        context = {
            "title": "Create Account Group",
            "form": form,
            "url": reverse('finance:create_account_group'),
            "redirect": True,
        }

        return render(request, 'finance/account_group_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_account_group(request, pk):
    instance = get_object_or_404(AccountGroup, pk=pk)
    if request.method == 'POST':
        form = AccountGroupForm(request.POST, instance=instance)

        if form.is_valid():
            if not instance.code:
                data = form.save(commit=False)
                data.date_updated = datetime.datetime.now()
                data.updater = request.user
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Account Group updated successfully.",
                    "redirect": "true",
                    # "redirect_url": reverse('finance:account_group', kwargs={'pk': pk})
                    "redirect_url": reverse('finance:account_groups')
                }

            else:
                response_data = {
                    "status": "false",
                    "title": "Updation Failed",
                    "message": "You cannot edit default groups.",
                    "redirect": "true",
                    "redirect_url": reverse('finance:account_group', kwargs={'pk': pk})
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
        form = AccountGroupForm(instance=instance)

        context = {
            "title": "Edit Account Group",
            "form": form,
            "url": reverse('finance:edit_account_group', kwargs={'pk': pk}),
            "redirect": True,
        }

        return render(request, 'finance/account_group_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_account_group(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(AccountGroup, pk=pk, is_deleted=False)

    if not instance.code:
        AccountGroup.objects.filter(pk=pk).update(name=instance.name + "_deleted_" + str(instance.id), is_deleted=True,deleted_reason=reason)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "AccountGroup Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('finance:account_groups')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Deletion Failed",
            "message": "You cannot delete default groups.",

        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@role_required(['superadmin'])
def account_groups(request):
    instances = AccountGroup.objects.filter(is_deleted=False)

    title = "Account Groups"
    query = request.GET.get("q")
    if instances:
        if query:
            instances = instances.filter(Q(name__icontains=query) | Q(types__icontains=query))
        title = "Account Groups"

    context = {
        "instances": instances,
        'title': title,
    }

    return render(request, 'finance/account_groups.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def account_group(request, pk):
    instance = get_object_or_404(AccountGroup.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Account Group : " + instance.name,
    }

    return render(request, 'finance/account_group.html', context)


# End of Autocompletes
''' Bank Account '''
@check_mode
@login_required
@role_required(['superadmin'])
def create_bank_account(request):
    if request.method == "POST":
        response_data = {}
        form = BankAccountForm(request.POST)

        if form.is_valid():
            warehouse = form.cleaned_data['warehouse']
            bank_name = form.cleaned_data['bank_name']
            auto_id = get_auto_id(BankAccount)

            # create Bank Account
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.save()

            account_group = AccountGroup.objects.get(code='current_asset', is_deleted=False)

            head = AccountHead.objects.create(
                name = bank_name,
                code = 'bank_account',
                account_group = account_group,
                bank_account = data
            )

            if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()

                opening_balance = form.cleaned_data['opening_balance']
                opening_balance_type = form.cleaned_data['opening_balance_type']
                print(opening_balance_type)

                AccountHeadOpening.objects.create(
                    auto_id = get_auto_id(AccountHeadOpening),
                    creator = request.user,
                    updater = request.user,
                    warehouse = warehouse,
                    account_head = head,
                    financial_year = financial_year,
                    amount_type = opening_balance_type,
                    amount = opening_balance
                )

            response_data = {
                'status': 'true',
                'title': "Successfully Created",
                'redirect': 'true',
                'redirect_url': reverse('finance:bank_account', kwargs={'pk': data.pk}),
                'message': "Bank account Successfully Created.",
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
        form = BankAccountForm()

        context = {
            "form": form,
            "title": "Create Bank Account",

            "redirect": True,
        }
        return render(request, 'finance/bank/bank_account_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_bank_account(request, pk):
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk, is_deleted=False))

    if request.method == "POST":
        response_data = {}
        form = BankAccountForm(request.POST, instance=instance)

        if form.is_valid():
            bank_name = form.cleaned_data['bank_name']
            warehouse = form.cleaned_data['warehouse']

            # Update Bank Account
            data = form.save(commit=False)
            data.updater = request.user
            # data.balance = instance.balance + first_balance - old_first_balance
            data.date_updated = datetime.datetime.now()
            data.save()

            account_group = AccountGroup.objects.get(code='current_asset', is_deleted=False)

            AccountHead.objects.filter(bank_account=instance, account_group=account_group).update(
                name = bank_name,
                code = bank_name,
                account_group = account_group,
                bank_account = data
            )

            head = AccountHead.objects.filter(bank_account=instance, account_group=account_group).latest('id')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()
                opening_balance = form.cleaned_data['opening_balance']
                opening_balance_type = form.cleaned_data['opening_balance_type']

                if AccountHeadOpening.objects.filter(financial_year=financial_year, account_head=head, is_deleted=False).exists():
                    AccountHeadOpening.objects.filter(financial_year=financial_year, account_head=head, is_deleted=False).update(
                        account_head = head,
                        amount_type = opening_balance_type,
                        amount = opening_balance,
                        warehouse = warehouse,
                    )

                else:
                    AccountHeadOpening.objects.create(
                        auto_id = get_auto_id(AccountHeadOpening),
                        creator = request.user,
                        updater = request.user,
                        account_head = head,
                        financial_year = financial_year,
                        amount_type = opening_balance_type,
                        amount = opening_balance,
                        warehouse = warehouse,
                    )

            response_data = {
                'status': 'true',
                'title': "Successfully updated",
                'redirect': 'true',
                "redirect_url": reverse('finance:bank_accounts'),
                'message': "Bank account Successfully updated.",
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
        form = BankAccountForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Bank Account : ",
            "instance": instance,
        }

        return render(request, 'finance/bank/bank_account_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def bank_accounts(request):
    title = "Bank Accounts"
    instances = BankAccount.objects.filter(is_deleted=False)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(bank_name__icontains=query) | Q(account_number__icontains=query))

    context = {
        'title': title,
        "instances": instances,
    }
    return render(request, 'finance/bank/bank_accounts.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def bank_account(request, pk):
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk))
    head = AccountHead.objects.get(bank_account=instance, is_deleted=False)
    today = datetime.datetime.now().date()

    # bank_ledger = get_ledger_data(head, today, today, None, 'current balance')
    current_balance_type = 'Dr'
    current_balance = 0

    if current_balance < 0:
        current_balance_type = 'Cr'
        current_balance *= -1

    context = {
        "instance": instance,
        "title": "Bank Account : " + instance.bank_name,
        "single_page": True,
        "current_balance" : current_balance,
        "current_balance_type" : current_balance_type,

    }

    return render(request, 'finance/bank/bank_account.html', context)


@check_mode
@ajax_required
@login_required
@role_required(['superadmin'])
def delete_bank_account(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(BankAccount.objects.filter(pk=pk))

    BankAccount.objects.filter(pk=pk).update(is_deleted=True, bank_name=instance.bank_name + "_deleted" + str(instance.auto_id),deleted_reason=reason)
    AccountHead.objects.filter(bank_account=instance).update(is_deleted=True, name=instance.bank_name + "_deleted" + str(instance.id),deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Bank Account Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('finance:bank_accounts')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


# End of Account Group
''' Account Account Head '''
@check_mode
@login_required
@role_required(['superadmin'])
def create_account_head(request):
    if request.method == 'POST':
        form = AccountHeadForm(request.POST)

        if form.is_valid():
            data = form.save(commit=False)
            data.save()

            financial_years = FinancialYear.objects.filter(is_deleted=False, is_active=True)
            if financial_years.exists():
                financial_year = financial_years.last()

                warehouse = form.cleaned_data['warehouse']
                opening_balance = form.cleaned_data['opening_balance']
                opening_balance_type = form.cleaned_data['opening_balance_type']

                AccountHeadOpening.objects.create(
                    auto_id = get_auto_id(AccountHeadOpening),
                    creator = request.user,
                    updater = request.user,
                    warehouse = warehouse,
                    account_head = data,
                    financial_year = financial_year,
                    amount_type = opening_balance_type,
                    amount = opening_balance
                )

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Account Head created successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:account_heads')
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
        form = AccountHeadForm()

        context = {
            "title": "Create Account Head",
            "form": form,
            "url": reverse('finance:create_account_head'),
            "redirect": True,

        }

        return render(request, 'finance/account_head_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_account_head(request, pk):
    instance = get_object_or_404(AccountHead, pk=pk)
    if request.method == 'POST':
        if instance.code:
            form = AccountHeadEditForm(request.POST, instance=instance)
        else:
            form = AccountHeadForm(request.POST, instance=instance)

        if form.is_valid():
            if not instance.code:
                form.save()
            else:
                opening_balance = form.cleaned_data['opening_balance']
                opening_balance_type = form.cleaned_data['opening_balance_type']
                # AccountHead.objects.filter(pk=pk).update(opening_balance=opening_balance, opening_balance_type=opening_balance_type)

            instance = get_object_or_404(AccountHead, pk=pk)
            instance.date_updated = datetime.datetime.now()
            instance.updater = request.user
            instance.save()

            if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()

                warehouse = form.cleaned_data['warehouse']
                opening_balance = form.cleaned_data['opening_balance']
                opening_balance_type = form.cleaned_data['opening_balance_type']

                if AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).exists():
                    head_opening = AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).update(
                        account_head = instance,
                        amount_type = opening_balance_type,
                        amount = opening_balance
                    )
                else:
                    AccountHeadOpening.objects.create(
                        auto_id = get_auto_id(AccountHeadOpening),
                        creator = request.user,
                        updater = request.user,
                        warehouse = warehouse,
                        account_head = instance,
                        financial_year = financial_year,
                        amount_type = opening_balance_type,
                        amount = opening_balance
                    )

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Account Head updated successfully.",
                "redirect": "true",
                "redirect_url": reverse('finance:account_head', kwargs={'pk': pk})
                # "redirect_url": reverse('finance:account_heads')
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
        warehouse = get_warehouse(request)
        initial = {
            "warehouse": warehouse
        }

        if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
            financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()
            if AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).exists():
                head_opening = AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).last()

                initial['opening_balance'] = head_opening.amount
                initial['opening_balance_type'] = head_opening.amount_type

        form = AccountHeadForm(instance=instance, initial=initial)

        if instance.code != None:
            initial['account_group'] = instance.account_group.name
            form = AccountHeadEditForm(instance=instance, initial=initial)

            for field in ['name', 'account_group']:
                form.fields[field].widget.attrs['readonly'] = 'readonly'

        context = {
            "title": "Edit Account Head",
            "instance": instance,
            "warehouse": warehouse,
            "form": form,
            "url": reverse('finance:edit_account_head', kwargs={'pk': pk}),
            "is_edit": True,
            "redirect": True,
        }

        return render(request, 'finance/account_head_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_account_head(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(AccountHead, pk=pk, is_deleted=False)

    if not instance.code:
        AccountHead.objects.filter(pk=pk).update(name=instance.name + "_deleted_" + str(instance.id), is_deleted=True,deleted_reason=reason)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "AccountHead Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('finance:account_heads')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Deletion Failed",
            "message": "You cannot delete default heads.",

        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@role_required(['superadmin'])
def account_heads(request):
    instances = AccountHead.objects.filter(account_group__is_deleted=False, is_deleted=False)

    title = "Account Heads"
    query = request.GET.get("q")
    if instances:
        if query:
            instances = instances.filter(Q(name__icontains=query) | Q(types__icontains=query))
        title = "Account Heads"

    context = {
        "instances": instances,
        'title': title,

    }

    return render(request, 'finance/account_heads.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def account_head(request, pk):
    instance = get_object_or_404(AccountHead.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Account Head : " + instance.name,
    }

    return render(request, 'finance/account_head.html', context)


# End of Account Head
''' Account Payment voucher '''
@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def create_payment_voucher(request):
    if PaymentVoucher.objects.all().exists():
        number = PaymentVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
        voucher_number = int(number) + 1
    else:
        voucher_number = 1

    # manual_voucher_number = 0
    # if PaymentVoucher.objects.filter(is_system_generated=False).exists():
    #     manual_voucher_number = PaymentVoucher.objects.filter(is_system_generated=False).aggregate(manual_voucher_number=Max('manual_voucher_number')).get('manual_voucher_number')
    # manual_voucher_number += 1

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['transfer_date','voucher_date', 'cheque_date', 'draft_date', 'transaction_date'])
        form = PaymentVoucherForm(ModifiedRequest)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date)
                account_head = form.cleaned_data['account_head']
                bank = form.cleaned_data['bank']
                amount = form.cleaned_data['amount']
                # sub_ledger = form.cleaned_data['sub_ledger']
                transfer_type = form.cleaned_data['transfer_type']
                # has_transferred = form.cleaned_data['has_transferred']
                today = datetime.datetime.now().date()
                balance_ok = True
                sub_ledger_ok = True

                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                if amount <= 0:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Please enter amount greater than 0."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                if transfer_type == PAYMENTVOUCHER_TRANSFER_TYPES.cash:
                    head = AccountHead.objects.get(name='Cash A/C')
                    # ledger_data = get_ledger_data(head, today, today, None, 'current balance')
                    current_balance = 0

                    if current_balance < amount:
                        balance_ok = False
                    balance_ok = True

                if account_head.name in ['Sundry Debtor', 'Sundry Creditor (Vendor)', 'Sundry Creditor (Delivery Agent)']:
                    customer = form.cleaned_data['customer']
                    vendor = form.cleaned_data['vendor']
                    supplier = form.cleaned_data['supplier']
                    delivery_agent = form.cleaned_data['delivery_agent']
                    sub_ledger = None
                    if customer:
                        sub_ledger = customer
                    elif vendor:
                        sub_ledger = vendor
                    elif supplier:
                        sub_ledger = supplier
                    elif delivery_agent:
                        sub_ledger = delivery_agent
                    if not sub_ledger:
                        sub_ledger_ok = False

                if sub_ledger_ok and balance_ok:
                    status = PAYMENTVOUCHER_CHEQUE_STATUS.pending
                    # if has_transferred:
                    #     status = PAYMENTVOUCHER_CHEQUE_STATUS.cleared

                    voucher_date = datetime.datetime.combine(voucher_date, datetime.datetime.now().time())

                    data = form.save(commit=False)
                    data.creator = request.user
                    data.updater = request.user
                    data.financial_year = financial_year
                    data.auto_id = get_auto_id(PaymentVoucher)

                    data.voucher_number = voucher_number
                    data.voucher_date = voucher_date
                    # data.manual_voucher_number = manual_voucher_number
                    data.account_head = account_head
                    data.cheque_status = status
                    data.save()

                    # if AccountHead.objects.filter(pk=account_head.pk).exists():
                    #     bal = AccountHead.objects.get(pk=account_head.pk).current_balance
                    #     AccountHead.objects.filter(pk=account_head.pk).update(current_balance=bal - amount)

                    # subtracting amount from cash/bank AccountHead
                    # if transfer_type == PAYMENTVOUCHER_TRANSFER_TYPES.cash:
                    #     current = AccountHead.objects.get(name='Cash A/C', is_system_generated=True).current_balance
                    #     AccountHead.objects.filter(name='Cash A/C', is_system_generated=True).update(current_balance=current - amount)

                    # else:
                    #     if AccountHead.objects.filter(bank__pk=bank.pk).exists():
                    #         current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
                    #         AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current - amount)


                    # update debit/credit of sub-ledgers (vendor/customer)
                    if account_head.name == 'Sundry Creditor (Vendor)':
                        if Vendor.objects.filter(pk=sub_ledger.pk).exists():
                            vendor = Vendor.objects.get(pk=sub_ledger.pk)
                            update_vendor_credit_debit(vendor.pk, 'debit', amount)  # debit since amount is transferred to vendor

                    elif account_head.name == "Sundry Debtor":
                        if Customer.objects.filter(pk=sub_ledger.pk).exists():
                            customer = Customer.objects.get(pk=sub_ledger.pk)
                            update_customer_credit_debit(sub_ledger, 'debit', amount)  # debit since amount is transferred to customer

                    response_data = {
                        "status": "true",
                        "title": "Successfully Created",
                        "message": "Payment Voucher created successfully.",
                        "redirect": "true",
                        "redirect_url": reverse('finance:payment_vouchers')
                    }
                else:
                    if not sub_ledger_ok:
                        error_message = "Please choose a sub-ledger before submitting"
                    elif not balance_ok:
                        error_message = "Cash A/C doesn't have enough balance."
                    else:
                        error_message = "Please choose an account (not Credit)"

                    response_data = {
                        "status": "false",
                        "stable": 'true',
                        "title": "Transaction Failed",
                        "message": error_message,
                    }
            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
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
        date = datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')

        initial_cash = AccountHead.objects.filter(account_group__name='Cash in Hand').first()
        form = PaymentVoucherForm(initial={'voucher_number':voucher_number,'voucher_date': date, 'transfer_type': 10})

        context = {
            "form": form,
            "title": "Create Payment Voucher",
            "url": reverse('finance:create_payment_voucher'),
            "redirect": True,


        }

        return render(request, 'finance/payment/entry_payment_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_payment_voucher(request, pk):
    instance = get_object_or_404(PaymentVoucher.objects.filter(pk=pk, is_deleted=False))

    old_amount = instance.amount
    old_sub_ledger = instance.sub_ledger
    old_account_head = instance.account_head

    old_bank = instance.bank
    old_transfer_type = instance.transfer_type

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transfer_date'])
        form = PaymentVoucherForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']
            transfer_type = form.cleaned_data['transfer_type']
            amount = form.cleaned_data['amount']

            if amount <= 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please enter amount greater than 0."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if transfer_type in [15, 20, 25]:
                bank = form.cleaned_data['bank']
                if not bank:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Please choose a bank account before submitting."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                # retruning old amount to cash/bank AccountHead
                # if old_transfer_type == PAYMENTVOUCHER_TRANSFER_TYPES.cash:
                #     current = AccountHead.objects.get(name='Cash A/C').current_balance
                #     AccountHead.objects.filter(name='Cash A/C').update(current_balance=current + old_amount)

                # else:
                #     if AccountHead.objects.filter(bank__pk=old_bank.pk).exists():
                #         current = AccountHead.objects.get(bank__pk=old_bank.pk).current_balance
                #         AccountHead.objects.filter(bank__pk=old_bank.pk).update(current_balance=current + old_amount)

                # update debit/credit of sub-ledgers (vendor/customer) back to thier credit/debit
                if old_account_head.name == 'Sundry Creditor (Vendor)':
                    if Vendor.objects.filter(pk=old_sub_ledger).exists():
                        vendor = Vendor.objects.get(pk=old_sub_ledger)
                        update_vendor_credit_debit(vendor.pk, 'credit', old_amount)  # credit since amount was transferred to vendor

                elif old_account_head.name == "Sundry Debtor":
                    if Customer.objects.filter(pk=old_sub_ledger).exists():
                        customer = Customer.objects.get(pk=old_sub_ledger)
                        update_customer_credit_debit(old_sub_ledger, 'credit', old_amount)  # credit since amount was transferred to customer

                # saving current updations
                bank = form.cleaned_data['bank']
                amount = form.cleaned_data['amount']
                sub_ledger = form.cleaned_data['sub_ledger']
                account_head = form.cleaned_data['account_head']
                # has_transferred = form.cleaned_data['has_transferred']
                voucher_date = datetime.datetime.combine(voucher_date, datetime.datetime.now().time())

                data = form.save(commit=False)
                data.voucher_date = voucher_date
                data.is_updated = True
                data.updater = request.user
                data.date_updated = datetime.datetime.now()
                data.save()

                # subtracting amount from cash/bank AccountHead
                # if transfer_type == PAYMENTVOUCHER_TRANSFER_TYPES.cash:
                #     current = AccountHead.objects.get(name='Cash A/C').current_balance
                #     AccountHead.objects.filter(name='Cash A/C').update(current_balance=current - amount)

                # else:
                #     if AccountHead.objects.filter(bank__pk=bank.pk).exists():
                #         current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
                #         AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current - amount)

                    # if has_transferred:
                    #     balance = BankAccount.objects.filter(is_deleted=False, pk=bank.pk).last().balance
                    #     BankAccount.objects.filter(is_deleted=False, pk=bank.pk).update(balance=balance - amount)

            # update debit/credit of sub-ledgers (vendor/customer)
                if account_head.name == 'Sundry Creditor (Vendor)':
                    if Vendor.objects.filter(pk=sub_ledger).exists():
                        vendor = Vendor.objects.get(pk=sub_ledger)
                        update_vendor_credit_debit(vendor.pk, 'debit', amount)  # debit since amount is transferred to vendor

                elif account_head.name == "Sundry Debtor":
                    if Customer.objects.filter(pk=sub_ledger).exists():
                        customer = Customer.objects.get(pk=sub_ledger)
                        update_customer_credit_debit(sub_ledger, 'debit', amount)  # debit since amount is transferred to customer

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Payment Voucher Successfully Updated.",
                    "redirect": "true",
                    "redirect_url": reverse('finance:payment_vouchers')
                    # "redirect_url": reverse('finance:payment_voucher', kwargs={'pk': data.pk})
                }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
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
        initial = {
            'voucher_date': datetime.datetime.strftime(instance.voucher_date, '%d/%m/%Y')
        }
        if instance.transfer_date:
            initial['transfer_date'] = datetime.datetime.strftime(instance.transfer_date, '%d/%m/%Y')
        elif instance.draft_date:
            initial['draft_date'] = datetime.datetime.strftime(instance.draft_date, '%d/%m/%Y')
        elif instance.cheque_date:
            initial['cheque_date'] = datetime.datetime.strftime(instance.cheque_date, '%d/%m/%Y')

        if instance.sub_ledger:
            if instance.account_head.name == 'Sundry Debtor':
                initial['customer'] = instance.sub_ledger
            elif instance.account_head.name == 'Sundry Creditor (Vendor)':
                initial['vendor'] = instance.sub_ledger
            elif instance.account_head.name == 'Sundry Creditor (Delivery Agent)':
                initial['delivery_agent'] = instance.sub_ledger

        form = PaymentVoucherForm(instance=instance, initial=initial)

        context = {
            "form": form,
            "title": "Edit Payment Voucher : ",
            "instance": instance,
            "url": reverse('finance:edit_payment_voucher', kwargs={'pk': instance.pk}),
            "redirect": True,
            "is_edit": True,
        }
        return render(request, 'finance/payment/entry_payment_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def payment_vouchers(request):
    filter_data ={}
    title = "Payment Vouchers"

    instances = PaymentVoucher.objects.filter().order_by('-voucher_number')

    query = request.GET.get("q")
    voucher_date = request.GET.get("voucher_date")
    voucher_type = request.GET.get("voucher_type")
    voucher_number = request.GET.get("voucher_number")
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    view_option = request.GET.get('view')

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if instances.exists():
        if query:
            sub_ledger_pks = []
            if Customer.objects.filter(Q(name__icontains=query) | Q(address__icontains=query), is_deleted=False).exists():
                customer_pks = list(Customer.objects.filter(Q(name__icontains=query) | Q(address__icontains=query), is_deleted=False).values_list('pk', flat=True))
                customer_pks = map(str, customer_pks)
                sub_ledger_pks += customer_pks
            if Vendor.objects.filter(name__icontains=query, is_deleted=False).exists():
                vendor_pks = list(Vendor.objects.filter(name__icontains=query, is_deleted=False).values_list('pk', flat=True))
                vendor_pks = map(str, vendor_pks)
                sub_ledger_pks += vendor_pks

            instances = instances.filter(
                Q(title__icontains=query) |
                Q(account_head__name__icontains=query) |
                Q(amount__icontains=query) |
                Q(sub_ledger__in=sub_ledger_pks)
            )
            filter_data['query'] = query

        if voucher_type == 'manual':
            instances = instances.filter(is_system_generated=False)
        elif voucher_type == 'is_system_generated':
            instances = instances.filter(is_system_generated=True)
        else:
            voucher_type = 'all'

        title = "Payment / Expense Vouchers"
        filter_data['voucher_type'] = voucher_type

        if from_date and to_date:
            f_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            t_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date__date__range=[f_date, t_date])

            filter_data['from_date'] = from_date
            filter_data['to_date'] = to_date

        if voucher_date:
            vo_date = datetime.datetime.strptime(voucher_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date__date=vo_date)
            filter_data['voucher_date'] = voucher_date

        if voucher_number:
            instances = instances.filter(voucher_number=voucher_number)
            filter_data['voucher_number'] = voucher_number

    if view_option == 'cancelled':
        total_amount = instances.aggregate(Sum('amount'))['amount__sum']
    else:
        total_amount = instances.filter(is_deleted=False).aggregate(Sum('amount'))['amount__sum']

    context = {
        "instances": instances,
        "total_amount": total_amount,
        "filter_data": filter_data,
        'title': title,
    }

    return render(request, 'finance/payment/payment_vouchers.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def payment_voucher(request, pk):
    instance = get_object_or_404(PaymentVoucher.objects.filter(pk=pk))

    context = {
        "instance": instance,
        "title": "Payment Voucher : " + str(instance.voucher_number),


    }

    return render(request, 'finance/payment/payment_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_payment_voucher(request, pk):
    instance = get_object_or_404(PaymentVoucher.objects.filter(pk=pk))

    if not instance.is_system_generated:
        instance.is_deleted = True
        instance.save()

        amount = instance.amount
        sub_ledger = instance.sub_ledger
        account_head = instance.account_head

        # retruning old amount to cash/bank AccountHead
        # if instance.transfer_type == PAYMENTVOUCHER_TRANSFER_TYPES.cash:
        #     current = AccountHead.objects.get(name='Cash A/C', is_system_generated=True).current_balance
        #     AccountHead.objects.filter(name='Cash A/C', is_system_generated=True).update(current_balance=current + amount)
        # else:
        #     bank = instance.bank
        #     if bank:
        #         if AccountHead.objects.filter(bank__pk=bank.pk).exists():
        #             current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
        #             AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current + amount)

        #         if instance.has_transferred:
        #             balance = BankAccount.objects.filter(is_deleted=False, pk=bank.pk).last().balance
        #             BankAccount.objects.filter(is_deleted=False, pk=bank.pk).update(balance=balance + amount)

        # update debit/credit of sub-ledgers (vendor/customer) back to thier credit/debit
        if account_head.name == 'Sundry Creditor (Vendor)':
            if Vendor.objects.filter(pk=sub_ledger).exists():
                vendor = Vendor.objects.get(pk=sub_ledger)
                update_vendor_credit_debit(vendor.pk, "credit", amount)  # credit since amount was transferred to vendor

        elif account_head.name == "Sundry Debtor":
            if Customer.objects.filter(pk=sub_ledger).exists():
                customer = Customer.objects.get(pk=sub_ledger)
                update_customer_credit_debit(sub_ledger, "credit", amount)  # credit since amount was transferred to customer

        response_data = {
            "status": "true",
            "title": "Successfully Cancelled",
            "message": "Payment Voucher Successfully Cancelled.",
            "redirect": "true",
            "redirect_url": reverse('finance:payment_vouchers')
        }

    else:
        response_data = {
            "status": "false",
            "title": "Cancellation Failed",
            "message": "You cannot Cancel system generated vouchers.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def print_payment_voucher(request, pk):
    instance = get_object_or_404(PaymentVoucher.objects.filter(pk=pk))

    context = {
        "instance": instance,
        "title": "Payment Voucher : " + str(instance.voucher_number),
    }

    return render(request, 'finance/payment/print_payment.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def cancelled_payment_vouchers(request):
    instances = None
    filter_data ={}

    if PaymentVoucher.objects.filter(is_deleted=True).exists():
        instances = PaymentVoucher.objects.filter(is_deleted=True).order_by('-voucher_number')

    title = "Cancelled Payment Vouchers"
    query = request.GET.get("q")
    voucher_date = request.GET.get("voucher_date")
    voucher_number = request.GET.get("voucher_number")

    if instances:
        if query:
            instances = instances.filter(Q(title__icontains=query))

        if voucher_date:
            vo_date = datetime.datetime.strptime(voucher_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date=vo_date)
            filter_data['voucher_date'] = voucher_date

        if voucher_number:
            instances = instances.filter(voucher_number=voucher_number)
            filter_data['voucher_number'] = voucher_number

    context = {
        'title': title,
        "instances": instances,
        "filter_data" : filter_data,

    }

    return render(request, 'finance/payment/payment_vouchers.html', context)


# End of Payment voucher

''' Receipt voucher '''
@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def create_receipt_voucher(request):
    if ReceiptVoucher.objects.all().exists():
        number = ReceiptVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
        voucher_number = int(number) + 1
    else:
        voucher_number = 1

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transfer_date'])
        form = ReceiptVoucherForm(ModifiedRequest)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date)
                account_head = form.cleaned_data['account_head']
                bank = form.cleaned_data['bank']
                amount = form.cleaned_data['amount']
                sub_ledger = form.cleaned_data['sub_ledger']
                transfer_type = form.cleaned_data['transfer_type']
                transfer_date = form.cleaned_data['transfer_date']
                sub_ledger_ok = True

                if amount <= 0:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Please enter amount greater than 0."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                status = RECEIPTVOUCHER_CHEQUE_STATUS.pending

                if account_head.name in ['Sundry Debtor', 'Sundry Creditor (Vendor)', 'Sundry Creditor (Delivery Agent)']:
                    if not sub_ledger:
                        sub_ledger_ok = False

                if sub_ledger_ok:
                    voucher_date = datetime.datetime.combine(voucher_date, datetime.datetime.now().time())

                    data = form.save(commit=False)
                    data.creator = request.user
                    data.updater = request.user
                    data.financial_year = financial_year
                    data.auto_id = get_auto_id(ReceiptVoucher)

                    data.voucher_number = voucher_number
                    data.voucher_date = voucher_date
                    data.account_head = account_head
                    data.cheque_status = status
                    data.save()

                    # if AccountHead.objects.filter(pk=account_head.pk).exists():
                    #     bal = AccountHead.objects.get(pk=account_head.pk).current_balance
                    #     AccountHead.objects.filter(pk=account_head.pk).update(current_balance=bal + amount)

                    # subtracting amount from cash/bank AccountHead
                    # if transfer_type == RECEIPTVOUCHER_TRANSFER_TYPES.cash:

                    #     current = AccountHead.objects.get(name='Cash A/C', system_generated=True).current_balance
                    #     AccountHead.objects.filter(name='Cash A/C', system_generated=True).update(current_balance=current + amount)

                    # else:
                    #     if AccountHead.objects.filter(bank__pk=bank.pk).exists():
                    #         current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
                    #         AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current + amount)


                    # update credit/debit of sub-ledgers (vendor/customer)
                    if account_head.name == 'Sundry Creditor (Vendor)':
                        if Vendor.objects.filter(pk=sub_ledger).exists():
                            vendor = Vendor.objects.get(pk=sub_ledger)
                            update_vendor_credit_debit(vendor.pk, "credit", amount)  # credit since amount is received from vendor

                    elif account_head.name == "Sundry Debtor":
                        if Customer.objects.filter(pk=sub_ledger).exists():
                            customer = Customer.objects.get(pk=sub_ledger)
                            update_customer_credit_debit(sub_ledger, "credit", amount)  # credit since amount is received from customer

                    response_data = {
                        "status": "true",
                        "title": "Successfully Created",
                        "message": "Receipt  Voucher created successfully.",
                        "redirect": "true",
                        "redirect_url": reverse('finance:receipt_vouchers')
                    }

                else:
                    if sub_ledger_ok:
                        error_message = "Please choose an account Before submitting (not Credit)"
                    else:
                        error_message = "Please choose a sub-ledger before submitting"

                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": error_message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
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
        date = datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')

        initial_cash = AccountHead.objects.filter(account_group__name='Cash in Hand').first()
        form = ReceiptVoucherForm(initial={'voucher_number': voucher_number, 'voucher_date': date, 'transfer_type': 10})

        context = {
            "form": form,
            "title": "Create Receipt Voucher",
            "url": reverse('finance:create_receipt_voucher'),
            "redirect": True,
        }

        return render(request, 'finance/receipt/entry_receipt_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_receipt_voucher(request, pk):
    instance = get_object_or_404(ReceiptVoucher.objects.filter(pk=pk, is_deleted=False))

    old_amount = instance.amount
    old_sub_ledger = instance.sub_ledger
    old_account_head = instance.account_head

    old_bank = instance.bank
    old_transfer_type = instance.transfer_type

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transfer_date'])
        form = ReceiptVoucherForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            transfer_type = form.cleaned_data['transfer_type']
            voucher_date = form.cleaned_data['voucher_date']
            amount = form.cleaned_data['amount']

            if amount <= 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please enter amount greater than 0."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if transfer_type in [15, 20, 25]:
                bank = form.cleaned_data['bank']
                if not bank:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Please choose a bank account before submitting."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                # retruning old amount to cash/bank AccountHead
                # if old_transfer_type == RECEIPTVOUCHER_TRANSFER_TYPES.cash:
                #     current = AccountHead.objects.get(name='Cash A/C', system_generated=True).current_balance
                #     AccountHead.objects.filter(name='Cash A/C', system_generated=True).update(current_balance=current - old_amount)

                # else:
                #     if AccountHead.objects.filter(bank__pk=old_bank.pk).exists():
                #         current = AccountHead.objects.get(bank__pk=old_bank.pk).current_balance
                #         AccountHead.objects.filter(bank__pk=old_bank.pk).update(current_balance=current - old_amount)

                    # if old_has_transferred:
                    #     balance = BankAccount.objects.filter(is_deleted=False, pk=old_bank.pk).last().balance
                    #     BankAccount.objects.filter(is_deleted=False, pk=old_bank.pk).update(balance=balance - old_amount)

                # update credit/debit of sub-ledgers (vendor/customer) back to thier debit/credit
                if old_account_head.name == 'Sundry Creditor (Vendor)':
                    if Vendor.objects.filter(pk=old_sub_ledger).exists():
                        vendor = Vendor.objects.get(pk=old_sub_ledger)
                        update_vendor_credit_debit(vendor.pk, 'debit', old_amount)  # debit since amount was received from vendor

                elif old_account_head.name == "Sundry Debtor":
                    if Customer.objects.filter(pk=old_sub_ledger).exists():
                        customer = Customer.objects.get(pk=old_sub_ledger)
                        update_customer_credit_debit(old_sub_ledger, 'debit', old_amount)  # debit since amount was received from customer

                # saving current updations
                bank = form.cleaned_data['bank']
                amount = form.cleaned_data['amount']
                sub_ledger = form.cleaned_data['sub_ledger']
                account_head = form.cleaned_data['account_head']
                # has_transferred = form.cleaned_data['has_transferred']
                voucher_date = datetime.datetime.combine(voucher_date, datetime.datetime.now().time())

                data = form.save(commit=False)
                data.is_updated = True
                data.updater = request.user
                data.date_updated = datetime.datetime.now()

                data.voucher_date = voucher_date
                data.save()

                # subtracting amount from cash/bank AccountHead
                # if transfer_type == RECEIPTVOUCHER_TRANSFER_TYPES.cash:
                #     current = AccountHead.objects.get(name='Cash A/C', system_generated=True).current_balance
                #     AccountHead.objects.filter(name='Cash A/C', system_generated=True).update(current_balance=current + amount)

                # else:
                #     if AccountHead.objects.filter(bank__pk=bank.pk).exists():
                #         current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
                #         AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current + amount)

            # update credit/debit of sub-ledgers (vendor/customer)
                if account_head.name == 'Sundry Creditor (Vendor)':
                    if Vendor.objects.filter(pk=sub_ledger).exists():
                        vendor = Vendor.objects.get(pk=sub_ledger)
                        update_vendor_credit_debit(vendor.pk, "credit", amount)  # credit since amount is received from vendor

                elif account_head.name == "Sundry Debtor":
                    if Customer.objects.filter(pk=sub_ledger).exists():
                        customer = Customer.objects.get(pk=sub_ledger)
                        update_customer_credit_debit(sub_ledger, "credit", amount)  # credit since amount is received from customer

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Receipt  Voucher Successfully Updated.",
                    "redirect": "true",
                    # "redirect_url": reverse('finance:receipt_voucher', kwargs={'pk': data.pk})
                    "redirect_url": reverse('finance:receipt_vouchers')
                }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
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
        initial = {
            'voucher_date': datetime.datetime.strftime(instance.voucher_date, '%d/%m/%Y')
        }
        if instance.transfer_date:
            initial['transfer_date'] = datetime.datetime.strftime(instance.transfer_date, '%d/%m/%Y')
        elif instance.draft_date:
            initial['draft_date'] = datetime.datetime.strftime(instance.draft_date, '%d/%m/%Y')
        elif instance.cheque_date:
            initial['cheque_date'] = datetime.datetime.strftime(instance.cheque_date, '%d/%m/%Y')

        if instance.sub_ledger:
            if instance.account_head.name == 'Sundry Debtor':
                initial['customer'] = instance.sub_ledger
            elif instance.account_head.name == 'Sundry Creditor (Vendor)':
                initial['vendor'] = instance.sub_ledger
            elif instance.account_head.name == 'Sundry Creditor (Delivery Agent)':
                initial['delivery_agent'] = instance.sub_ledger

        form = ReceiptVoucherForm(instance=instance, initial=initial)

        context = {
            "form": form,
            "title": "Edit Receipt  Voucher : ",
            "instance": instance,
            "url": reverse('finance:edit_receipt_voucher', kwargs={'pk': instance.pk}),
            "redirect": True,
            "is_edit": True,
        }
        return render(request, 'finance/receipt/entry_receipt_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def receipt_vouchers(request):
    filter_data = {}
    title = "Receipt Vouchers"

    instances = ReceiptVoucher.objects.filter().order_by('-voucher_number')

    query = request.GET.get("q")
    voucher_date = request.GET.get("voucher_date")
    voucher_number = request.GET.get("voucher_number")
    voucher_type = request.GET.get("voucher_type")
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    view_option = request.GET.get('view')

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if instances.exists():
        if query:
            sub_ledger_pks = []
            if Customer.objects.filter(Q(name__icontains=query) | Q(address__icontains=query), is_deleted=False).exists():
                customer_pks = list(Customer.objects.filter(Q(name__icontains=query) | Q(address__icontains=query), is_deleted=False).values_list('pk', flat=True))
                customer_pks = map(str, customer_pks)
                sub_ledger_pks += customer_pks
            if Vendor.objects.filter(name__icontains=query, is_deleted=False).exists():
                vendor_pks = list(Vendor.objects.filter(name__icontains=query, is_deleted=False).values_list('pk', flat=True))
                vendor_pks = map(str, vendor_pks)
                sub_ledger_pks += vendor_pks

            instances = instances.filter(
                Q(title__icontains=query) |
                Q(account_head__name__icontains=query) |
                Q(amount__icontains=query) |
                Q(sub_ledger__in=sub_ledger_pks)
            )
            filter_data['query'] = query

        title = "Receipt Vouchers"
        filter_data['voucher_type'] = voucher_type

        if voucher_type == 'all':
            pass
        # elif voucher_type == 'manual':
        #     instances = instances.filter(system_generated=False)
        elif voucher_type == 'is_system_generated':
            instances = instances.filter(is_system_generated=True)

        if voucher_date:
            vo_date = datetime.datetime.strptime(voucher_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date__date=vo_date)
            filter_data['voucher_date'] = voucher_date

        if from_date and to_date:
            f_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            t_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date__date__range=[f_date, t_date])

            filter_data['from_date'] = from_date
            filter_data['to_date'] = to_date

        if voucher_number:
            instances = instances.filter(voucher_number=voucher_number)
            filter_data['voucher_number'] = voucher_number

    if view_option == 'cancelled':
        total_amount = instances.aggregate(Sum('amount'))['amount__sum']
    else:
        total_amount = instances.filter(is_deleted=False).aggregate(Sum('amount'))['amount__sum']

    context = {
        'title': title,
        "instances": instances,
        "filter_data" : filter_data,
        "total_amount": total_amount,
    }

    return render(request, 'finance/receipt/receipt_vouchers.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def receipt_voucher(request, pk):
    instance = get_object_or_404(ReceiptVoucher.objects.filter(pk=pk))

    context = {
        "instance": instance,
        "title": "Receipt Voucher : " + str(instance.voucher_number),

    }

    return render(request, 'finance/receipt/receipt_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_receipt_voucher(request, pk):
    instance = get_object_or_404(ReceiptVoucher.objects.filter(pk=pk))
    instance.is_deleted = True
    instance.save()

    amount = instance.amount
    sub_ledger = instance.sub_ledger
    account_head = instance.account_head

    # retruning old amount to cash/bank AccountHead
    # if instance.transfer_type == RECEIPTVOUCHER_TRANSFER_TYPES.cash:
    #     current = AccountHead.objects.get(name='Cash A/C', system_generated=True).current_balance
    #     AccountHead.objects.filter(name='Cash A/C', system_generated=True).update(current_balance=current + amount)
    # else:
    #     bank = instance.bank
    #     if bank:
    #         if AccountHead.objects.filter(bank__pk=bank.pk).exists():
    #             current = AccountHead.objects.get(bank__pk=bank.pk).current_balance
    #             AccountHead.objects.filter(bank__pk=bank.pk).update(current_balance=current + amount)

    #         if instance.has_transferred:
    #             balance = BankAccount.objects.filter(is_deleted=False, pk=bank.pk).last().balance
    #             BankAccount.objects.filter(is_deleted=False, pk=bank.pk).update(balance=balance + amount)

    # update credit/debit of sub-ledgers (vendor/customer) back to thier debit/credit
    if account_head.name == 'Sundry Creditor (Vendor)':
        if Vendor.objects.filter(pk=sub_ledger).exists():
            vendor = Vendor.objects.get(pk=sub_ledger)
            update_vendor_credit_debit(vendor.pk, 'debit', amount)  # debit since amount was received from vendor

    elif account_head.name == "Sundry Debtor":
        if Customer.objects.filter(pk=sub_ledger).exists():
            customer = Customer.objects.get(pk=sub_ledger)
            update_customer_credit_debit(sub_ledger, 'debit', amount)  # debit since amount was received from customer

    response_data = {
        "status": "true",
        "title": "Successfully Cancelled",
        "message": "Payment Voucher Successfully Cancelled.",
        "redirect": "true",
        "redirect_url": reverse('finance:receipt_vouchers')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def print_receipt_voucher(request, pk):
    instance = get_object_or_404(ReceiptVoucher.objects.filter(pk=pk))

    context = {
        "instance": instance,
        "title": "Receipt Voucher : " + str(instance.voucher_number),
    }

    return render(request, 'finance/receipt/print_receipt.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def cancelled_receipt_vouchers(request):
    instances = None
    filter_data = {}

    if ReceiptVoucher.objects.filter(is_deleted=True).exists():
        instances = ReceiptVoucher.objects.filter(is_deleted=True).order_by('-voucher_number')

    title = "Cancelled Receipt Vouchers"
    query = request.GET.get("q")
    voucher_date = request.GET.get("voucher_date")
    voucher_number = request.GET.get("voucher_number")

    if instances:
        if query:
            instances = instances.filter(Q(title__icontains=query))

        if voucher_date:
            vo_date = datetime.datetime.strptime(voucher_date, '%d/%m/%Y').date()
            instances = instances.filter(voucher_date=vo_date)
            filter_data['voucher_date'] = voucher_date

        if voucher_number:
            instances = instances.filter(voucher_number=voucher_number)
            filter_data['voucher_number'] = voucher_number

    context = {
        'title': title,
        "instances": instances,
        "filter_data" : filter_data,

    }

    return render(request, 'finance/receipt/receipt_vouchers.html', context)


''' Journal Voucher '''
@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def create_journal_voucher(request):
    if JournalVoucher.objects.exists():
        number = JournalVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
        voucher_no = number + 1
    else:
        voucher_no = 1

    JournalVoucherItemFormSet = formset_factory(JournalVoucherItemForm, extra=1)
    today = datetime.datetime.today().date()

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date'])
        form = JournalVoucherForm(ModifiedRequest)
        journal_voucher_item_formset = JournalVoucherItemFormSet(request.POST, prefix='journal_voucher_item_formset')

        if form.is_valid() and journal_voucher_item_formset.is_valid():
            voucher_date = form.cleaned_data['voucher_date']
            sub_ledger_ok = True

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date)
                debit_total = 0
                credit_total = 0
                balance_ok = True
                error_message = ''

                for f in journal_voucher_item_formset:
                    amount = f.cleaned_data['amount']
                    sub_ledger = f.cleaned_data['sub_ledger']
                    amount_type = f.cleaned_data['amount_type']
                    account_head = f.cleaned_data['account_head']

                    if amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
                        credit_total += amount

                        # if account_head.account_group.name == 'Cash in Hand' and account_head.system_generated:
                        #     ledger_data = get_ledger_data(account_head, today, today, None, 'current balance')
                        #     current_balance = ledger_data['closing_balance']

                        #     if current_balance < amount:
                        #         balance_ok = False
                        #         error_message += f"{account_head.name} doesn't have enough balance"

                    elif amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
                        debit_total += amount

                    if account_head.name in ['Sundry Debtor', 'Sundry Creditor (Vendor)', 'Sundry Creditor (Delivery Agent)']:
                        if not sub_ledger:
                            sub_ledger_ok = False

                if sub_ledger_ok and credit_total == debit_total and debit_total != 0 and balance_ok:
                    voucher_date = datetime.datetime.combine(voucher_date, datetime.datetime.now().time())

                    data = form.save(commit=False)
                    data.financial_year = financial_year
                    data.auto_id = get_auto_id(JournalVoucher)
                    data.creator = request.user
                    data.updater = request.user

                    data.voucher_date = voucher_date
                    data.save()

                    for f in journal_voucher_item_formset:
                        amount = f.cleaned_data['amount']
                        amount_type = f.cleaned_data['amount_type']
                        account_head = f.cleaned_data['account_head']

                        item_data = f.save(commit=False)
                        item_data.journal = data
                        item_data.save()

                        # if amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
                        #     AccountHead.objects.filter(pk=account_head.pk).update(current_balance=F('current_balance') - amount)
                        # elif amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
                        #     AccountHead.objects.filter(pk=account_head.pk).update(current_balance=F('current_balance') + amount)

                    data.voucher_number = voucher_no
                    data.save()

                    response_data = {
                        "status": "true",
                        "title": "Successfully Created",
                        "message": "Journal Voucher created successfully.",
                        "redirect": "true",
                        "redirect_url": reverse('finance:journal_vouchers')
                    }
                else:
                    message = "credit total and debit total must be equal or not zero"
                    if not balance_ok:
                        message = error_message
                    if not sub_ledger_ok:
                        error_message = "Please choose a sub-ledger before submitting"

                    response_data = {
                        'status': 'false',
                        'stable': 'true',
                        'title': "Form validation error",
                        'message': message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = str(generate_form_errors(form, formset=False))
            message += str(generate_form_errors(journal_voucher_item_formset, formset=True))

            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        initial = {
            'voucher_number': voucher_no,
            'voucher_date': datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')
        }

        form = JournalVoucherForm(initial=initial)

        journal_voucher_item_formset = JournalVoucherItemFormSet(prefix='journal_voucher_item_formset')
        # journal_item_credit_formset = JournalItemCreditFormSet(prefix='journal_item_credit_formset')

        context = {
            "form": form,
            "title": "Journal Voucher",
            "caption": "Journal Voucher",
            "journal_voucher_item_formset": journal_voucher_item_formset,
            "url": reverse('finance:create_journal_voucher'),
            "redirect": True,
            "is_create_page": True,

        }
    return render(request, 'finance/journal/journal_voucher_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def journal_vouchers(request):
    instances = JournalVoucher.objects.all().order_by('-voucher_number', 'voucher_date')
    title = "Journal Vouchers"
    filter_data = {}

    query = request.GET.get("q")
    voucher_date = request.GET.get("voucher_date")
    voucher_number = request.GET.get("voucher_number")
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    view_option = request.GET.get('view')

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if query:

        instances = instances.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        filter_data['query'] = query

    title = "Receipt Vouchers"

    if voucher_date:
        vo_date = datetime.datetime.strptime(voucher_date, '%d/%m/%Y').date()
        instances = instances.filter(voucher_date__date=vo_date)
        filter_data['voucher_date'] = voucher_date

    if from_date and to_date:
        f_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        t_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(voucher_date__date__range=[f_date, t_date])

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if voucher_number:
        instances = instances.filter(voucher_number=voucher_number)
        filter_data['voucher_number'] = voucher_number

    context = {
        'instances': instances,
        "title": title,
        "filter_data": filter_data,
    }

    return render(request, 'finance/journal/journal_vouchers.html', context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def journal_voucher(request, pk):
    instance = get_object_or_404(JournalVoucher.objects.filter(pk=pk))
    entries = JournalVoucherItem.objects.filter(journal=instance, journal__is_deleted=False)

    context = {
        "instance": instance,
        "title": "Manual Journal View",
        "single_page": True,
        "entries": entries,

    }

    return render(request, 'finance/journal/journal_voucher.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_journal_voucher(request, pk):
    instance = get_object_or_404(JournalVoucher.objects.filter(pk=pk, is_deleted=False))
    old_journal_items = None

    if JournalVoucherItem.objects.filter(journal=instance).exists():
        old_journal_items = JournalVoucherItem.objects.filter(journal=instance)
        extra = 0
    else:
        extra = 1

    JournalItemFormset = inlineformset_factory(
        JournalVoucher,
        JournalVoucherItem,
        can_delete=True,
        extra=extra,
        form=JournalVoucherItemForm
    )

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date'])
        form = JournalVoucherForm(ModifiedRequest, instance=instance)
        journal_voucher_item_formset = JournalItemFormset(request.POST, instance=instance, prefix='journal_voucher_item_formset')

        if form.is_valid() and journal_voucher_item_formset.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                debit_total = 0
                credit_total = 0

                for f in journal_voucher_item_formset:
                    amount = f.cleaned_data['amount']
                    amount_type = f.cleaned_data['amount_type']
                    account_head = f.cleaned_data['account_head']

                    if amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
                        credit_total += amount
                    elif amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
                        debit_total += amount

                if credit_total == debit_total and debit_total != 0:
                    # save journal voucher
                    data = form.save(commit=False)
                    data.is_updated = True
                    data.updater = request.user
                    data.date_updated = datetime.datetime.now()

                    data.save()

                    # returning amount to corresponding account head
                    # for old_item in old_journal_items:
                    #     current_balance = AccountHead.objects.get(pk=old_item.account_head.pk).current_balance
                    #     balance = current_balance
                    #     old_amount = old_item.amount

                    #     if old_item.amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
                    #         balance = current_balance + old_amount
                    #     elif old_item.amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
                    #         balance = current_balance - old_amount

                    #     AccountHead.objects.filter(pk=old_item.account_head.pk).update(current_balance=balance)

                    # deleting old items
                    old_journal_items.delete()

                    # creating new journal items
                    for f in journal_voucher_item_formset:
                        amount = f.cleaned_data['amount']
                        amount_type = f.cleaned_data['amount_type']
                        account_head = f.cleaned_data['account_head']

                        item_data = f.save(commit=False)
                        item_data.journal = data
                        item_data.save()

                        # current_balance = AccountHead.objects.get(pk=account_head.pk).current_balance
                        # balance = current_balance

                        # if amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
                        #     balance = current_balance - amount
                        # elif amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
                        #     balance = current_balance + amount

                        # AccountHead.objects.filter(pk=account_head.pk).update(current_balance=balance)

                    response_data = {
                        "status": "true",
                        "redirect": "true",
                        "title": "Successfully Created",
                        "message": "Journal Voucher created successfully.",
                        "redirect_url": reverse('finance:journal_vouchers'),
                        # "redirect_url": reverse('finance:journal_voucher', kwargs={'pk': pk})
                    }
                else:

                    response_data = {
                        'status': 'false',
                        'stable': 'true',
                        'title': "Form validation error",
                        "message": "credit total and debit total must be equal or not zero"
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form, formset=False)
            print(form.errors)
            print(journal_voucher_item_formset.errors)
            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        initial = {
            'voucher_date': datetime.datetime.strftime(instance.voucher_date, '%d/%m/%Y')
        }
        form = JournalVoucherForm(instance=instance, initial=initial)
        journal_voucher_item_formset = JournalItemFormset(prefix='journal_voucher_item_formset', instance=instance)

        context = {
            "title": "Journal Voucher",
            "caption": "Journal Voucher",
            "journal_voucher_item_formset": journal_voucher_item_formset,
            "form": form,
            "redirect": True,
            "is_create_page": True,
        }
        return render(request, 'finance/journal/journal_voucher_entry.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_journal_voucher(request, pk):
    instance = get_object_or_404(JournalVoucher.objects.filter(pk=pk, is_deleted=False))
    old_journal_items = JournalVoucherItem.objects.filter(journal=instance)

    # returning amount to corresponding account head
    # for old_item in old_journal_items:
        # current_balance = AccountHead.objects.get(pk=old_item.account_head.pk).current_balance
        # balance = current_balance
        # old_amount = old_item.amount

        # if old_item.amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.credit:
        #     balance = current_balance + old_amount
        # elif old_item.amount_type == FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES.debit:
        #     balance = current_balance - old_amount

        # AccountHead.objects.filter(pk=old_item.account_head.pk).update(current_balance=balance)

    old_journal_items.update(is_deleted=True)
    instance.is_deleted = True
    instance.save()

    response_data = {
        'status': 'true',
        'stable': 'true',
        'title': "Deleted",
        "message": "Journal delete successfully",
        "redirect_url": reverse('finance:journal_vouchers'),

    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


# End of Journal voucher
# credit note vouchers Start
@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def create_credit_note_voucher(request):
    sale_return_group, created = AccountGroup.objects.get_or_create(name='Sale Returns', is_deleted=False)
    sale_return_head, created = AccountHead.objects.get_or_create(name='Sale Returns A/C', code="Sale Returns A/C", account_group=sale_return_group, is_deleted=False)
    purchase_return_group, created = AccountGroup.objects.get_or_create(name='Purchase Returns', is_deleted=False)
    purchase_return_head, created = AccountHead.objects.get_or_create(name='Purchase Returns A/C', code="Purchase Returns A/C", account_group=purchase_return_group, is_deleted=False)

    today = datetime.datetime.now()

    voucher_no = 0
    if CreditNoteVoucher.objects.all().exists():
        voucher_no = CreditNoteVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number', 0)
    voucher_number = voucher_no + 1

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transaction_date'])
        form = CreditNoteVoucherForm(ModifiedRequest)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                transfer_type = form.cleaned_data['transfer_type']
                sale_return = form.cleaned_data['sale_return']
                paid_amount = form.cleaned_data['amount']
                amount_ok = True
                balance_ok = True

                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                return_amount = sale_return.amount_returned

                # if transfer_type == CREDITNOTE_TRANSFER_TYPES.credit:
                #     pass

                # elif transfer_type == CREDITNOTE_TRANSFER_TYPES.cash:
                #     head = AccountHead.objects.get(name='Cash A/C', system_generated=True)
                #     ledger_data = get_ledger_data(head, today.date(), today.date(), None, 'current balance')
                #     current_balance = ledger_data['closing_balance']

                #     if current_balance < paid_amount:
                #         balance_ok = False

                if paid_amount > sale_return.amount_returned or paid_amount <= 0:
                    amount_ok = False

                # else:
                #     bank = form.cleaned_data['bank']
                #     head = AccountHead.objects.get(bank=bank, system_generated=True)
                #     ledger_data = get_ledger_data(head, today.date(), today.date(), None, 'current balance')
                #     current_balance = ledger_data['closing_balance']

                #     if current_balance < paid_amount:
                #         balance_ok = False

                if balance_ok and amount_ok:
                    data = form.save(commit=False)
                    data.auto_id = get_auto_id(CreditNoteVoucher)
                    data.warehouse = sale_return.warehouse
                    data.creator = request.user
                    data.updater = request.user

                    data.sub_ledger_name = str(sale_return)
                    data.save()

                    response_data = {
                        "status" : "true",
                        "title" : "Successfully Created",
                        "message" : "Credit Note Voucher created successfully.",
                        "redirect" : "true",
                        "redirect_url" : reverse('finance:credit_note_voucher',kwargs={'pk':data.pk})
                    }

                else:
                    if amount_ok == False:
                        error_message = f"Amount greater than payable"
                        if paid_amount <= 0:
                            error_message = f"Amount should be greater than 0"

                    elif transfer_type == CREDITNOTE_TRANSFER_TYPES.cash:
                        error_message = "Cash A/C doesn't have enough balance."
                    else:
                        error_message = "%s doesn't have enough balance."%bank.name

                    response_data = {
                        "status": "false",
                        "stable": 'true',
                        "title": "Transaction Failed",
                        "message": error_message,
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = CreditNoteVoucherForm(initial={"voucher_number": voucher_number})
        context = {
            "form" : form,
            "today": today,
            "redirect" : True,
            "title" : "Create Credit Note Voucher",
            "url" : reverse('finance:create_credit_note_voucher'),
        }

        return render(request,'finance/credit_note/entry_credit_note.html',context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def credit_note_vouchers(request):
    instances = CreditNoteVoucher.objects.all()
    title = "Credit Note Vouchers"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))
        title = "Credit Note Vouchers - %s" %query

    date = request.GET.get("voucher_date")
    if date:
        voucher_date = datetime.datetime.strptime(date, '%d/%m/%Y').date()
        instances = instances.filter(voucher_date__date=voucher_date)

    voucher_number = request.GET.get("voucher_number")
    if voucher_number:
        instances = instances.filter(voucher_number__icontains=voucher_number)

    filter_data = {
        "query": query,
        "voucher_date": date,
        "voucher_number": voucher_number,
    }

    context = {
        'title' : title,
        "instances" : instances,
        "filter_data": filter_data
    }

    return render(request,'finance/credit_note/credit_notes.html',context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def credit_note_voucher(request, pk):
    instance = get_object_or_404(CreditNoteVoucher.objects.filter(pk=pk,is_deleted=False))

    context = {
        "instance" : instance,
        "title" : "Credit Note Voucher : " + instance.title,
    }

    return render(request,'finance/credit_note/credit_note.html',context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_credit_note_voucher(request,pk):
    instance = get_object_or_404(CreditNoteVoucher.objects.filter(pk=pk,is_deleted=False))

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transaction_date'])
        form = CreditNoteVoucherForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                sale_return_pk = form.cleaned_data['sub_ledger']
                # fine_amount = form.cleaned_data['fine_amount']
                paid_amount = form.cleaned_data['amount']

                sale_return = SaleReturn.objects.get(pk=sale_return_pk)

                transfer_type = form.cleaned_data['transfer_type']
                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                return_amount = sale_return.amount_returned
                # payable_amount = return_amount - fine_amount
                if paid_amount > 0:
                    data = form.save(commit=False)
                    # data.payable_amount = payable_amount
                    data.is_updated = True
                    data.updater = request.user
                    data.date_updated = datetime.datetime.now()

                    data.sub_ledger_name = str(sale_return)
                    data.save()

                    response_data = {
                        "status" : "true",
                        "title" : "Successfully Updated",
                        "message" : "Credit Note Voucher Successfully Updated.",
                        "redirect" : "true",
                        "redirect_url" : reverse('finance:credit_note_voucher',kwargs={'pk':data.pk})
                    }
                else:
                    message = 'Amount should be greater than 0'
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Financial Year error",
                        "message": message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        initial = {
            'voucher_date': datetime.datetime.strftime(instance.voucher_date, '%d/%m/%Y')
        }

        if instance.transaction_date:
            initial['transaction_date'] = datetime.datetime.strftime(instance.transaction_date, '%d/%m/%Y')
        elif instance.draft_date:
            initial['draft_date'] = datetime.datetime.strftime(instance.draft_date, '%d/%m/%Y')
        elif instance.cheque_date:
            initial['cheque_date'] = datetime.datetime.strftime(instance.cheque_date, '%d/%m/%Y')

        form = CreditNoteVoucherForm(instance=instance, initial=initial)

        context = {
            "form" : form,
            "title" : "Edit Credit Note Voucher : " + instance.title,
            "instance" : instance,
            "url" : reverse('finance:edit_credit_note_voucher',kwargs={'pk':instance.pk}),
            "redirect" : True,
            "is_edit": True
        }

        return render(request, 'finance/credit_note/entry_credit_note.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_credit_note_voucher(request,pk):
    instance = get_object_or_404(CreditNoteVoucher.objects.filter(pk=pk,is_deleted=False))
    instance.is_deleted = True
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully Cancelled",
        "message" : "Credit Note Voucher Successfully Cancelled.",
        "redirect" : "true",
        "redirect_url" : reverse('finance:credit_note_vouchers')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
# End of Credit Note voucher


# debit note vouchers Start
@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def create_debit_note_voucher(request):
    voucher_no = 0
    if DebitNoteVoucher.objects.all().exists():
        voucher_no = DebitNoteVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number', 0)
    voucher_number = voucher_no + 1

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transaction_date'])
        form = DebitNoteVoucherForm(ModifiedRequest)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']
            purchase_return = form.cleaned_data['purchase_return']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                paid_amount = form.cleaned_data['amount']

                transfer_type = form.cleaned_data['transfer_type']
                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                if paid_amount <= purchase_return.amount_returned and paid_amount > 0:
                    data = form.save(commit=False)
                    data.creator = request.user
                    data.updater = request.user
                    data.warehouse = purchase_return.purchase.warehouse
                    data.auto_id = get_auto_id(DebitNoteVoucher)
                    data.save()

                    response_data = {
                        "status" : "true",
                        "title" : "Successfully Created",
                        "message" : "Debit Note Voucher created successfully.",
                        "redirect" : "true",
                        "redirect_url" : reverse('finance:debit_note_voucher',kwargs={'pk':data.pk})
                    }
                else:
                    message = 'Amount greater than returnable amount'
                    if paid_amount <= 0:
                        message = 'Amount should be greater than 0'
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Financial Year error",
                        "message": message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = DebitNoteVoucherForm(initial={"voucher_number": voucher_number})
        context = {
            "form" : form,
            "redirect" : True,
            "title" : "Create Debit Note Voucher",
            "url" : reverse('finance:create_debit_note_voucher'),
        }

        return render(request,'finance/debit_note/entry_debit_note.html',context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def debit_note_vouchers(request):
    instances = DebitNoteVoucher.objects.all()
    title = "Debit Note Vouchers"

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))
        title = "Debit Note Vouchers - %s" %query

    date = request.GET.get("voucher_date")
    if date:
        voucher_date = datetime.datetime.strptime(date, '%d/%m/%Y').date()
        instances = instances.filter(voucher_date__date=voucher_date)

    voucher_number = request.GET.get("voucher_number")
    if voucher_number:
        instances = instances.filter(voucher_number__icontains=voucher_number)

    filter_data = {
        "query": query,
        "voucher_date": date,
        "voucher_number": voucher_number,
    }

    context = {
        'title' : title,
        "instances" : instances,
        "filter_data": filter_data
    }

    return render(request,'finance/debit_note/debit_notes.html',context)


@check_mode
@login_required
@role_required(['superadmin', 'staff_user'])
def debit_note_voucher(request, pk):
    instance = get_object_or_404(DebitNoteVoucher.objects.filter(pk=pk,is_deleted=False))

    context = {
        "instance" : instance,
        "title" : "Debit Note Voucher : " + instance.title,
    }

    return render(request,'finance/debit_note/debit_note.html',context)


@check_mode
@login_required
@role_required(['superadmin'])
def edit_debit_note_voucher(request,pk):
    instance = get_object_or_404(DebitNoteVoucher.objects.filter(pk=pk,is_deleted=False))

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['voucher_date', 'cheque_date', 'draft_date', 'transaction_date'])
        form = DebitNoteVoucherForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            voucher_date = form.cleaned_data['voucher_date']

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=voucher_date, end_date__date__gte=voucher_date).exists():
                purchase_return_pk = form.cleaned_data['sub_ledger']
                paid_amount = form.cleaned_data['amount']

                transfer_type = form.cleaned_data['transfer_type']
                if transfer_type in [15, 20, 25]:
                    bank = form.cleaned_data['bank']
                    if not bank:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Please choose a bank account before submitting."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                purchase_return = PurchaseReturn.objects.get(pk=purchase_return_pk)

                if paid_amount > 0:
                    data = form.save(commit=False)
                    data.sub_ledger_name = str(purchase_return)
                    data.updater = request.user
                    data.is_updated = True
                    data.date_updated = datetime.datetime.now()
                    data.save()

                    response_data = {
                        "status" : "true",
                        "title" : "Successfully Updated",
                        "message" : "Debit Note Voucher Successfully Updated.",
                        "redirect" : "true",
                        "redirect_url" : reverse('finance:debit_note_voucher',kwargs={'pk':data.pk})
                    }
                else:
                    message = 'Amount should be greater than 0'
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Financial Year error",
                        "message": message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Voucher date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = DebitNoteVoucherForm(instance=instance)

        initial = {
            'voucher_date': datetime.datetime.strftime(instance.voucher_date, '%d/%m/%Y')
        }

        if instance.transaction_date:
            initial['transaction_date'] = datetime.datetime.strftime(instance.transaction_date, '%d/%m/%Y')
        elif instance.draft_date:
            initial['draft_date'] = datetime.datetime.strftime(instance.draft_date, '%d/%m/%Y')
        elif instance.cheque_date:
            initial['cheque_date'] = datetime.datetime.strftime(instance.cheque_date, '%d/%m/%Y')

        context = {
            "form" : form,
            "title" : "Edit Debit Note Voucher : " + instance.title,
            "instance" : instance,
            "url" : reverse('finance:edit_debit_note_voucher',kwargs={'pk':instance.pk}),
            "redirect" : True,
            "is_edit": True
        }

        return render(request, 'finance/debit_note/entry_debit_note.html', context)


@check_mode
@login_required
@role_required(['superadmin'])
def delete_debit_note_voucher(request,pk):
    instance = get_object_or_404(DebitNoteVoucher.objects.filter(pk=pk,is_deleted=False))
    instance.is_deleted = True
    instance.save()

    response_data = {
        "status" : "true",
        "title" : "Successfully Cancelled",
        "message" : "Debit Note Voucher Successfully Cancelled.",
        "redirect" : "true",
        "redirect_url" : reverse('finance:debit_note_vouchers')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_invoice_prifix(request):

    if request.method == 'POST':
        form = InvoicePrefixForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(InvoicePrefix)

            # create InvoicePrefix
            financial_year = None
            if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True)

                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.financial_year = financial_year
                data.auto_id = auto_id

                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Invoice Prifix Created Successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('finance:invoice_prifix', kwargs={'pk': data.pk})
                }
            else:
                error_message = "Please Add a Financial year."
                error_message = "Don't have an active Financial year."
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
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
        form = InvoicePrefixForm()
        context = {
            "title": "Create Invoice Prifix ",
            "form": form,
            "url": reverse('finance:create_invoice_prifix'),
        }

        return render(request, 'finance/invoice_prifix/invoice_prifix_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def invoice_prifixs(request):
    instances = InvoicePrefix.objects.filter(is_deleted=False)
    title = "Invoice Prifix"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(order__icontains=query)| Q(purchase__icontains=query))
        title = "Invoice Prifix - %s" % query

    context = {
        "instances": instances,
        'title': title,
    }
    return render(request, 'finance/invoice_prifix/invoice_prifixs.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def invoice_prifix(request, pk):
    instance = get_object_or_404(InvoicePrefix.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "InvoicePrefix",
        "single_page": True,

    }
    return render(request, 'finance/invoice_prifix/invoice_prifix.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_invoice_prifix(request, pk):
    instance = get_object_or_404(InvoicePrefix.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = InvoicePrefixForm(request.POST, instance=instance)

        if form.is_valid():

            # update InvoicePrefix
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "InvoicePrefix Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('finance:invoice_prifix', kwargs={'pk': data.pk})
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
        form = InvoicePrefixForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit InvoicePrefix",
            "instance": instance,
            "url": reverse('finance:edit_invoice_prifix', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'finance/invoice_prifix/invoice_prifix_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_invoice_prifix(request, pk):
    reason = request.GET.get('reason')

    instance = get_object_or_404(InvoicePrefix.objects.filter(pk=pk, is_deleted=False))

    InvoicePrefix.objects.filter(pk=pk).update(
        is_deleted=True,deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "InvoicePrefix Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('finance:invoice_prifixs')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_invoice_prifixs(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                InvoicePrefix.objects.filter(pk=pk, is_deleted=False))
            InvoicePrefix.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected InvoicePrefixs Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('finance:invoice_prifixs')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_account_head(request):
    pk = request.GET.get('id')
    warehouse = None

    if request.GET.get("warehouse"):
        if Warehouse.objects.filter(pk=request.GET.get("warehouse")).exists():
            warehouse = Warehouse.objects.get(pk=request.GET.get("warehouse"))

    if pk:
        account_heads = AccountHead.objects.filter(pk=pk)

        if account_heads.exists() and warehouse:
            instance = account_heads.last()

            if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()
                if AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).exists():
                    head_opening = AccountHeadOpening.objects.filter(financial_year=financial_year, warehouse=warehouse, account_head=instance, is_deleted=False).last()

                    response_data = {
                        "status": "true",
                        'opening_balance': str(head_opening.amount),
                        'opening_balance_type': head_opening.amount_type
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    response_data = {
        "status": "false",
        "message": "AccountHead doesn't exists."
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
