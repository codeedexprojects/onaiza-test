import os

import xlwt
from django.conf import settings as SETTINGS

from purchases.filters import PurchaseFilter


class ExportToExcelUtils:
    def __init__(self, instances, serializer, request, file_name):
        self.instances = instances
        self.serializer = serializer
        self.request = request
        self.file_name = file_name

    def make_heading(self, name):
        """
        creation of table heading
        :param name:
        :return:
        """
        return name.capitalize().replace('_display', '').replace('__date', '').replace('__', ' ').replace('_', ' ')

    def export_to_excel(self):
        """
        export to excel function
        :return:
        """
        instances = self.instances

        list_data = self.serializer(instance=instances, many=True,
                                    context={'request': self.request, 'is_excel': "true"}).data
        wb = xlwt.Workbook()
        title = self.file_name
        ws = wb.add_sheet(title)

        for index, item in enumerate(list_data):
            if index == 0:
                for key_index, key in enumerate(item.keys()):
                    ws.write(index, key_index, self.make_heading(key))

            for item_index, value in enumerate(item.values()):
                ws.write(index + 1, item_index, str(value))

        if not os.path.isdir(str(SETTINGS.MEDIA_ROOT) + "/excels/"):
            os.makedirs(str(SETTINGS.MEDIA_ROOT) + "/excels/")

        media_root = str(SETTINGS.MEDIA_ROOT) + '/excels/' + title + '.xls'
        wb.save(media_root)

        file_url = str(SETTINGS.MEDIA_URL + '/excels/' + title + '.xls')

        return file_url

    def export_to_excel_single_objects(self, instances):

        list_data = self.serializer(instance=instances, many=True,
                                    context={'request': self.request, 'is_excel': "true"}).data
        wb = xlwt.Workbook()
        title = self.file_name
        ws = wb.add_sheet(title)

        for index, item in enumerate(list_data):
            if index == 0:
                for key_index, key in enumerate(item.keys()):
                    ws.write(index, key_index, self.make_heading(key))

            for item_index, value in enumerate(item.values()):
                ws.write(index + 1, item_index, str(value))

        if not os.path.isdir(str(SETTINGS.MEDIA_ROOT) + "/excels/"):
            os.makedirs(str(SETTINGS.MEDIA_ROOT) + "/excels/")

        media_root = str(SETTINGS.MEDIA_ROOT) + '/excels/' + title + '.xls'
        wb.save(media_root)

        file_url = str(SETTINGS.MEDIA_URL + '/excels/' + title + '.xls')

        return file_url
