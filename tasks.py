from celery import shared_task
from django.utils import timezone
from .models import Booking


@shared_task
def release_expired_holds():
    """
    Runs on a schedule (wire up via django-celery-beat, e.g. every minute)
    to release seats from abandoned checkouts. This is the safety net --
    the API also does an inline sweep per-showtime on read/write, but this
    catches holds for showtimes nobody happens to be looking at right now.
    """
    expired = Booking.objects.filter(
        status=Booking.Status.PENDING,
        expires_at__lt=timezone.now(),
    )
    count = 0
    for booking in expired:
        booking.seats.all().delete()
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        count += 1
    return f"Released {count} expired booking(s)."
