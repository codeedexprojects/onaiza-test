from main.functions import get_current_role
from users.models import Notification


def main_context(request):
    current_role = get_current_role(request)
    user_type = 'User'

    if current_role == 'superadmin':
        user_type = 'Admin User'
    elif current_role == 'vendor_user':
        user_type = 'Vendor User'
    elif current_role == 'customer_user':
        user_type = 'Customer User'

    user = request.user
    user_id = None
    if user.is_authenticated:
        user_id = user.pk

    is_wishlist_item = True
    user_notifications = Notification.objects.none()
    notifications_count = 0

    if user.is_authenticated:
        user_notifications = Notification.objects.filter(is_deleted=False, is_active=True, is_read=False, user=request.user)
        notifications_count = user_notifications.count()

    user_notifications = user_notifications[:9] # to pass only the latest 9 notifications to frontend

    return {
        'current_role': current_role,
        'user_type': user_type,
        'user_id': user_id,
        'notifications_count':notifications_count,
        "user_notifications": user_notifications,
    }
