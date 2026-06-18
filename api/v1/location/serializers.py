from rest_framework import serializers
from warehouses.models import Location



class LocationSerializer(serializers.ModelSerializer):

    is_default = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['name','pincode','is_default', 'id','malayalam_name']

    def get_is_default(self,instances):
        request = self.context.get("request")
        pincode_session = request.session.get('pincode', '')
        if pincode_session:
            if pincode_session == instances.pincode:
                return True
            else:
                return False
        else:
            return False
