import json
from django.db.models import Count, F
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes, renderer_classes)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.v1.general.banner_utils import BannerUtils
from api.v1.general.functions import is_pincode_exists, get_pincode, get_shop_category_instances
from api.v1.general.serializers import *
from offers.models import Offers
from products.models import Category, ProductVariant
from web.models import ProductReview
from main.models import AppUpdate


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def offer_sliders(request):
    instances = Offers.objects.filter(is_deleted=False)

    if is_pincode_exists(request):
        pincode = get_pincode(request)
        instances = instances.filter(warehouse__location__pincode=pincode)

    serialized = OfferSlidersSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_latest_category_offer(request):
    instances = Offers.objects.filter(is_deleted=False, offer_type__in=['category', 'sub_category']).first()

    if is_pincode_exists(request):
        pincode = get_pincode(request)
        instances = Offers.objects.filter(is_deleted=False, offer_type__in=['category', 'sub_category'],
                                          warehouse__location__pincode=pincode).first()

    serialized = OfferSlidersSerializer(instances, context={"request": request})

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def categories(request):
    instances = Category.objects.filter(is_deleted=False)
    serialized = CategorySerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def best_sellers(request):
    minimal = request.GET.get('minimal')
    query = request.GET.get('query')
    category = request.GET.get('category')
    sub_category = request.GET.get('sub_category')
    sort = request.GET.get('sort')

    try:
        category = category.replace('/', '') if category else None
        sub_category = sub_category.replace('/', '') if category else None
        sort = sort.replace('/', '') if category else None
    except:
        pass

    variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True)

    # get the best sellers item on the basis of order+sale count
    product_instances = variants.annotate(order_count=Count('orderitem'), sale_count=Count('saleitem'),
        total_count=F('sale_count') + F('order_count')).order_by('-total_count')

    if minimal:
        product_instances = product_instances[:1]

    if query:
        product_instances = product_instances.filter(Q(title__icontains=query) | Q(product__name__icontains=query) | Q(
            product__brand__name__icontains=query) | Q(product__category__name__icontains=query) | Q(
            product__subcategory__name__icontains=query))
    if category:
        product_instances = product_instances.filter(product__category__pk=category)

    if sub_category:
        product_instances = product_instances.filter(product__subcategory__pk=sub_category)

    if sort:
        if 'a-z' in sort:
            product_instances = product_instances.order_by("title")
        elif 'z-a' in sort:
            product_instances = product_instances.order_by("-title")

        elif 'price_increase' in sort:
            product_instances = product_instances.order_by("mrp")

        elif 'price_decrease' in sort:
            product_instances = product_instances.order_by("-mrp")

    product_instances = product_instances[:30]  # to get only 30 variants

    serialized = BestSellersSerializer(product_instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def nearest_shops(request):
    instances = Vendor.objects.filter(is_deleted=False)

    query = request.GET.get('query').replace('/', '')

    if query:
        instances = instances.filter(name__icontains=query)

    # instances =  instances[:5]

    serialized = ShopSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def best_offers(request):
    instances = None

    query = request.GET.get('query').replace('/', '')

    instances = Offers.objects.filter(offer_type="product", is_deleted=False).order_by('-date_added')

    if is_pincode_exists(request):
        pincode = get_pincode(request)
        instances = Offers.objects.filter(offer_type="product", is_deleted=False, warehouse__location__pincode=pincode)

    if query:
        instances = instances.filter(
            Q(product_variant__title__icontains=query) | Q(product_variant__product__name__icontains=query) | Q(
                product_variant__product__brand__name__icontains=query) | Q(
                product_variant__product__category__name__icontains=query) | Q(
                product_variant__product__subcategory__name__icontains=query))

    serialized = BestOfferSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def product(request, pk):
    instance = ProductVariant.objects.get(pk=pk)

    serialized = ProductVariantSerializer(instance, context={"request": request})

    response_data = {"StatusCode": 6000, "data": serialized.data, }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def shops(request):
    query = request.GET.get('query')

    instances = Vendor.objects.filter(is_deleted=False)

    if is_pincode_exists(request):
        pincode = get_pincode(request)
        instances = Vendor.objects.filter(is_deleted=False, location__pincode=pincode)

    if query:
        instances = instances.filter(name__icontains=query)

    serialized = ShopSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def shop(request, pk):
    query = request.GET.get('query').replace('/', '')
    sort = request.GET.get('sort').replace('/', '')
    category = request.GET.get('category').replace('/', '')
    sub_category = request.GET.get('sub_category').replace('/', '')

    if Vendor.objects.filter(pk=pk).exists():
        shop_instances = Vendor.objects.get(pk=pk)

        instances = ProductVariant.objects.filter(is_deleted=False, product__vendor=shop_instances, is_admin_approved=True)
        category_instances = get_shop_category_instances(instances)

        if query:
            instances = instances.filter(Q(title__icontains=query) | Q(product__name__icontains=query) | Q(
                product__brand__name__icontains=query) | Q(product__category__name__icontains=query) | Q(
                product__subcategory__name__icontains=query))

        if sort:
            if 'a-z' in sort:
                instances = instances.order_by("title")
            elif 'z-a' in sort:
                instances = instances.order_by("-title")

            elif 'price_increase' in sort:
                instances = instances.order_by("mrp")

            elif 'price_decrease' in sort:
                instances = instances.order_by("-mrp")

        if category:
            instances = instances.filter(product__category__pk=category)

        if sub_category:
            instances = instances.filter(product__subcategory__pk=sub_category)

        serialized = BestSellersSerializer(instances, context={"request": request}, many=True)
        shop_serialized = ShopSerializer(shop_instances, context={"request": request})
        category_serialized = CategorySerializer(category_instances, context={"request": request}, many=True)

        response_data = {"StatusCode": 6000, "shop": shop_serialized.data, "data": serialized.data,
            "categories": category_serialized.data, }
    else:
        response_data = {"StatusCode": 6001, "message": "Shop Not Found"}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def search(request):
    instances = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True)

    query = request.GET.get('query').replace('/', '')
    sort = request.GET.get('sort').replace('/', '')
    category = request.GET.get('category').replace('/', '')
    sub_category = request.GET.get('sub_category').replace('/', '')

    if query:
        instances = instances.filter(Q(title__icontains=query) | Q(product__name__icontains=query) | Q(
            product__brand__name__icontains=query) | Q(product__category__name__icontains=query) | Q(
            product__subcategory__name__icontains=query))

    if sort:
        if 'a-z' in sort:
            instances = instances.order_by("title")
        elif 'z-a' in sort:
            instances = instances.order_by("-title")

        elif 'price_increase' in sort:
            instances = instances.order_by("mrp")

        elif 'price_decrease' in sort:
            instances = instances.order_by("-mrp")

    if category:
        instances = instances.filter(product__category__pk=category)

    if sub_category:
        instances = instances.filter(product__subcategory__pk=sub_category)

    paginator = PageNumberPagination()
    paginator.page_size = 2
    result_page = paginator.paginate_queryset(instances, request)
    # serialized = ProductVariantSerializer(instances, many=True,context={"request":request})
    serialized = BestSellersSerializer(instances, many=True, context={"request": request})
    return paginator.get_paginated_response(serialized.data)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def product_reviews(request, pk):
    product_current_rating_count = ProductVariant.objects.get(pk=pk)
    instances = ProductReview.objects.filter(product_variant__pk=pk)

    instances_count = instances.count()

    ratings = {"rating": str(round(product_current_rating_count.current_rating, 1)),
        "no_of_customers_rated": str(instances_count), }

    paginator = PageNumberPagination()
    paginator.page_size = 2
    result_page = paginator.paginate_queryset(instances, request)

    serialized = ProductReviewSerializer(instances, context={"request": request}, many=True)

    return paginator.get_paginated_response(serialized.data)


@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def app_update(request):
    instances = AppUpdate.objects.all()
    obj = {}

    if instances.exists():
        instance = instances.latest('id')

        obj = {'version': instance.version, 'force_update': instance.force_update,
            'update_recomented': instance.update_recomented, }

    response_data = {"StatusCode": 6000, "data": obj}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def banners(request):
    banner_type = request.GET.get('banner_type', None)
    banner_utils = BannerUtils(banner_type, request)
    data = banner_utils.serialized_datas()

    response_data = {"StatusCode": 6000, "data": data}

    return Response(response_data, status=status.HTTP_200_OK)
