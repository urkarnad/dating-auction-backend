from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from auction.models import Lot, Complaints, Faculty, Major, Role, Bid
from auction.serializers import LotSerializer, BidSerializer, CommentSerializer, ComplaintsSerializer, \
    FacultySerializer, MajorSerializer, RoleSerializer, MyLotSerializer
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
        lots = Lot.objects.all()

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

        serializer = LotSerializer(my_lot)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
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

        photo = request.FILES.get('photo')
        if not photo:
            return Response(
                {"detail": "фото не надано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_photo = UserPhotos.objects.create(user=user, photo=photo)

        return Response(
            {
                "detail": "фото успішно завантажено.",
                "photo_url": request.build_absolute_uri(user_photo.photo.url)
            },
            status=status.HTTP_201_CREATED
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

        if amount:
            bid_data = {"user": user.id, "lot": lot.id, "amount": amount}
            bid_serializer = BidSerializer(data=bid_data)
            bid_serializer.is_valid(raise_exception=True)
            bid = bid_serializer.save()

            Bid.objects.filter(lot=lot, is_overbid=False).exclude(id=bid.id).update(is_overbid=True)

            lot.last_bet = bid.amount
            lot.save(update_fields=["last_bet"])

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
            {"detail": "напишіть текст або кількість."},
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
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = CustomUserSerializer(
            request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = CustomUserSerializer(
            request.user,
            data=request.data,
            partial=True
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

        bids = Bid.objects.filter(user=request.user).select_related('lot', 'lot__user')

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
