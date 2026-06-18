import math
import string
import random
import datetime
import requests
import urllib
from decimal import Decimal
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Max
from main.models import Settings
# from finance.models import FinancialYear


def get_otp(size=4, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ipaddress = x_forwarded_for.split(',')[-1].strip()
    else:
        ipaddress = request.META.get('REMOTE_ADDR')

    return ipaddress


def get_auto_id(model):
    auto_id = 1
    latest_auto_id = model.objects.aggregate(Max('auto_id'))
    max_auto_id = latest_auto_id['auto_id__max']
    if max_auto_id:
        auto_id = int(max_auto_id) + 1

    return auto_id


def get_a_id(model, warehouse):
    print(warehouse)
    a_id = 1
    latest_a_id = model.objects.filter(warehouse_id=warehouse.pk).aggregate(Max('a_id'))['a_id__max']
    if latest_a_id:
        a_id = int(latest_a_id) + 1

    return a_id


def generate_form_errors_old(args, formset=False):
    message = ''
    if not formset:
        for field in args:
            if field.errors:
                message += field.errors + "|"
        for err in args.non_field_errors():
            message += str(err) + "|"

    elif formset:
        for form in args:
            for field in form:
                if field.errors:
                    message += field.errors + "|"
            for err in form.non_field_errors():
                message += str(err) + "|"
    return message[:-1]


def generate_form_errors(args, formset=False):
    i = 1
    message = ""
    if not formset:
        for field in args:
            if field.errors:
                message += "\n"
                message += field.label + " : "
                message += str(field.errors)

        for err in args.non_field_errors():
            message += str(err)
    elif formset:
        for form in args:
            for field in form:
                if field.errors:
                    message += "\n"
                    message += field.label + " : "
                    message += str(field.errors)
            for err in form.non_field_errors():
                message += str(err)

    message = message.replace("<li>", "")
    message = message.replace("</li>", "")
    message = message.replace('<ul class="errorlist">', "")
    message = message.replace("</ul>", "")
    return message


def get_current_role(request):
    is_superadmin = False
    is_customer_user = False
    is_vendor_user = False

    is_supplier_user = False
    is_delivery_agent = False
    is_warehouse_manager = False
    is_normal_staff = False
    is_billing_staff = False

    current_role = "user"
    if request.user.is_authenticated:
        groups = request.user.groups.all()

        if request.user.is_superuser:
            is_superadmin = True
        elif groups.filter(name="customer_user").exists():
            is_customer_user = True
        elif groups.filter(name="vendor_user").exists():
            is_vendor_user = True
        elif groups.filter(name="supplier_user").exists():
            is_supplier_user = True
        elif groups.filter(name="delivery_agent").exists():
            is_delivery_agent = True
        elif groups.filter(name="warehouse_manager").exists():
            is_warehouse_manager = True
        elif groups.filter(name="normal_staff").exists():
            is_normal_staff = True
        elif groups.filter(name="billing_staff").exists():
            is_billing_staff = True

        if "current_role" in request.session:
            role = request.session['current_role']
            if role == "superadmin":
                current_role = "superadmin"
            elif role == "customer_user":
                current_role = "customer_user"
            elif role == "vendor_user":
                current_role = "vendor_user"
            elif role == "supplier_user":
                current_role = "supplier_user"
            elif role == "delivery_agent":
                current_role = "delivery_agent"
            elif role == "warehouse_manager":
                current_role = "warehouse_manager"
            elif role == "normal_staff":
                current_role = "normal_staff"
            elif role == "billing_staff":
                current_role = "billing_staff"
        else:
            if is_superadmin:
                current_role = "superadmin"
            elif is_customer_user:
                current_role = "customer_user"
            elif is_vendor_user:
                current_role = "vendor_user"
            elif is_supplier_user:
                current_role = "supplier_user"
            elif is_delivery_agent:
                current_role = "delivery_agent"
            elif is_warehouse_manager:
                current_role = "warehouse_manager"
            elif is_normal_staff:
                current_role = "normal_staff"
            elif is_billing_staff:
                current_role = "billing_staff"

        return current_role


def get_purchase_no(Model):
    purchase_no = 1
    if Model.objects.all().exists():
        latest_purchase_no = Model.objects.all().latest("date_added")
        purchase_no = latest_purchase_no.purchase_no + 1
    return purchase_no


def get_purchase_order_no(Model):
    purchase_no = 1
    if Model.objects.all().exists():
        latest_purchase_no = Model.objects.all().latest("date_added")
        if latest_purchase_no.order_no:
            purchase_no = latest_purchase_no.order_no + 1
        else:
            purchase_no = 1
    return purchase_no


def get_settings_sale():
    instance, created = Settings.objects.get_or_create(counter=1)
    return instance


def get_order_id(model):
    order_no = 1
    latest_order_no = model.objects.all().order_by("-date_added")[:1]
    if latest_order_no:
        for auto in latest_order_no:
            order_no = auto.order_no + 1
    return order_no


def sendSMS(message_type, numbers, variables_values=[]):
    key = 'HAXYGvLOxmIS2DVf6cFaTW4NndPjlyitJrRqswKBQZ58Mb01g3Zk6r5Bm3PXti9jVSdcY1AxsJgz2Ev0'
    values = '|'.join(variables_values)
    is_ok = True

    if message_type == 'otp':
        message_id = 138154
        # variables = otp

    elif message_type == 'placed':
        message_id = 138155
        # variables = order_id, date

    elif message_type == 'shipped':
        message_id = 138156
        # variables = order_id, date

    elif message_type == 'on_delivery':
        message_id = 138158
        # variables = order_id

    elif message_type == 'delivered':
        message_id = 138159
        # variables = date

    elif message_type == 'cancelled':
        message_id = 138160
        # variables = order_id

    else:
        is_ok = False

    if settings.SERVER == False:
        is_ok = False

    if is_ok:
        url = f"https://www.fast2sms.com/dev/bulkV2?authorization={key}&route=dlt&sender_id=ONIAZA&message={message_id}&variables_values={values}&flash=0&numbers={numbers}"

        r = requests.get(url=url)
        data = r.content

        return data
    else:
        return ''


# def sendSMS(numbers, message):
    # apikey = "MzM1MjY1NmM0YzMxNDMzMzcyNjk0NTRlNDE3NDU3NzI="
    # sender = 'ONIAZA'

    # data = urllib.parse.urlencode({
    #     'apikey': apikey,
    #     'numbers': numbers,
    #     'message' : message,
    #     'sender': sender
    # })

    # data = data.encode('utf-8')
    # request = urllib.request.Request("https://api.textlocal.in/send/?")

    # f = urllib.request.urlopen(request, data)
    # fr = f.read()

    # return(fr)


def send_email(to_address, subject, content, html_content, attachment=None, attachment2=None, attachment3=None):
    new_message = MailerMessage()
    new_message.subject = subject
    new_message.to_address = to_address
    # if bcc_address:
    #     new_message.bcc_address = bcc_address
    new_message.from_address = settings.DEFAULT_FROM_EMAIL
    new_message.content = content
    new_message.html_content = html_content
    if attachment:
        new_message.add_attachment(attachment)
    if attachment2:
        new_message.add_attachment(attachment2)
    if attachment3:
        new_message.add_attachment(attachment3)
    new_message.app = "default"
    new_message.save()


def get_placeholder():
    image = 'https://i2.wp.com/quidtree.com/wp-content/uploads/2020/01/placeholder.png?fit=1200%2C800&ssl=1'
    return image


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


# def get_current_financial_year():
    # financial_year = FinancialYear.objects.filter(is_active=True, is_deleted=False).last()
    # return financial_year


def get_date_updated_request(request_post, field_names):
    for field_name in field_names:
        try:
            date_str = request_post.get(field_name)

            if date_str:
                try:
                    my_date = datetime.datetime.strptime(str(date_str), '%d/%m/%Y')

                except:
                    try:
                        my_date = datetime.datetime.strptime(str(date_str), '%m/%d/%Y')
                    except:
                        my_date = None

                if my_date:
                    str_date = datetime.datetime.strftime(my_date, '%m/%d/%Y')
                    request_post.update({field_name: str_date})
        except:
            pass

    return request_post
