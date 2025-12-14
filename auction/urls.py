from django.urls import path

from auction import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='homepage'),
    path('mylot/', views.MyLot.as_view(), name='my_lot'),
    path('mylot/upload-photo/', views.UploadLotPhoto.as_view(), name='upload_lot_photo'),
    path('lots/<int:pk>/', views.LotDetail.as_view(), name='lot_detail'),
    path('contacts/', views.Feedback.as_view(), name='feedback'),
    path('profile/', views.Profile.as_view(), name='profile'),
    path('profile/upload-photo/', views.UploadProfilePhoto.as_view(), name='upload_profile_photo'),
    path('rules/', views.Rules.as_view(), name='rules'),
    path('complaints/', views.ComplaintsList.as_view(), name='complaints'),
    path('complaints/<int:pk>/', views.ComplaintDetail.as_view(), name='complaint'),
    path('mybids/', views.MyBids.as_view(), name='my_bids'),
    path('faculties/', views.FacultyList.as_view(), name='faculty-list'),
    path('majors/', views.MajorList.as_view(), name='major-list'),
    path('roles/', views.RoleList.as_view(), name='role-list'),
    path('years/', views.YearList.as_view(), name='year-list'),
    path('genders/', views.GenderList.as_view(), name='gender-list'),
]
