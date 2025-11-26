from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from auction.models import Lot, Complaints, MyBids
from auction.serializers import LotSerializer, BidSerializer, CommentSerializer, ComplaintsSerializer, MyBidsSerializer
from user.serializers import CustomUserSerializer

class LotPagination(PageNumberPagination):
    page_size = 10                       
    page_size_query_param = "page_size"  
    max_page_size = 100  

class HomePage(APIView):
    def get(self, request):
        lots = Lot.objects.all()

        search_query = request.query_params.get('search')
        if search_query:
            lots = lots.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        faculty = request.query_params.get('faculty')
        gender = request.query_params.get('gender')
        year = request.query_params.get('year')
        has_photo = request.query_params.get('has_photo')
        role = request.query_params.get('role')

        if faculty:
            lots = lots.filter(faculty=faculty)
        if gender:
            lots = lots.filter(gender=gender)
        if year:
            lots = lots.filter(year=year)
        if role:
            lots = lots.filter(role=role)
        if has_photo == 'true':
            lots = lots.exclude(photo='')

        sort_param = request.query_params.get('sort')
        if sort_param == 'price_asc':
            lots = lots.order_by('price')
        elif sort_param == 'price_desc':
            lots = lots.order_by('-price')
        elif sort_param == 'created_at_asc':
            lots = lots.order_by('created_at')
        elif sort_param == 'created_at_desc':
            lots = lots.order_by('-created_at')

        paginator = LotPagination()
        page_qs = paginator.paginate_queryset(lots, request, view=self)

        serializer = LotSerializer(page_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyLot(APIView):
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
            return Response({"detail": "You can create only 1 lot."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = LotSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        my_lot = Lot.objects.filter(owner=user).first()

        if not my_lot:
            return Response(
                {"detail": "You don't have any created lot."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LotSerializer(my_lot, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        my_lot = Lot.objects.filter(owner=user).first()

        if not my_lot:
            return Response(
                {"detail": "You don't have any created lot."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LotSerializer(my_lot, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LotDetail(APIView):
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
                {"detail": "Bid successfully placed."},
                status=status.HTTP_201_CREATED
            )

        elif text:
            comment_data = {"user": user.id, "lot": lot.id, "text": text}
            comment_serializer = CommentSerializer(data=comment_data)
            comment_serializer.is_valid(raise_exception=True)
            comment_serializer.save()

            return Response(
                {"detail": "Comment successfully added."},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"detail": "Provide at least text or amount."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        lot = self.get_object(pk)

        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {"detail": "You don't have permission to delete this lot."},
                status=status.HTTP_403_FORBIDDEN
            )
        lot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Feedback(APIView):
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        message = request.data.get("message")

        return Response({"details": "Your feedback has been sent."}, status=status.HTTP_200_OK)


class Profile(APIView):
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


class ComplaintDetail(APIView):
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


class MyBids(APIView):
    def get(self, request):
        status_filter = request.query_params.get("status")

        bids = MyBids.objects.filter(user=request.user)

        if status_filter == "overbid":
            bids = bids.filter(is_overbid=True)
        elif status_filter == "active":
            bids = bids.filter(is_overbid=False)

        serializer = MyBidsSerializer(bids, many=True)
        return Response(serializer.data)
