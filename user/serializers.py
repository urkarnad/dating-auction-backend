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
            "profile_pic", "photo",
            "facebook", "instagram", "discord", "soundcloud",
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
