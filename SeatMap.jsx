import { useEffect, useMemo, useState } from "react";
import { getSeatMap, createBooking } from "./api.js";

// Used only if the API isn't reachable yet, so the component still renders
// something real during frontend development.
const MOCK_SEATS = (() => {
  const rows = ["A", "B", "C", "D", "E", "F"];
  const seats = [];
  let id = 1;
  rows.forEach((row, rowIdx) => {
    const type = rowIdx >= 4 ? "recliner" : rowIdx >= 2 ? "premium" : "standard";
    const price = rowIdx >= 4 ? 18.5 : rowIdx >= 2 ? 14 : 11;
    for (let n = 1; n <= 10; n++) {
      seats.push({
        id: id++,
        row_label: row,
        number: n,
        seat_type: type,
        price,
        is_available: Math.random() > 0.18,
      });
    }
  });
  return seats;
})();

const SEAT_STYLES = {
  standard: "border-house-800/60 bg-house-800",
  premium: "border-marquee-500/40 bg-house-800",
  recliner: "border-velvet-500/50 bg-house-800",
};

function Seat({ seat, selected, onToggle }) {
  if (!seat.is_available) {
    return (
      <div
        className="w-7 h-7 rounded-t-md border border-house-800/40 bg-house-900/40"
        title={`${seat.row_label}${seat.number} — taken`}
      />
    );
  }
  return (
    <button
      onClick={() => onToggle(seat)}
      title={`${seat.row_label}${seat.number} — $${seat.price.toFixed(2)}`}
      className={`w-7 h-7 rounded-t-md border transition-all duration-150
        ${selected ? "bg-marquee-400 border-marquee-400 shadow-[0_0_10px_rgba(240,192,90,0.7)] scale-110" : SEAT_STYLES[seat.seat_type]}
        hover:scale-105 hover:border-marquee-400/70`}
    />
  );
}

export default function SeatMap({ showtimeId, showtimeLabel = "Tonight, 7:30 PM · Screen 3" }) {
  const [seats, setSeats] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [booking, setBooking] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getSeatMap(showtimeId)
      .then((data) => !cancelled && setSeats(data))
      .catch(() => !cancelled && setSeats(MOCK_SEATS)) // dev fallback
      .finally(() => !cancelled && setLoading(false));
    return () => (cancelled = true);
  }, [showtimeId]);

  const rows = useMemo(() => {
    const byRow = {};
    seats.forEach((s) => {
      byRow[s.row_label] = byRow[s.row_label] || [];
      byRow[s.row_label].push(s);
    });
    return Object.entries(byRow).sort(([a], [b]) => a.localeCompare(b));
  }, [seats]);

  const selectedSeats = seats.filter((s) => selected.has(s.id));
  const total = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  function toggle(seat) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(seat.id)) next.delete(seat.id);
      else if (next.size < 8) next.add(seat.id);
      return next;
    });
  }

  async function handleReserve() {
    setError(null);
    try {
      const result = await createBooking(showtimeId, [...selected]);
      setBooking(result);
    } catch (err) {
      if (err.status === 409) {
        setError("Someone just grabbed one of those seats — pick again.");
        setSelected(new Set());
        getSeatMap(showtimeId).then(setSeats).catch(() => {});
      } else {
        setError("Couldn't reserve those seats. Please try again.");
      }
    }
  }

  if (loading) {
    return <div className="text-house-800 font-body text-sm p-8">Loading seats…</div>;
  }

  if (booking) {
    return (
      <div className="max-w-sm mx-auto bg-house-900 border border-marquee-500/30 rounded-lg p-6 font-body text-screen-glow">
        <p className="font-display text-3xl tracking-wide text-marquee-400 mb-1">Reserved</p>
        <p className="text-sm text-house-800/80 mb-4">
          Seats held for 8 minutes — complete payment to confirm.
        </p>
        <ul className="text-sm space-y-1 mb-4">
          {booking.seats?.map((bs) => (
            <li key={bs.id} className="flex justify-between">
              <span>{bs.seat.row_label}{bs.seat.number}</span>
              <span>${Number(bs.price).toFixed(2)}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between font-semibold border-t border-house-800 pt-3">
          <span>Total</span>
          <span>${Number(booking.total_price).toFixed(2)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="font-body max-w-2xl mx-auto text-screen-glow">
      <div className="text-center mb-2">
        <p className="font-display text-2xl tracking-wider text-marquee-400">{showtimeLabel}</p>
      </div>

      {/* Signature element: the glowing curved screen */}
      <div className="relative h-6 mb-8 mx-8">
        <div
          className="absolute inset-x-0 top-0 h-full rounded-b-[100%] bg-screen-glow/90"
          style={{ boxShadow: "0 0 40px 8px rgba(253,246,227,0.35)" }}
        />
        <p className="absolute inset-x-0 -bottom-5 text-center text-[10px] tracking-[0.3em] text-house-800/70 uppercase">
          Screen
        </p>
      </div>

      <div className="space-y-2 mb-6">
        {rows.map(([rowLabel, rowSeats]) => (
          <div key={rowLabel} className="flex items-center gap-2 justify-center">
            <span className="w-4 text-xs text-house-800/60 text-right font-medium">{rowLabel}</span>
            <div className="flex gap-1.5">
              {rowSeats.map((seat) => (
                <Seat key={seat.id} seat={seat} selected={selected.has(seat.id)} onToggle={toggle} />
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-center gap-6 text-xs text-house-800/70 mb-6">
        <Legend swatch="bg-house-800 border-house-800/60" label="Standard" />
        <Legend swatch="bg-house-800 border-marquee-500/40" label="Premium" />
        <Legend swatch="bg-house-800 border-velvet-500/50" label="Recliner" />
        <Legend swatch="bg-marquee-400 border-marquee-400" label="Selected" />
        <Legend swatch="bg-house-900/40 border-house-800/40" label="Taken" />
      </div>

      {error && (
        <p className="text-velvet-500 text-sm text-center mb-3">{error}</p>
      )}

      {/* Ticket-stub style summary bar */}
      <div className="flex items-stretch bg-house-900 border border-house-800 rounded-lg overflow-hidden">
        <div className="flex-1 p-4">
          <p className="text-xs uppercase tracking-widest text-house-800/60">
            {selectedSeats.length} seat{selectedSeats.length !== 1 ? "s" : ""} selected
          </p>
          <p className="font-display text-xl text-marquee-400">${total.toFixed(2)}</p>
        </div>
        <button
          onClick={handleReserve}
          disabled={selectedSeats.length === 0}
          className="px-6 font-display tracking-wide text-lg bg-velvet-500 disabled:bg-house-800 disabled:text-house-800/40 hover:bg-velvet-600 transition-colors"
        >
          Reserve
        </button>
      </div>
    </div>
  );
}

function Legend({ swatch, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`w-3 h-3 rounded-sm border ${swatch}`} />
      {label}
    </div>
  );
}
