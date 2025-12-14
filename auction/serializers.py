from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from user.models import Year, Gender, UserPhotos
from .models import (
    Role, Faculty, Major, Lot, Bid, Comment, Themes, Complaints
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class FacultySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(
            queryset=Faculty.objects.all(),
            message="Faculty with this name already exists."
        )]
    )

    class Meta:
        model = Faculty
        fields = ["id", "name"]


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ["id", "name", "faculty"]
        validators = [
            UniqueTogetherValidator(
                queryset=Major.objects.all(),
                fields=("name", "faculty"),
                message="This major already exists for the selected faculty."
            )
        ]


class ThemesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Themes
        fields = ["id", "name"]


class ComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaints
        fields = ["id", "user", "theme", "text"]


class LotSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    faculty = serializers.CharField(source='user.faculty.name', read_only=True)
    major = serializers.CharField(source='user.major.name', read_only=True, allow_null=True)
    year = serializers.CharField(source='user.year.year', read_only=True)
    gender = serializers.CharField(source='user.gender.gender', read_only=True)
    role = serializers.CharField(source='user.role.name', read_only=True, allow_null=True)
    soundcloud_url = serializers.URLField(source='user.soundcloud', read_only=True, allow_null=True)
    facebook_url = serializers.URLField(source='user.facebook', read_only=True, allow_null=True)
    instagram_url = serializers.URLField(source='user.instagram', read_only=True, allow_null=True)

    photos = serializers.SerializerMethodField()
    main_photo = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    lot_number = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Lot
        fields = [
            "id", "lot_number", "user", "created_at", "description", "last_bet",
            "first_name", "last_name", "faculty", "major", "year", "gender",
            "role", "soundcloud_url", "facebook_url", "instagram_url", "photos", "main_photo", "comments"
        ]
        read_only_fields = ["created_at", "user"]

    def get_first_name(self, obj):
        return obj.first_name

    def get_last_name(self, obj):
        return obj.last_name

    def get_photos(self, obj):
        request = self.context.get('request')
        photos = UserPhotos.objects.filter(user=obj.user)
        if request:
            return [request.build_absolute_uri(photo.photo.url) for photo in photos]
        return [photo.photo.url for photo in photos]

    def get_main_photo(self, obj):
        request = self.context.get('request')
        first_photo = UserPhotos.objects.filter(user=obj.user).order_by('created_at').first()

        if first_photo:
            if request:
                return request.build_absolute_uri(first_photo.photo.url)
            return first_photo.photo.url

        return None

    def get_comments(self, obj):
        comments = Comment.objects.filter(lot=obj).order_by('created_at')
        return [{
            'id': c.id,
            'user_name': f"{c.user.first_name} {c.user.last_name}",
            'text': c.text,
            'bid': c.bid.amount if c.bid else None,
            'created_at': c.created_at,
            'parent': c.parent_id
        } for c in comments]


class MyLotSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    lot_number = serializers.IntegerField(source='id', read_only=True)
    last_bet = serializers.IntegerField(read_only=True)
    photos = serializers.SerializerMethodField(read_only=True)
    photos_count = serializers.SerializerMethodField(read_only=True)
    can_upload_more = serializers.SerializerMethodField(read_only=True)

    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    faculty = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(),
        required=False
    )
    major = serializers.PrimaryKeyRelatedField(
        queryset=Major.objects.all(),
        allow_null=True,
        required=False
    )
    year = serializers.PrimaryKeyRelatedField(
        queryset=Year.objects.all(),
        required=False
    )
    gender = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(),
        required=False
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        allow_null=True,
        required=False
    )

    soundcloud_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    facebook_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    instagram_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    description = serializers.CharField(allow_blank=True, required=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['faculty'] = instance.user.faculty_id if instance.user.faculty else None
        representation['major'] = instance.user.major_id if instance.user.major else None
        representation['year'] = instance.user.year_id if instance.user.year else None
        representation['gender'] = instance.user.gender_id if instance.user.gender else None
        representation['role'] = instance.user.role_id if instance.user.role else None

        representation['first_name'] = instance.first_name
        representation['last_name'] = instance.last_name

        representation['soundcloud_url'] = instance.user.soundcloud
        representation['facebook_url'] = instance.user.facebook
        representation['instagram_url'] = instance.user.instagram

        representation['description'] = instance.description

        return representation

    def get_photos(self, obj):
        request = self.context.get('request')
        photos = UserPhotos.objects.filter(user=obj.user)
        if request:
            return [request.build_absolute_uri(photo.photo.url) for photo in photos]
        return [photo.photo.url for photo in photos]

    def get_photos_count(self, obj):
        return UserPhotos.objects.filter(user=obj.user).count()

    def get_can_upload_more(self, obj):
        count = UserPhotos.objects.filter(user=obj.user).count()
        return count < 5

    def validate(self, attrs):
        faculty = attrs.get('faculty')
        major = attrs.get('major')

        if self.instance:
            faculty = faculty or self.instance.user.faculty
            major = major if 'major' in attrs else self.instance.user.major

        if major and faculty and major.faculty_id != faculty.id:
            raise serializers.ValidationError(
                "Selected major does not belong to the chosen faculty."
            )

        return attrs

    def create(self, validated_data):
        user = self.context['user']

        display_first_name = validated_data.pop('first_name', '')
        display_last_name = validated_data.pop('last_name', '')

        user_fields = {
            'faculty': validated_data.pop('faculty', user.faculty),
            'major': validated_data.pop('major', user.major),
            'year': validated_data.pop('year', user.year),
            'gender': validated_data.pop('gender', user.gender),
            'role': validated_data.pop('role', user.role),
        }

        if 'soundcloud_url' in validated_data:
            user.soundcloud = validated_data.pop('soundcloud_url')
        if 'facebook_url' in validated_data:
            user.facebook = validated_data.pop('facebook_url')
        if 'instagram_url' in validated_data:
            user.instagram = validated_data.pop('instagram_url')

        for field, value in user_fields.items():
            if value is not None:
                setattr(user, field, value)
        user.save()

        lot = Lot.objects.create(
            user=user,
            display_first_name=display_first_name,
            display_last_name=display_last_name,
            **validated_data  # description, etc.
        )

        return lot

    def update(self, lot, validated_data):
        if 'first_name' in validated_data:
            lot.display_first_name = validated_data.pop('first_name')

        if 'last_name' in validated_data:
            lot.display_last_name = validated_data.pop('last_name')

        user = lot.user
        user_fields = ['faculty', 'major', 'year', 'gender', 'role']

        for field in user_fields:
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))

        if 'soundcloud_url' in validated_data:
            user.soundcloud = validated_data.pop('soundcloud_url')
        if 'facebook_url' in validated_data:
            user.facebook = validated_data.pop('facebook_url')
        if 'instagram_url' in validated_data:
            user.instagram = validated_data.pop('instagram_url')

        user.save()

        for attr, value in validated_data.items():
            setattr(lot, attr, value)

        lot.save()

        return lot


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ["id", "user", "lot", "amount"]

    def validate_amount(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be positive.")
        return value

    def validate(self, attrs):
        lot = attrs.get("lot") or getattr(self.instance, "lot", None)
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        if lot is None or amount is None:
            return attrs

        minimal_required = (lot.last_bet or 0) + 10
        if amount < minimal_required:
            raise serializers.ValidationError(
                f"Bid must be at least {minimal_required}. Current last bet: {lot.last_bet}."
            )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    ANTI_SPAM_MAX = 5
    ANTI_SPAM_WINDOW_MIN = 1

    class Meta:
        model = Comment
        fields = ["id", "user", "created_at", "text", "bid", "parent", "lot"]
        read_only_fields = ["created_at"]
        extra_kwargs = {
            'bid': {'required': False, 'allow_null': True},
            'text': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        lot = attrs.get("lot") or getattr(self.instance, "lot", None)
        bid = attrs.get("bid") or getattr(self.instance, "bid", None)
        parent = attrs.get("parent") or getattr(self.instance, "parent", None)
        user = attrs.get("user") or getattr(self.instance, "user", None)
        text = attrs.get("text", "")

        if not text and not bid:
            raise serializers.ValidationError("Either 'text' or 'bid' must be provided.")

        if bid and lot and bid.lot_id != lot.id:
            raise serializers.ValidationError("Selected bid does not belong to the provided lot.")

        if parent and lot and parent.lot_id != lot.id:
            raise serializers.ValidationError("Parent comment must belong to the same lot.")

        if user:
            window_start = timezone.now() - timedelta(minutes=self.ANTI_SPAM_WINDOW_MIN)
            recent_count = Comment.objects.filter(
                user=user,
                created_at__gte=window_start
            ).count()
            if recent_count >= self.ANTI_SPAM_MAX:
                raise serializers.ValidationError(
                    f"Rate limit exceeded: at most {self.ANTI_SPAM_MAX} comments per "
                    f"{self.ANTI_SPAM_WINDOW_MIN} minute(s)."
                )

        return attrs
