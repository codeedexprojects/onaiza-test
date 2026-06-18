import googlemaps
from delivery_agent.models import CollectPayment, DeliveryAgents
from django.db.models import Sum
from orders.models import Orders


def get_cash_in_hand(request):
    total_amount_collected_sum = Orders.objects.filter(
        order_status="30",
        delivery_agent__user=request.user,
        payment_status="20"
    ).aggregate(Sum('total_amt'))

    total_amount_transferred_sum = CollectPayment.objects.filter(delivery_agent__user=request.user,is_transferred=False ).aggregate(
        Sum('collected_amount'))


    total_amount = total_amount_collected_sum['total_amt__sum']
    total_transferred_amount = total_amount_transferred_sum['collected_amount__sum']

    return {
        "amount": total_amount_transferred_sum['collected_amount__sum'],
        "transferred": total_transferred_amount,
    }


def calculate_distance(travel_data, status):
    gmaps = googlemaps.Client(key='AIzaSyA6pvYf7Nz2PpHhMAUIFSew0vsGykAyegU')

    if status == 'picked_up':
        origin = (travel_data.origin_latitude, travel_data.origin_longitude)
        destination = (travel_data.pickup_latitude, travel_data.pickup_longitude)

    else:
        origin = (travel_data.pickup_latitude, travel_data.pickup_longitude)
        destination = (travel_data.delivery_latitude, travel_data.delivery_longitude)

    google_result = gmaps.distance_matrix(origin, destination, mode='driving')

    sample_data = {
        'destination_addresses': ['7CHM+57M, Kerala 679332, India'],
        'origin_addresses': ['Kerala 685501, India'],
        'rows': [{
            'elements': [{
                'distance': {
                    'text': '314 km',
                    'value': 313830
                },
                'duration': {
                    'text': '9 hours 19 mins',
                    'value': 33553
                },
                'status': 'OK'
            }]
        }],
        'status': 'OK'
    }

    if google_result['status'] == "OK":
        try:
            google_data = google_result["rows"][0]["elements"][0]
            distance_in_meters = google_data['distance']['value']
            duration_in_second = google_data['duration']['value']

            distance = distance_in_meters
            duration = duration_in_second // 60 # minutes

            distance_text = google_data['distance']['text']
            duration_text = google_data['duration']['text']

        except:
            distance = 0
            distance_text = ''
            duration = 0
            duration_text = ''
    else:
        distance = 0
        distance_text = ''
        duration = 0
        duration_text = ''

    return {
        "distance": distance,
        "distance_text": distance_text,

        "duration": duration,
        "duration_text": duration_text,
    }


def get_delivery_agent(user):
    instance = DeliveryAgents.objects.get(user=user)
    return instance