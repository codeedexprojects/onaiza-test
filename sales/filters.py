import datetime

from django.db.models import Q
from sales.models import Sale


class SaleFilter:
    def __init__(self, request):
        self.request = request

    def get_q(self, query, instances):
        """
        fetch all purchases consist of query
        :param query:
        :param instances:
        :return:
        """
        print("q params==>>",query)
        results = instances.filter(
            Q(sale_id__istartswith=query) |
            Q(tracking_id__istartswith=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(customer__email__icontains=query) |
            Q(customer__address__icontains=query)
        )

        return results

    def get_on_date(self, on_date, instances):
        """
        return purchases with specified date
        :param on_date:
        :param instances:
        :return:
        """
        o_date = datetime.datetime.strptime(on_date, '%Y-%m-%d').date()
        results = instances.filter(sale_date__date=o_date)
        return results

    def get_from_to_date(self, from_date, to_date, instances):
        # f_date = datetime.strptime(from_date, '%d/%m/%Y').date()
        # t_date = datetime.strptime(to_date, '%d/%m/%Y').date()
        f_date = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
        t_date = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
        results = instances.filter(sale_date__date__range=[f_date, t_date])
        return results

    def get_payment_method(self, method, instances):
        results = instances.filter(payment_method=method)
        return results

    def get_invoice_id(self, id, instances):
        results = instances.filter(Q(sale_id__istartswith=id))
        return results

    def get_filtered_results(self):
        """
        fetch all the results after query
        :return:
        """
        results = Sale.objects.filter(is_deleted=False)

        query = self.request.GET.get("q")
        on_date = self.request.GET.get('on_date')
        to_date = self.request.GET.get('to_date')
        from_date = self.request.GET.get('from_date')
        payment_method = self.request.GET.get('payment_method')
        invoice_id = self.request.GET.get('invoice_id')
        view_option = self.request.GET.get('view')

        if query:
            print("q3eury is =>",query)
            results = self.get_q(query, results)

        if on_date:
            results = self.get_on_date(on_date, results)

        if from_date and to_date:
            results = self.get_from_to_date(from_date, to_date, results)

        if payment_method:
            results = self.get_payment_method(payment_method, results)

        if invoice_id:
            results = self.get_invoice_id(invoice_id, results)

        return results
