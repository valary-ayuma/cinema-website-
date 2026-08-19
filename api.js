const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function authHeaders() {
  const token = localStorage.getItem("authToken");
  return token ? { Authorization: `Token ${token}` } : {};
}

export async function getSeatMap(showtimeId) {
  const res = await fetch(`${BASE_URL}/showtimes/${showtimeId}/seatmap/`);
  if (!res.ok) throw new Error("Failed to load seat map");
  return res.json();
}

export async function createBooking(showtimeId, seatIds) {
  const res = await fetch(`${BASE_URL}/bookings/create/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ showtime_id: showtimeId, seat_ids: seatIds }),
  });
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.detail || "Booking failed");
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export async function confirmPayment(bookingId, providerRef) {
  const res = await fetch(`${BASE_URL}/bookings/${bookingId}/confirm-payment/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ provider_ref: providerRef }),
  });
  if (!res.ok) throw new Error("Payment confirmation failed");
  return res.json();
}
