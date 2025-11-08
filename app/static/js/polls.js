console.log("✅ polls.js geladen!");

async function loadArtists() {
  try {
    const res = await fetch("/api/artists");
    const data = await res.json();

    const container = document.getElementById("pollContainer");
    container.innerHTML = "";

    if (!data || data.length === 0) {
      container.innerHTML = "<p>Nog geen artiesten ontvangen.</p>";
      return;
    }

    data.forEach(a => {
      const div = document.createElement("div");
      div.classList.add("form-check", "text-start", "d-inline-block", "mx-2");
      div.innerHTML = `
        <input class="form-check-input" type="radio" name="artist" value="${a.id}">
        <label class="form-check-label">${a.Artist_name}</label>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    console.error("⚠️ Fout bij ophalen artiesten:", err);
  }
}

async function submitVote() {
  const selected = document.querySelector('input[name="artist"]:checked');
  if (!selected) {
    alert("Kies eerst een artiest!");
    return;
  }

  const formData = new URLSearchParams();
  formData.append("artist_id", selected.value);

  const res = await fetch("/vote", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (res.ok) {
    window.location.href = "/results";
  } else {
    alert("Er ging iets mis bij het opslaan van je stem.");
  }
}

window.onload = loadArtists;
window.submitVote = submitVote;

