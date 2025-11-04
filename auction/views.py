from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auction.models import Lot


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
            lots = lots.order_by('date')
        elif sort_param == 'created_at_desc':
            lots = lots.order_by('-date')

        # there will be serializer when we merge branches

        return ...


class MyLot(APIView):
    def get(self, request):
        user = request.user
        my_lot = Lot.objects.filter(owner=user).first()

        if not my_lot:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # there will be serializer
        return ...

