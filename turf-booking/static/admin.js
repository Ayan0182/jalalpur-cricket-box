// ================= ADMIN SUMMARY =================
fetch("/admin/summary")
  .then(res => res.json())
  .then(data => {
    document.getElementById("today-count").innerText = data.today;
    document.getElementById("tomorrow-count").innerText = data.tomorrow;
    document.getElementById("weekend-count").innerText = data.weekend;
    document.getElementById("revenue-count").innerText = "₹" + data.revenue;
  });

// ================= LOAD BOOKINGS =================
let allBookings = [];

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

    let actionBtn = "-";

    if (b.status === "confirmed") {
      actionBtn = `<button onclick="cancelBooking(${b.booking_id})">Cancel</button>`;
    } 
    else if (b.status === "cancelled") {
      actionBtn = `<button onclick="deleteBooking(${b.booking_id})" style="background:crimson">Delete</button>`;
    }

    tr.innerHTML = `
      <td>${b.name}</td>
      <td>${b.phone}</td>
      <td>${b.date}</td>
      <td>${b.day}</td>
      <td>${b.time}</td>
      <td>₹${b.price}</td>
      <td>${b.status}</td>
      <td>${actionBtn}</td>
    `;

    table.appendChild(tr);
  });
}

// ================= CANCEL =================
function cancelBooking(id) {
  const ok = confirm("Cancel this booking?");
  if (!ok) return;

  fetch("/admin/cancel-booking", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ booking_id: id })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      location.reload();   // ❌ no extra alert
    }
  });
}

// ================= DELETE =================
function deleteBooking(id) {
  fetch("/admin/delete-booking", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ booking_id: id })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      location.reload();   // no popup at all
    }
  });
}

// ================= SEARCH =================
document.getElementById("searchInput").addEventListener("input", function () {
  const value = this.value.toLowerCase();

  const filtered = allBookings.filter(b =>
    b.name.toLowerCase().includes(value) ||
    b.phone.includes(value)
  );

  renderTable(filtered);
});

