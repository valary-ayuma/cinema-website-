from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404, redirect

from .models import Theater, Movie, Showtime, Seat, Booking, BookingSeat, Payment
from .serializers import (
    TheaterSerializer, MovieSerializer, ShowtimeSerializer,
    SeatMapEntrySerializer, BookingSerializer, CreateBookingSerializer,
    PaymentSerializer,
)

# ==================== WEB FRONTEND VIEWS ====================

def landing_page_view(request):
    """Renders the main landing page listing available movies and theaters."""
    movies = Movie.objects.all()
    theaters = Theater.objects.all()
    
    # Optional filter parameters
    selected_theater_id = request.GET.get('theater')
    selected_movie_id = request.GET.get('movie')
    
    showtimes = Showtime.objects.select_related("movie", "screen", "screen__theater").filter(
        start_time__gte=timezone.now()
    )
    
    if selected_theater_id:
        showtimes = showtimes.filter(screen__theater_id=selected_theater_id)
    if selected_movie_id:
        showtimes = showtimes.filter(movie_id=selected_movie_id)

    context = {
        "movies": movies,
        "theaters": theaters,
        "showtimes": showtimes[:15],
        "selected_theater": int(selected_theater_id) if selected_theater_id else None,
        "selected_movie": int(selected_movie_id) if selected_movie_id else None,
    }
    return render(request, "booking/landing.html", context)


def seat_map_view(request, showtime_id):
    """Renders the seat map selection page for a specific showtime."""
    showtime = get_object_or_404(Showtime.objects.select_related("movie", "screen__theater"), id=showtime_id)
    return render(request, "booking/seat_map.html", {"showtime": showtime})


def my_bookings_view(request):
    """Shows the currently logged-in user's bookings."""
    if not request.user.is_authenticated:
        return redirect("/admin/login/?next=/my-bookings/")

    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related(
            "showtime",
            "showtime__movie",
            "showtime__screen",
            "showtime__screen__theater",
            "payment",
        )
        .prefetch_related(
            "seats",
            "seats__seat",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "booking/my_bookings.html",
        {
            "bookings": bookings,
        },
    )

    


# ==================== API VIEWSETS ====================

class TheaterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Theater.objects.all()
    serializer_class = TheaterSerializer
    permission_classes = [permissions.AllowAny]


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]


class ShowtimeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShowtimeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Showtime.objects.select_related("movie", "screen", "screen__theater")
        movie_id = self.request.query_params.get("movie")
        theater_id = self.request.query_params.get("theater")
        if movie_id:
            qs = qs.filter(movie_id=movie_id)
        if theater_id:
            qs = qs.filter(screen__theater_id=theater_id)
        return qs.filter(start_time__gte=timezone.now())


def _release_expired_holds(showtime):
    expired = Booking.objects.filter(
        showtime=showtime,
        status=Booking.Status.PENDING,
        expires_at__lt=timezone.now(),
    )
    for booking in expired:
        booking.seats.all().delete()
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])


class SeatMapView(APIView):
    """GET /api/showtimes/<id>/seatmap/ -- full seat layout with availability."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, showtime_id):
        try:
            showtime = Showtime.objects.select_related("screen").get(id=showtime_id)
        except Showtime.DoesNotExist:
            return Response({"detail": "Showtime not found."}, status=404)

        _release_expired_holds(showtime)

        taken_seat_ids = set(
            BookingSeat.objects.filter(showtime=showtime).values_list("seat_id", flat=True)
        )
        seats = Seat.objects.filter(screen=showtime.screen)
        data = [
            {
                "id": s.id,
                "row_label": s.row_label,
                "number": s.number,
                "seat_type": s.seat_type,
                "price": showtime.seat_price(s),
                "is_available": s.id not in taken_seat_ids,
            }
            for s in seats
        ]
        return Response(SeatMapEntrySerializer(data, many=True).data)


class CreateBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        showtime_id = serializer.validated_data["showtime_id"]
        seat_ids = serializer.validated_data["seat_ids"]

        try:
            showtime = Showtime.objects.get(id=showtime_id)
        except Showtime.DoesNotExist:
            return Response({"detail": "Showtime not found."}, status=404)

        seats = list(Seat.objects.filter(id__in=seat_ids, screen=showtime.screen))
        if len(seats) != len(seat_ids):
            return Response({"detail": "One or more seats are invalid for this showtime."}, status=400)

        try:
            with transaction.atomic():
                locked_existing = list(
                    BookingSeat.objects.select_for_update().filter(
                        showtime=showtime, seat_id__in=seat_ids
                    )
                )
                if locked_existing:
                    taken = [bs.seat_id for bs in locked_existing]
                    return Response(
                        {"detail": "Some seats were just taken.", "seat_ids": taken},
                        status=status.HTTP_409_CONFLICT,
                    )

                total = sum(showtime.seat_price(s) for s in seats)
                booking = Booking.objects.create(
                    user=request.user,
                    showtime=showtime,
                    status=Booking.Status.PENDING,
                    total_price=total,
                    expires_at=timezone.now() + settings.SEAT_HOLD_DURATION,
                )
                BookingSeat.objects.bulk_create([
                    BookingSeat(booking=booking, showtime=showtime, seat=s, price=showtime.seat_price(s))
                    for s in seats
                ])
        except IntegrityError:
            return Response(
                {"detail": "Some seats were just taken. Please pick again."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related("showtime")


class ConfirmPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.select_related("payment").get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

        if booking.is_expired():
            booking.seats.all().delete()
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status"])
            return Response({"detail": "This hold has expired. Please select seats again."}, status=410)

        if booking.status != Booking.Status.PENDING:
            return Response({"detail": f"Booking is already {booking.status}."}, status=400)

        provider_ref = request.data.get("provider_ref", "")
        Payment.objects.update_or_create(
            booking=booking,
            defaults={
                "amount": booking.total_price,
                "status": Payment.Status.SUCCEEDED,
                "provider_ref": provider_ref,
            },
        )
        booking.status = Booking.Status.CONFIRMED
        booking.expires_at = None
        booking.save(update_fields=["status", "expires_at"])
        return Response(BookingSerializer(booking).data)