from api.v1.general.serializers import BannerSerializer
from web.models import SpotlightBanner


class BannerUtils:
    def __init__(self, banner_type, request):
        self.banner_type = banner_type
        self.request = request

    def get_banners(self):
        print("Banner type is ", self.banner_type)
        return SpotlightBanner.objects.filter(is_deleted=False, banner_type=self.banner_type)

    def serialized_datas(self):
        instances = self.get_banners()
        serialized = BannerSerializer(instances, many=True, context={"request": self.request})
        return serialized.data
