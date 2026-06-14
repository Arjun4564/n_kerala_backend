from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
        ]

    def validate(self, data):
        # Password match check
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "password": "Passwords do not match"
            })

        # Username uniqueness check
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                "username": "Username already taken"
            })

        # Email uniqueness (optional but recommended)
        if data.get('email') and User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                "email": "Email already registered"
            })

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'full_name',
            'first_name',
            'last_name',
            'email',
        ]

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username