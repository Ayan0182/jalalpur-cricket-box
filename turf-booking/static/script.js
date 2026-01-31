const slotsDiv = document.getElementById("slots");
const datesDiv = document.getElementById("dates");
const bookingForm = document.getElementById("booking-form");

let selectedDate = null;
let selectedSlots = [];   // ✅ MULTIPLE SLOTS

const phoneInput = document.getElementById("phone");
const phoneError = document.getElementById("phone-error");
const confirmBtn = document.getElementById("confirmBtn");
const confirmModal = document.getElementById("confirmModal");
const mobileFooter = document.getElementById("mobileFooter");
const footerPrice = document.getElementById("footerPrice");

/* ================= INIT ================= */
if (confirmModal) confirmModal.style.display = "none";
if (mobileFooter) mobileFooter.style.display = "none";
footerPrice.innerText = "₹0";

/* ================= HELPERS ================= */
function isMobile() {
  return window.innerWidth <= 768;
}

function parseHour(timeStr) {
  const [time, meridian] = timeStr.split(" ");
  let hour = parseInt(time);
  if (meridian === "PM" && hour !== 12) hour += 12;
  if (meridian === "AM" && hour === 12) hour = 0;
  return hour;
}

function totalPrice() {
  return selectedSlots.reduce((sum, s) => sum + s.price, 0);
}

/* ================= PHONE INPUT ================= */
phoneInput.addEventListener("input", () => {
  phoneInput.value = phoneInput.value.replace(/\D/g, "");
  phoneError.style.display = "none";
});

/* ================= LOAD DATES ================= */
fetch("/dates")
  .then(r => r.json())
  .then(dates => {
    dates.forEach((d, i) => {
      const btn = document.createElement("button");
      btn.className = "date-btn";
      btn.innerText = d.label;

      btn.onclick = () => {
        document.querySelectorAll(".date-btn")
          .forEach(b => b.classList.remove("active"));

        btn.classList.add("active");
        selectedDate = d.date;

        selectedSlots = [];
        bookingForm.style.display = "none";
        document.getElementById("selected-slot-summary").style.display = "none";
        mobileFooter.style.display = "none";
        footerPrice.innerText = "₹0";

        loadSlots();
      };

      if (i === 0) {
        btn.classList.add("active");
        selectedDate = d.date;
      }

      datesDiv.appendChild(btn);
    });

    loadSlots();
  });

/* ================= LOAD SLOTS ================= */
function loadSlots() {
  slotsDiv.innerHTML = "<b>Loading slots...</b>";

  fetch(`/slots?date=${selectedDate}`)
    .then(r => r.json())
    .then(data => {
      slotsDiv.innerHTML = "";

      const currentHour = new Date().getHours();
      let available = 0, booked = 0;

      data.forEach(slot => {
        if (selectedDate === new Date().toISOString().split("T")[0]) {
          const h = parseHour(slot.time);
          const isNight = h >= 18 || h <= 2;
          if (!isNight && h < currentHour) return;
        }

        const div = document.createElement("div");

        if (slot.status !== "available") {
          div.className = "slot booked";
          booked++;
        } else {
          div.className = "slot available";
          available++;
          div.onclick = () => toggleSlot(slot, div);
        }

        div.innerHTML = `<div>${slot.time}</div><div>₹${slot.price}</div>`;
        slotsDiv.appendChild(div);
      });

      document.getElementById("slotCount").innerText =
        `Available: ${available} | Booked: ${booked}`;
    });
}

/* ================= SELECT / DESELECT ================= */
function toggleSlot(slot, el) {

  const index = selectedSlots.findIndex(s => s.id === slot.id);

  // ❌ DESELECT
  if (index !== -1) {
    selectedSlots.splice(index, 1);
    el.classList.remove("selected");
  }
  // ✅ SELECT
  else {
    selectedSlots.push(slot);
    el.classList.add("selected");
  }

  if (selectedSlots.length === 0) {
    bookingForm.style.display = "none";
    mobileFooter.style.display = "none";
    footerPrice.innerText = "₹0";
    document.getElementById("selected-slot-summary").style.display = "none";
    return;
  }

  // SUMMARY
  document.getElementById("selected-slot-summary").innerHTML =
    selectedSlots.map(s => `⏰ ${s.time} – ₹${s.price}`).join("<br>") +
    `<br><b>Total: ₹${totalPrice()}</b>`;

  document.getElementById("selected-slot-summary").style.display = "block";

  // PC
  if (!isMobile()) {
    bookingForm.style.display = "block";
    bookingForm.scrollIntoView({ behavior: "smooth" });
  }

  // MOBILE
  if (isMobile()) {
    footerPrice.innerText = "₹" + totalPrice();
    mobileFooter.style.display = "flex";
  }
}

/* ================= MOBILE BUTTON ================= */
function openBookingForm() {
  bookingForm.style.display = "block";
  bookingForm.scrollIntoView({ behavior: "smooth" });
}

/* ================= CONFIRM BOOKING ================= */
function confirmBooking() {
  const name = document.getElementById("name").value.trim();
  const phone = phoneInput.value.trim();

  if (!name) return alert("Enter name");
  if (!/^\d{10}$/.test(phone)) {
    phoneError.style.display = "block";
    return;
  }
  if (selectedSlots.length === 0) return alert("Select slot(s)");

  confirmBtn.disabled = true;
  confirmBtn.innerText = "Confirming...";

  fetch("/confirm-booking", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      phone,
      slot_ids: selectedSlots.map(s => s.id)
    })
  })
    .then(r => r.json())
    .then(d => {
      if (d.success) confirmModal.style.display = "flex";
      else alert("Booking failed");
    });
}

function closeModal() {
  confirmModal.style.display = "none";
  location.reload();
}
