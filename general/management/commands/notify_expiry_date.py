from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import F, Count
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from users.models import NotificationSubject, Notification
from general.models import Batch
from products.models import Product, ProductVariant


class Command(BaseCommand):

    def handle(self, *args, **options):
        today = datetime.now().date()

        users = User.objects.filter(is_superuser=True, is_active=True)
        batches = Batch.objects.filter(stock__gt=0, is_deleted=False)
        notification_subject = NotificationSubject.objects.get(code='batch_expiry_date_reached')

        expired_batches = batches.filter(expire_date__lt=today)

        if expired_batches.exists():
            message = f"{expired_batches.count()} products has been expired"

            for user in users:
                Notification.objects.create(
                    is_active = True,
                    subject = notification_subject,
                    user = user,
                    message = message,
                    time = datetime.now()
                )

        expiring_batches = batches.none()

        # products = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True)
        # for product in products:
        #     expiry_limit = today + timedelta(days=product.expiry_dates_limit)
        #     expiring_batches |= batches.filter(product=product, expire_date__range=[today, expiry_limit])

        if expiring_batches.exists():
            message = f"{expiring_batches.count()} products are expiring soon"

            for user in users:
                Notification.objects.create(
                    is_active = True,
                    subject = notification_subject,
                    user = user,
                    message = message,
                    time = datetime.now()
                )

        notification_subject = NotificationSubject.objects.get(code='product_low_stock')

        # products = Product.objects.filter(is_deleted=False, stock__lt=F('low_stock_limit'))
        variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, stock__lt=F('low_stock_limit'))

        if variants.exists():
            total_count = variants.count()
            message = f"{total_count} products are low in stock"

            for user in users:
                Notification.objects.create(
                    is_active = True,
                    subject = notification_subject,
                    user = user,
                    message = message,
                    time = datetime.now()
                )
