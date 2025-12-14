from django.db.models import Q, Max
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from auction.models import Lot, Complaints, Faculty, Major, Role, Bid, Comment
from auction.serializers import LotSerializer, BidSerializer, CommentSerializer, ComplaintsSerializer, \
    FacultySerializer, MajorSerializer, RoleSerializer, MyLotSerializer
from notifications.services import notification_service
from user.models import UserPhotos
from user.serializers import CustomUserSerializer
from user.permissions import NotBanned


class NotBannedMixin:
    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), NotBanned()]
        return [IsAuthenticated()]


class LotPagination(PageNumberPagination):
    page_size = 12                       
    page_size_query_param = "page_size"  
    max_page_size = 100  


class HomePage(APIView):
    def get(self, request):
        lots = Lot.objects.all().order_by("-created_at")

        search_query = request.query_params.get('search')
        if search_query:
            lots = lots.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        faculty = request.query_params.get('faculty')
        gender = request.query_params.get('gender')
        year = request.query_params.get('year')
        has_photo = request.query_params.get('has_photo')
        role = request.query_params.get('role')

        if faculty:
            lots = lots.filter(user__faculty_id=faculty)
        if gender:
            lots = lots.filter(user__gender=gender)
        if year:
            lots = lots.filter(user__year=year)
        if role:
            lots = lots.filter(user__role=role)
        if has_photo == 'true':
            lots = lots.exclude(user__photo='')

        sort_param = request.query_params.get('sort')
        if sort_param == 'price_asc':
            lots = lots.order_by('last_bet')
        elif sort_param == 'price_desc':
            lots = lots.order_by('-last_bet')
        elif sort_param == 'created_at_asc':
            lots = lots.order_by('created_at')
        elif sort_param == 'created_at_desc':
            lots = lots.order_by('-created_at')

        paginator = LotPagination()
        page_qs = paginator.paginate_queryset(lots, request, view=self)

        serializer = LotSerializer(page_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyLot(NotBannedMixin, APIView):
    def get(self, request):
        user = request.user
        my_lot = Lot.objects.filter(user=user).first()

        if not my_lot:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MyLotSerializer(my_lot, context={'request': request})
        data = serializer.data

        lot_serializer = LotSerializer(my_lot, context={'request': request})
        data['comments'] = lot_serializer.data.get('comments', [])
        return Response(data)

    def post(self, request):
        user = request.user

        text = request.data.get('text')
        parent_id = request.data.get('parent')

        if text is not None or parent_id is not None:
            my_lot = Lot.objects.filter(user=user).first()

            if not my_lot:
                return Response(
                    {"detail": "у вас немає лоту."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not text:
                return Response(
                    {"detail": "текст обов'язковий."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            actual_parent_id = None
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, lot=my_lot)
                    if parent_comment.parent_id is not None:
                        actual_parent_id = parent_comment.parent_id
                        replied_to_user = parent_comment.user
                        text = f"@{replied_to_user.first_name} {replied_to_user.last_name}: {text}"
                    else:
                        actual_parent_id = parent_id
                except Comment.DoesNotExist:
                    return Response(
                        {"detail": "коментар не знайдено."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            comment_data = {
                "user": user.id,
                "lot": my_lot.id,
                "text": text,
            }

            if actual_parent_id:
                comment_data["parent"] = actual_parent_id

            comment_serializer = CommentSerializer(data=comment_data)
            comment_serializer.is_valid(raise_exception=True)
            comment_serializer.save()

            return Response(
                {"detail": "коментар успішно додано."},
                status=status.HTTP_201_CREATED
            )

        if Lot.objects.filter(user=user).exists():
            return Response({"detail": "ви можете створити лише 1 лот."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = MyLotSerializer(data=request.data, context={'user': user})

        if serializer.is_valid():
            lot = serializer.save()
            return Response(MyLotSerializer(lot).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        my_lot = Lot.objects.filter(user=user).first()

        if not my_lot:
            return Response(
                {"detail": "ви ще не створювали лот."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MyLotSerializer(my_lot, data=request.data, context={'user': user})

        if serializer.is_valid():
            lot = serializer.save()
            return Response(MyLotSerializer(lot).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        my_lot = Lot.objects.filter(user=user).first()

        if not my_lot:
            return Response(
                {"detail": "ви ще не створювали лот."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MyLotSerializer(my_lot, data=request.data, partial=True, context={'user': user})

        if serializer.is_valid():
            lot = serializer.save()
            return Response(MyLotSerializer(lot).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadLotPhoto(NotBannedMixin, APIView):
    # permission_classes = [IsAuthenticated], це перекриває Mixin

    def post(self, request):
        user = request.user
        my_lot = Lot.objects.filter(user=user).first()

        if not my_lot:
            return Response(
                {"detail": "спочатку створіть лот."},
                status=status.HTTP_404_NOT_FOUND
            )

        current_photos_count = UserPhotos.objects.filter(user=user).count()

        photos = request.FILES.getlist('photo')

        if not photos:
            return Response(
                {"detail": "фото не надано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_photos_count + len(photos) > 5:
            return Response(
                {"detail": f"Максимум 5 фото. У вас вже {current_photos_count} фото."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_urls = []
        for photo in photos:
            user_photo = UserPhotos.objects.create(user=user, photo=photo)
            uploaded_urls.append(request.build_absolute_uri(user_photo.photo.url))

        return Response(
            {
                "detail": f"успішно завантажено {len(photos)} фото.",
                "photos": uploaded_urls,
                "total_photos": current_photos_count + len(photos)
            },
            status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        """Видалення конкретного фото"""
        user = request.user
        photo_id = request.data.get('photo_id')

        if not photo_id:
            return Response(
                {"detail": "вкажіть photo_id для видалення."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            photo = UserPhotos.objects.get(id=photo_id, user=user)
            photo.delete()
            return Response(
                {"detail": "фото успішно видалено."},
                status=status.HTTP_204_NO_CONTENT
            )
        except UserPhotos.DoesNotExist:
            return Response(
                {"detail": "фото не знайдено."},
                status=status.HTTP_404_NOT_FOUND
            )


class UploadProfilePhoto(NotBannedMixin, APIView):
    def post(self, request):
        user = request.user
        photo = request.FILES.get('photo')

        if not photo:
            return Response(
                {"detail": "фото не надано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.profile_pic:
            user.profile_pic.delete(save=False)

        user.profile_pic = photo
        user.save()

        return Response(
            {
                "detail": "аватарка успішно оновлена.",
                "photo_url": request.build_absolute_uri(user.profile_pic.url)
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        user = request.user

        if not user.profile_pic:
            return Response(
                {"detail": "у вас немає аватарки."},
                status=status.HTTP_404_NOT_FOUND
            )

        user.profile_pic.delete(save=False)
        user.profile_pic = None
        user.save()

        return Response(
            {"detail": "аватарка успішно видалена."},
            status=status.HTTP_204_NO_CONTENT
        )


class LotDetail(NotBannedMixin, APIView):
    def get_object(self, pk):
        try:
            return Lot.objects.get(pk=pk)
        except Lot.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        lot = self.get_object(pk)
        serializer = LotSerializer(lot)
        return Response(serializer.data)

    def post(self, request, pk):
        lot = self.get_object(pk)
        user = request.user

        amount = request.data.get('amount')
        text = request.data.get('text')
        parent_id = request.data.get('parent')

        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, lot=lot)

                if parent_comment.parent_id is not None:
                    actual_parent_id = parent_comment.parent_id
                    replied_to_user = parent_comment.user
                    text = f"@{replied_to_user.first_name} {replied_to_user.last_name}: {text}"
                else:
                    actual_parent_id = parent_id

            except Comment.DoesNotExist:
                return Response(
                    {"detail": "коментар для відповіді не знайдено."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if amount:
                return Response(
                    {"detail": "не можна залишати ставку у відповіді на коментар."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            comment_data = {
                "user": user.id,
                "lot": lot.id,
                "text": text,
                "parent": actual_parent_id
            }
            comment_serializer = CommentSerializer(data=comment_data)
            comment_serializer.is_valid(raise_exception=True)
            comment_serializer.save()

            return Response(
                {"detail": "відповідь успішно додано."},
                status=status.HTTP_201_CREATED
            )

        # for discord
        previous_bid = Bid.objects.filter(lot=lot).order_by('-amount').first()

        if amount:
            bid_data = {"user": user.id, "lot": lot.id, "amount": amount}
            bid_serializer = BidSerializer(data=bid_data)
            bid_serializer.is_valid(raise_exception=True)
            bid = bid_serializer.save()

            # for discord
            bid.is_overbid = False
            bid.save(update_fields=['is_overbid'])

            Bid.objects.filter(lot=lot, is_overbid=False).exclude(id=bid.id).update(is_overbid=True)

            lot.last_bet = bid.amount
            lot.save(update_fields=["last_bet"])

            # send notification
            if previous_bid:
                notification_service.notify_bid_overbid_sync(previous_bid=previous_bid, new_bid=bid, lot=lot)

            if text:
                comment_data = {
                    "user": user.id,
                    "lot": lot.id,
                    "text": text,
                    "bid": bid.id
                }
                comment_serializer = CommentSerializer(data=comment_data)
                comment_serializer.is_valid(raise_exception=True)
                comment_serializer.save()
            return Response(
                {"detail": "ставку успішно додано."},
                status=status.HTTP_201_CREATED
            )

        elif text:
            comment_data = {"user": user.id, "lot": lot.id, "text": text}
            comment_serializer = CommentSerializer(data=comment_data)
            comment_serializer.is_valid(raise_exception=True)
            comment_serializer.save()

            return Response(
                {"detail": "коментар успішно доданий."},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"detail": "напишіть текст або вкажіть ставку."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        lot = self.get_object(pk)

        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {"detail": "у вас немає дозволу на видалення лоту."},
                status=status.HTTP_403_FORBIDDEN
            )
        lot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Feedback(NotBannedMixin, APIView):
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        message = request.data.get("message")

        return Response({"details": "Your feedback has been sent."}, status=status.HTTP_200_OK)


class Profile(NotBannedMixin, APIView):
    def get(self, request):
        serializer = CustomUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        serializer = CustomUserSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = CustomUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class Rules(APIView):
    # temporary rules, later we will append html page
    def get(self, request):
        return Response({
            "rules": [
                "1. No cheating",
                "2. No harassment",
                "3. No spam"
            ]
        })


class ComplaintsList(APIView):
    def get(self, request):
        if not request.user.is_staff or not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        complaints = Complaints.objects.all()
        serializer = ComplaintsSerializer(complaints, many=True)
        return Response(serializer.data)


class ComplaintDetail(NotBannedMixin, APIView):
    def post(self, request, pk):
        data = {
            "user": request.user.id,
            "theme": pk,
            "text": request.data.get("text")
        }
        serializer = ComplaintsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyBids(NotBannedMixin, APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get("status")

        latest_bids_subquery = Bid.objects.filter(
            user=request.user
        ).values('lot').annotate(
            max_id=Max('id')
        ).values('max_id')

        bids = Bid.objects.filter(
            id__in=latest_bids_subquery
        ).select_related('lot', 'lot__user').order_by('-created_at')

        if status_filter == "overbid":
            bids = bids.filter(is_overbid=True)
        elif status_filter == "active":
            bids = bids.filter(is_overbid=False)

        data = []
        for bid in bids:
            data.append({
                'id': bid.id,
                'amount': bid.amount,
                'created_at': bid.created_at,
                'is_overbid': bid.is_overbid,
                'lot': bid.lot.id,
                'lot_info': {
                    'id': bid.lot.id,
                    'lot_number': bid.lot.id,
                    'first_name': bid.lot.first_name,
                    'last_name': bid.lot.last_name,
                    'current_bet': bid.lot.last_bet,
                }
            })

        return Response(data)


class FacultyList(APIView):
    def get(self, request):
        faculties = Faculty.objects.all()
        serializer = FacultySerializer(faculties, many=True)
        return Response(serializer.data)


class MajorList(APIView):
    def get(self, request):
        faculty_id = request.query_params.get('faculty')

        if faculty_id:
            majors = Major.objects.filter(faculty_id=faculty_id)
        else:
            majors = Major.objects.all()

        serializer = MajorSerializer(majors, many=True)
        return Response(serializer.data)


class RoleList(APIView):
    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)


class YearList(APIView):
    def get(self, request):
        from user.models import Year
        from user.serializers import YearSerializer

        years = Year.objects.all()
        serializer = YearSerializer(years, many=True)
        return Response(serializer.data)


class GenderList(APIView):
    def get(self, request):
        from user.models import Gender
        from user.serializers import GenderSerializer

        genders = Gender.objects.all()
        serializer = GenderSerializer(genders, many=True)
        return Response(serializer.data)
