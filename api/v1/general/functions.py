import datetime
import random
import re
import requests
import decimal
import string
from products.models import Category,ProductVariant


def generate_serializer_errors(args):
    message = ''
    for key, values in args.items():
        error_message = ""
        for value in values:
            error_message += value + ","
        error_message = error_message[:-1]

        message += "%s : %s |" % (key, error_message)
    return message[:-3]


def get_user_token(request, user_name, password):
    headers = {
        'Content-Type': 'application/json',
    }
    data = '{"username": "' + user_name + '", "password":"' + password + '"}'
    print(data, "--data")
    protocol = "http://"
    if request.is_secure():
        protocol = "https://"

    web_host = request.get_host()
    request_url = protocol + web_host + "/api/v1/auth/token/"

    print(request_url, "--------request_url")

    response = requests.post(request_url, headers=headers, data=data)
    print(response, "------response2")
    return (response)


def is_pincode_exists(request):
    if 'pincode' in request.session:
        return True
    else:
        return False

def get_pincode(request):
    pincode_session = request.session.get('pincode', '')
    if pincode_session:
        return pincode_session

def get_shop_category_instances(product_instances):
   categories = product_instances.values_list('product__category',flat=True).distinct()
   category_instances = Category.objects.filter(pk__in=categories)

   return category_instances

def get_retail_price_of_product(request):
    """
    get retail price of a product from chosen pincode, if pincode is none the products retail price will added
    :param request:
    """
    pass
