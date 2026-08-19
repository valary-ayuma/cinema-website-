# Movie Booking System — Backend

Django + Django REST Framework API for a movie reservation/booking system.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Postgres must be running and reachable via the DB_* env vars below,
# or point them at your own instance.
export DB_NAME=moviebooking DB_USER=postgres DB_PASSWORD=postgres DB_HOST=localhost

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin panel: http://localhost:8000/admin/ — add Theaters, Screens, Seats, Movies, Showtimes here first.

## Background worker (seat hold expiry)

Requires Redis running locally (`redis-server`).

```bash
celery -A moviebooking worker -l info
celery -A moviebooking beat -l info   # schedules release_expired_holds periodically
```

Without this running, expired holds are still cleaned up lazily whenever the seat map
or booking endpoints are hit for that showtime — but the worker is what cleans up
showtimes nobody is actively looking at.

## API overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/movies/` | GET | List movies |
| `/api/showtimes/?movie=<id>&theater=<id>` | GET | List upcoming showtimes |
| `/api/showtimes/<id>/seatmap/` | GET | Full seat layout + availability + price |
| `/api/bookings/create/` | POST | `{showtime_id, seat_ids: [...]}` — holds seats, returns booking (pending) |
| `/api/bookings/<id>/confirm-payment/` | POST | Called after payment succeeds — confirms booking |
| `/api/bookings/` | GET | Current user's bookings |

Auth: DRF token auth. Get a token via `/api-auth/login/` in dev, or issue one via
`rest_framework.authtoken` for real clients.

## Concurrency model (why nobody double-books a seat)

1. `POST /api/bookings/create/` opens a DB transaction and takes a row lock
   (`select_for_update`) on any existing seat rows for that showtime before
   inserting new ones — concurrent requests for the same seat serialize
   instead of racing.
2. A DB-level unique constraint on `(showtime, seat)` is the backstop: even
   if the locking logic is ever wrong, the database itself refuses a
   duplicate, and the API returns `409 Conflict`.
3. A booking starts as `pending` with an `expires_at` (default 8 min). If
   payment isn't confirmed in time, the hold is released — either lazily
   (next time that showtime's seat map is read) or by the Celery sweep.

## Payments

`ConfirmPaymentView` is written to be called from your payment provider's
webhook (e.g. Stripe `payment_intent.succeeded`), not directly by the
client — wire up `stripe.Webhook.construct_event(...)` there before going
to production. The current version trusts `provider_ref` from the request
body, which is fine for local development only.

## Not yet included (next steps for a production launch)

- Payment provider webhook signature verification
- Rate limiting / throttling on booking creation
- Email/SMS confirmation on booking
- Refund/cancellation flow
- Search/filtering on movies (genre, showing today, etc.)
