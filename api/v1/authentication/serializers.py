from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from six import text_type
from django.contrib.auth.models import User
# from users.models import UserDetails


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(UserTokenObtainPairSerializer, cls).get_token(user)
        return token

    def validate(cls, attrs):
        data = super(UserTokenObtainPairSerializer, cls).validate(attrs)

        refresh = cls.get_token(cls.user)

        data['refresh'] = text_type(refresh)
        data['access'] = text_type(refresh.access_token)

        roles = list(set([x.name for x in cls.user.groups.all()]))
        if 'app_user' in roles:
            data['role'] = "app_user"

        elif cls.user.is_superuser:
            data['role'] = "superuser"
            data['StatusCode'] = 6000
        else:
            data['role'] = "user"
            data['phone'] = cls.user.username
            data['otp'] = cls.user.password
            data['StatusCode'] = 6000

        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username',
            'password'
        )

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.save()
        return user
