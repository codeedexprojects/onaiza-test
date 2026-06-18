from django.contrib.auth.models import User, Group


def create_user_of_vendor(username, password):
    user_data = User.objects.create_user(
        username = username,
        password = password,
        is_active = True,
    )

    group = Group.objects.get(name="vendor_user")
    user_data.groups.add(group)

    return user_data
