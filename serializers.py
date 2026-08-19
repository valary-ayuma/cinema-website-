from rest_framework import serializers
from .models import Theater, Screen, Seat, Movie, Showtime, Booking, BookingSeat, Payment


class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = ["id", "name", "address", "city"]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "row_label", "number", "seat_type"]


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "duration_minutes", "rating", "description", "poster_url"]


class ShowtimeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    theater_name = serializers.CharField(source="screen.theater.name", read_only=True)
    screen_name = serializers.CharField(source="screen.name", read_only=True)

    class Meta:
        model = Showtime
        fields = [
            "id", "movie", "theater_name", "screen_name",
            "start_time", "end_time", "base_price",
        ]


class SeatMapEntrySerializer(serializers.Serializer):
    """One seat, annotated with its price for this showtime and whether it's taken."""
    id = serializers.IntegerField()
    row_label = serializers.CharField()
    number = serializers.IntegerField()
    seat_type = serializers.CharField()
    price = serializers.FloatField()
    is_available = serializers.BooleanField()


class BookingSeatSerializer(serializers.ModelSerializer):
    seat = SeatSerializer(read_only=True)

    class Meta:
        model = BookingSeat
        fields = ["id", "seat", "price"]


class BookingSerializer(serializers.ModelSerializer):
    seats = BookingSeatSerializer(many=True, read_only=True)
    showtime = ShowtimeSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "showtime", "status", "total_price", "created_at", "expires_at", "seats"]


class CreateBookingSerializer(serializers.Serializer):
    """Input for POST /bookings/ -- select seats for a showtime."""
    showtime_id = serializers.IntegerField()
    seat_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1, max_length=12)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "booking", "amount", "status", "provider", "provider_ref", "created_at"]



class BookingSerializer(serializers.ModelSerializer):
    seats = BookingSeatSerializer(many=True, read_only=True)
    showtime = ShowtimeSerializer(read_only=True)
    payment_status = serializers.SerializerMethodField()
    payment_provider = serializers.SerializerMethodField()
    payment_reference = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "showtime",
            "status",
            "total_price",
            "created_at",
            "expires_at",
            "seats",
            "payment_status",
            "payment_provider",
            "payment_reference",
        ]

    def get_payment_status(self, obj):
        try:
            return obj.payment.status
        except Payment.DoesNotExist:
            return None

    def get_payment_provider(self, obj):
        try:
            return obj.payment.provider
        except Payment.DoesNotExist:
            return None

    def get_payment_reference(self, obj):
        try:
            return obj.payment.provider_ref
        except Payment.DoesNotExist:
            return None