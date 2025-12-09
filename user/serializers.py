from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Year, Gender, CustomUser
from auction.models import Role, Faculty, Major


class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ["id", "year"]


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ["id", "gender"]


class CustomUserSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    gender = serializers.PrimaryKeyRelatedField(queryset=Gender.objects.all())
    faculty = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    major = serializers.PrimaryKeyRelatedField(queryset=Major.objects.all(), allow_null=True, required=False)
    year = serializers.PrimaryKeyRelatedField(queryset=Year.objects.all(), allow_null=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name", "last_name",
            "role", "gender", "faculty", "major", "year",
            "created_at", "updated_at",
            "profile_pic",
            "facebook", "instagram", "discord_id", "soundcloud",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_first_name(self, value):
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("First name cannot be empty.")
        return v

    def validate_last_name(self, value):
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Last name cannot be empty.")
        return v

    def validate(self, attrs):
        faculty = attrs.get("faculty") or getattr(self.instance, "faculty", None)
        # if major is explicitly present in this request, use it; else fall back to instance
        major = attrs.get("major") if "major" in attrs else getattr(self.instance, "major", None)

        if major and faculty and major.faculty_id != faculty.id:
            raise serializers.ValidationError("Selected major does not belong to the chosen faculty.")
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    confirm_password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate_email(self, value):
        if not value.endswith("@ukma.edu.ua"):
            raise serializers.ValidationError("На жаль, реєстрація можлива лише через корпоративну пошту НаУКМА.")

        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Користувач з цією поштою вже зареєстрований!')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Паролі не збігаються!')
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user, created = CustomUser.objects.get_or_create(email=validated_data['email'],
                                                         defaults={
                                                             'first_name': validated_data['first_name'],
                                                             'last_name': validated_data['last_name'],
                                                             'email': validated_data['email'],
                                                         })
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Дані некоректні!')
        attrs['user'] = user
        return attrs
