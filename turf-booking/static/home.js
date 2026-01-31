document.addEventListener("DOMContentLoaded", () => {

  const skeleton = document.getElementById("availabilitySkeleton");
  const realBox = document.getElementById("availabilityReal");

  fetch("/home-availability")
    .then(res => res.json())
    .then(data => {

      // hide skeleton
      if (skeleton) skeleton.style.display = "none";

      // show real data
      if (realBox) realBox.classList.remove("hidden");

      const avail = document.getElementById("availCount");
      const booked = document.getElementById("bookedCount");

      if (avail && booked) {
        avail.innerText = `🟢 ${data.available} Slots Available`;
        booked.innerText = `🔴 ${data.booked} Slots Booked`;
      }
    })
    .catch(() => {
      console.log("Availability fetch failed");
    });
});
