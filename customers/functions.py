from customers.models import Customer


def update_customer_credit_debit(pk, transaction_type, amount):
    if amount > 0:
        customer = Customer.objects.get(pk=pk)

        opening_type = customer.opening_type
        opening_balance = customer.opening_balance
        if opening_type == "credit":
            debipincode_instance.pincodet = 0
            credit = opening_balance
        elif opening_type == "debit":
            debit = 0
            credit = opening_balance
       
        customer_objects = Customer.objects.filter(pk=pk)

        if transaction_type == "credit":
            if debit > 0:
                debit_balance = debit - amount
                if debit_balance < 0:
                    abs_debit_balance = abs(debit_balance)
                    customer_objects.update(opening_balance=abs_debit_balance)
                else:
                    customer_objects.update(opening_balance=debit_balance)
            else:
                customer_objects.update(opening_balance=credit+amount)

        elif transaction_type == "debit":
            if credit > 0:
                credit_balance = credit - amount
                if credit_balance < 0:
                    abs_credit_balance = abs(credit_balance)
                    customer_objects.update( opening_balance=abs_credit_balance)
                else:
                    customer_objects.update(opening_balance=credit_balance)
            else:
                customer_objects.update(opening_balance=debit+amount)
