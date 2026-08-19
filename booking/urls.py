from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# ---- DRF router for the read-only viewsets ----
router = DefaultRouter()
router.register(r"theaters", views.TheaterViewSet, basename="theater")
router.register(r"movies", views.MovieViewSet, basename="movie")
router.register(r"showtimes", views.ShowtimeViewSet, basename="showtime")
router.register(r"bookings", views.BookingViewSet, basename="booking")

urlpatterns = [
    # ---- Web frontend pages ----
    path("", views.landing_page_view, name="landing_page"),
    path("showtimes/<int:showtime_id>/seats/", views.seat_map_view, name="seat_map"),

    # ---- API: custom endpoints (must come BEFORE router.urls, otherwise
    # the router's "bookings/<pk>/" pattern greedily matches
    # "bookings/create/" with pk="create" and routes POST to the
    # read-only BookingViewSet, which only allows GET -> 405 error) ----
    path("api/showtimes/<int:showtime_id>/seatmap/", views.SeatMapView.as_view(), name="seatmap"),
    path("api/bookings/create/", views.CreateBookingView.as_view(), name="create_booking"),
    path("api/bookings/<int:booking_id>/confirm/", views.ConfirmPaymentView.as_view(), name="confirm_payment"),

    # ---- API: router-based read-only endpoints ----
    # e.g. /api/theaters/, /api/movies/, /api/showtimes/, /api/bookings/
    path("api/", include(router.urls)),

    path(
    "my-bookings/",
    views.my_bookings_view,
    name="my_bookings",
),
]
