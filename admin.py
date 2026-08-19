from django.contrib import admin
from .models import Theater, Screen, Seat, Movie, Showtime, Booking, BookingSeat, Payment


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "address"]
    search_fields = ["name", "city"]


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ["name", "theater"]
    inlines = [SeatInline]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "duration_minutes", "rating"]
    search_fields = ["title"]


@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ["movie", "screen", "start_time", "end_time", "base_price"]
    list_filter = ["screen__theater", "movie"]


class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "showtime", "status", "total_price", "created_at", "expires_at"]
    list_filter = ["status"]
    inlines = [BookingSeatInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["booking", "amount", "status", "provider", "created_at"]
