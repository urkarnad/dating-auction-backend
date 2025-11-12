from django.urls import path

from auction import views
urlpatterns = [
    path('', views.HomePage.as_view(), name='homepage'),
    path('mylot/', views.MyLot.as_view(), name='my_lot'),
    path('lots/<int:pk>/', views.LotDetail.as_view(), name='lot_detail'),
    path('contacts/', views.Feedback.as_view(), name='feedback'),
    path('profile/', views.Profile.as_view(), name='profile'),
    path('rules/', views.Rules.as_view(), name='rules'),
    path('complaints/', views.ComplaintsList.as_view(), name='complaints'),
    path('complaints/<int:pk>/', views.ComplaintDetail.as_view(), name='complaint'),
    path('mybids/', views.MyBids.as_view(), name='my_bids'),
]
