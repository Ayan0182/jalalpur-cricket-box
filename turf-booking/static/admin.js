// ================= ADMIN SUMMARY =================
fetch("/admin/summary")
  .then(res => res.json())
  .then(data => {
    document.getElementById("today-count").innerText = data.today;
    document.getElementById("tomorrow-count").innerText = data.tomorrow;
    document.getElementById("weekend-count").innerText = data.weekend;
    document.getElementById("revenue-count").innerText = "₹" + data.revenue;
  });

// ================= LOAD BOOKINGS TABLE =================
let allBookings = [];

// ================= LOAD BOOKINGS TABLE =================
fetch("/admin/bookings")
  .then(res => res.json())
  .then(data => {
    allBookings = data;
    renderTable(data);
  });

function renderTable(data) {
  const table = document.getElementById("bookingTable");
  table.innerHTML = "";

  data.forEach(b => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${b.name}</td>
      <td>${b.phone}</td>
      <td>${b.date}</td>
      <td>${b.day}</td>
      <td>${b.time}</td>
      <td>₹${b.price}</td>
      <td>${b.status}</td>
      <td>
        ${
          b.status === "confirmed"
            ? `<button onclick="cancelBooking(${b.booking_id})">Cancel</button>`
            : "-"
        }
      </td>
    `;

    table.appendChild(tr);
  });
}


// ================= CANCEL BOOKING =================
function cancelBooking(id) {
  if (!confirm("Cancel this booking?")) return;

  fetch("/admin/cancel-booking", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ booking_id: id })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Booking cancelled");
        location.reload();
      }
    });
}

// ============================= Change PAssword =============================


document.getElementById("searchInput").addEventListener("input", function () {
  const value = this.value.toLowerCase();

  const filtered = allBookings.filter(b =>
    b.name.toLowerCase().includes(value) ||
    b.phone.includes(value)
  );

  renderTable(filtered);
});
