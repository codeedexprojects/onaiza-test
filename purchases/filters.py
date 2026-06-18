import datetime

from django.db.models import Q
from purchases.models import Purchase


class PurchaseFilter:
    def __init__(self, request):
        self.request = request

    def get_q(self, query, instances):
        """
        fetch all purchases consist of query
        :param query:
        :param instances:
        :return:
        """
        results = instances.filter(
            Q(purchase_id__icontains=query) | Q(paid__icontains=query) | Q(subtotal__icontains=query) | Q(
                supplier__name__icontains=query) | Q(creator__username__icontains=query))

        return results

    def get_on_date(self, on_date, instances):
        """
        return purchases with specified date
        :param on_date:
        :param instances:
        :return:
        """
        # o_date = datetime.datetime.strptime(on_date, '%d/%m/%Y').date()
        results = instances.filter(date__date=on_date)
        return results

    def get_from_to_date(self, from_date, to_date, instances):
        # f_date = datetime.strptime(from_date, '%d/%m/%Y').date()
        # t_date = datetime.strptime(to_date, '%d/%m/%Y').date()
        results = instances.filter(date__date__range=[from_date, to_date])
        return results

    def get_payment_method(self, method, instances):
        results = instances.filter(payment_method=method)
        return results

    def get_supplier(self,supplier,instances):
        results = instances.filter(supplier__pk=supplier)
        return results

    def get_filtered_results(self):
        """
        fetch all the results after query
        :return:
        """
        results = Purchase.objects.filter(is_deleted=False)

        query = self.request.GET.get("q")
        on_date = self.request.GET.get('on_date')
        to_date = self.request.GET.get('to_date')
        from_date = self.request.GET.get('from_date')
        payment_method = self.request.GET.get('payment_method')
        supplier = self.request.GET.get('suppliers')

        if query:
            results = self.get_q(query, results)

        if on_date:
            results = self.get_on_date(on_date, results)

        if from_date and to_date:
            results = self.get_from_to_date(from_date, to_date,results)

        if payment_method:
            results = self.get_payment_method(payment_method,results)

        if supplier:
            results = self.get_supplier(supplier,results)

        return results
