from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("theaters", views.TheaterViewSet, basename="theater")
router.register("movies", views.MovieViewSet, basename="movie")
router.register("showtimes", views.ShowtimeViewSet, basename="showtime")
router.register("bookings", views.BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    path("showtimes/<int:showtime_id>/seatmap/", views.SeatMapView.as_view(), name="seatmap"),
    path("bookings/create/", views.CreateBookingView.as_view(), name="create-booking"),
    path("bookings/<int:booking_id>/confirm-payment/", views.ConfirmPaymentView.as_view(), name="confirm-payment"),
]
