from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from .models import (
    Role, Faculty, Major, Lot, Bid, Comment, MyBids, Themes, Complaints
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class FacultySerializer(serializers.ModelSerializer):
    # unique faculty name
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
    class Meta:
        model = Lot
        fields = ["id", "user", "created_at", "description", "last_bet"]
        read_only_fields = ["created_at"]
        extra_kwargs = {
            "last_bet": {"min_value": 0},
        }


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
    ANTI_SPAM_MAX = 5         # allowed comments per window
    ANTI_SPAM_WINDOW_MIN = 1  # window in minutes

    class Meta:
        model = Comment
        fields = ["id", "user", "created_at", "text", "bid", "parent", "lot"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        lot = attrs.get("lot") or getattr(self.instance, "lot", None)
        bid = attrs.get("bid") or getattr(self.instance, "bid", None)
        parent = attrs.get("parent") or getattr(self.instance, "parent", None)
        user = attrs.get("user") or getattr(self.instance, "user", None)

        # bid must belong to the same lot
        if bid and lot and bid.lot_id != lot.id:
            raise serializers.ValidationError("Selected bid does not belong to the provided lot.")
        # parent must belong to the same lot
        if parent and lot and parent.lot_id != lot.id:
            raise serializers.ValidationError("Parent comment must belong to the same lot.")

        # anti-spam  window
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


class MyBidsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyBids
        fields = ["id", "user", "lot", "bid"]
        validators = [
            UniqueTogetherValidator(
                queryset=MyBids.objects.all(),
                fields=("user", "lot"),
                message="This user already has a bid record for this lot."
            )
        ]

    def validate(self, attrs):
        lot = attrs.get("lot") or getattr(self.instance, "lot", None)
        bid = attrs.get("bid") or getattr(self.instance, "bid", None)
        if bid and lot and bid.lot_id != lot.id:
            raise serializers.ValidationError("The selected bid must belong to the same lot.")
        return attrs
