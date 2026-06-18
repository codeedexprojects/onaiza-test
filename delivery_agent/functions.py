import googlemaps

from delivery_agent.models import DeliveryAgents, DeliveryAgentTravel
from django.db.models import Sum, F


def get_location_distance(request, franchaisee, origins):
    gmaps = googlemaps.Client(key='AIzaSyBlZedPGDv2kGpzevN9Q43ZyXHAXUby67w')

    location = franchaisee.location
    latitude = location.latitude
    longitude = location.longitude
    destination = (latitude, longitude)

    result = gmaps.distance_matrix(origins, destination, mode='driving')["rows"][0]["elements"][0]

    try:
        distance = result['distance']
        distance = distance['text']
        distance = distance.split(" ")
        distance_1 = distance[0]
        distance_type = distance[1]
        distance_1 = float(distance_1)
        if distance_type == "km":
            distance_1 = 1000 * distance_1

        duration = result['duration']
        duration = duration['text']
        duration = duration.split(" ")
        duration_1 = duration[0]
        duration_type = duration[1]
        duration_1 = float(duration_1)
        try:
            if duration_type == "hour" or duration_type == "hours":
                duration_1 = duration_1 * 60
                dur_min = duration[2]
                dur_min = float(dur_min)
                duration_1 += dur_min
        except:
            pass
    except:
        distance_1 = 100000
        duration_1 = 100000

    return {"distance": distance_1, "duration": duration_1}


def get_distance_and_duration(request, instance, origins, distances, durations):
    result = get_location_distance(request, instance, origins)
    distance = result["distance"]
    duration = result["duration"]
    distances.append(distance)
    durations.append(duration)

    return {"distances": distances, "durations": durations}


def get_origins(request, instance):
    location = instance.location
    origins = (location.latitude, location.longitude)

    return origins


def get_all_delivery_agents():
    agents = DeliveryAgents.objects.filter(is_deleted=False)
    return agents


def get_total_distance(agent):
    distance_travelled = DeliveryAgentTravel.objects.filter(
        delivery_agent=agent
    ).aggregate(
        total_distance=Sum(F('pickup_distance')) + Sum(F('delivery_distance'))
    )['total_distance']

    return distance_travelled


def serializer_return(field, returnable_value):
    if field:
        return returnable_value
    else:
        return "-"
