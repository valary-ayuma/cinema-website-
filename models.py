from django.conf import settings
from django.db import models
from django.utils import timezone


class Theater(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.city})"


class Screen(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name="screens")
    name = models.CharField(max_length=50)  # e.g. "Screen 3", "IMAX"

    class Meta:
        unique_together = ("theater", "name")

    def __str__(self):
        return f"{self.theater.name} - {self.name}"


class Seat(models.Model):
    class SeatType(models.TextChoices):
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"
        RECLINER = "recliner", "Recliner"

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="seats")
    row_label = models.CharField(max_length=2)   # "A", "B", ...
    number = models.PositiveIntegerField()        # 1, 2, 3, ...
    seat_type = models.CharField(max_length=20, choices=SeatType.choices, default=SeatType.STANDARD)

    class Meta:
        unique_together = ("screen", "row_label", "number")
        ordering = ["row_label", "number"]

    def __str__(self):
        return f"{self.row_label}{self.number}"


class Movie(models.Model):
    title = models.CharField(max_length=200)
    duration_minutes = models.PositiveIntegerField()
    rating = models.CharField(max_length=10, blank=True)  # e.g. PG-13
    description = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)

    def __str__(self):
        return self.title


class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="showtimes")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["start_time"]
        # A screen can't run two showtimes that overlap.
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "start_time"], name="unique_screen_start_time"
            )
        ]

    def __str__(self):
        return f"{self.movie.title} @ {self.start_time:%Y-%m-%d %H:%M} ({self.screen})"

    def seat_price(self, seat: Seat):
        multiplier = {"standard": 1.0, "premium": 1.4, "recliner": 1.8}[seat.seat_type]
        return round(float(self.base_price) * multiplier, 2)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending payment"      # seats held, not yet paid
        CONFIRMED = "confirmed", "Confirmed"          # paid, seats locked in
        CANCELLED = "cancelled", "Cancelled"          # expired hold or user-cancelled


    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name="bookings")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # Only meaningful while status == pending. After this, the hold can be released.
    expires_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return (
            self.status == self.Status.PENDING
            and self.expires_at is not None
            and timezone.now() > self.expires_at
        )

    def __str__(self):
        return f"Booking #{self.id} - {self.user} - {self.showtime}"


class BookingSeat(models.Model):
    """
    One row per seat in a booking. The unique constraint below is what
    actually prevents double-booking at the database level -- application
    logic (transactions + row locks) prevents the race, this constraint
    is the backstop if that logic is ever wrong or bypassed.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="seats")
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name="booked_seats")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="bookings")
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        constraints = [
            # A given seat can only be held/booked once per showtime,
            # REGARDLESS of which booking it's attached to.
            models.UniqueConstraint(fields=["showtime", "seat"], name="unique_seat_per_showtime"),
        ]

    def __str__(self):
        return f"{self.seat} - {self.showtime}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=50, default="stripe")
    provider_ref = models.CharField(max_length=200, blank=True)  # e.g. Stripe PaymentIntent ID
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for booking #{self.booking_id} - {self.status}"
