// --------- Supabase verbinding ----------
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// Jouw Supabase projectgegevens
const supabaseUrl = 'https://pwvyxvgwntypsbyuhkwa.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3dnl4dmd3bnR5cHNieXVoa3dhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA4OTUxMTQsImV4cCI6MjA3NjQ3MTExNH0.k__cCybqrTeEyZeDo9XD-Bz0Mzw-HR4MXdFgwJg8CLM';

// Maak Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

console.log("✅ polls.js is geladen!");
console.log("🌍 Supabase URL:", supabaseUrl);
console.log("🔑 Supabase key begint met:", supabaseKey.slice(0, 10));

// --------- Testverbinding ----------
async function testConnection() {
  const { data, error } = await supabase.from('Artists').select('*').limit(3);
  if (error) console.error("⚠️ Error:", error.message);
  else console.log("🎵 Test data ontvangen van Supabase:", data);
}
testConnection();


// --------- Artiesten ophalen en tonen ----------
async function loadArtists() {
  try {
    const { data, error } = await supabase
      .from("Artists")
      .select("id, Artist_name");

    if (error) throw error;

    console.log("🎵 Artiesten geladen:", data);

    const container = document.getElementById("pollContainer");
    container.innerHTML = "";

    if (!data || data.length === 0) {
      container.innerHTML = "<p>Nog geen suggesties ontvangen.</p>";
      return;
    }

    // Tel frequentie van artiesten en haal top 3
    const counts = {};
    data.forEach(a => {
      const name = a.Artist_name.trim().toLowerCase();
      counts[name] = (counts[name] || 0) + 1;
    });

    const sortedNames = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([name]) => name);

    // Unieke artiesten met id ophalen
    const topArtists = sortedNames.map(name =>
      data.find(a => a.Artist_name.toLowerCase() === name)
    );

    // Toon artiesten
    topArtists.forEach(artist => {
      const div = document.createElement("div");
      div.classList.add("form-check", "text-start", "d-inline-block", "mx-2");
      div.innerHTML = `
        <input class="form-check-input" type="radio" name="artist" value="${artist.id}">
        <label class="form-check-label">${artist.Artist_name}</label>
      `;
      container.appendChild(div);
    });

  } catch (err) {
    console.error("⚠️ Fout bij ophalen artiesten:", err);
  }
}


// --------- Mooie pop-up functie ----------
function showPopup(message, type = "success") {
  const popup = document.createElement("div");
  popup.innerHTML = `
    <div style="
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999;
      animation: fadeIn 0.3s ease-out;
    ">
      <div style="
        background: white;
        padding: 30px 40px;
        border-radius: 20px;
        text-align: center;
        font-family: 'Georgia', serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        max-width: 350px;
      ">
        <h4 style="color: ${type === 'success' ? '#0a6847' : '#b30000'};">
          ${type === 'success' ? '🎉 Bedankt voor je stem!' : '⚠️ Er ging iets mis'}
        </h4>
        <p style="margin-top: 10px; color: #444;">${message}</p>
        <button style="
          margin-top: 20px;
          background: ${type === 'success' ? '#0a6847' : '#b30000'};
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          cursor: pointer;
        ">OK</button>
      </div>
    </div>
  `;
  document.body.appendChild(popup);
  const button = popup.querySelector("button");
  button.addEventListener("click", () => popup.remove());
}


// --------- Stem opslaan functie ----------
async function submitVote() {
  const selected = document.querySelector('input[name="artist"]:checked');

  if (!selected) {
    showPopup("Kies eerst een artiest om te stemmen!", "error");
    return;
  }

  const artistId = selected.value;
  console.log("🎯 Gestemde artiest ID:", artistId);

  const { data, error } = await supabase
    .from("Votes_for")
    .insert([{ polloption_id: parseInt(artistId), user_id: null }]);

  if (error) {
    console.error("⚠️ Fout bij opslaan stem:", error);
    showPopup("Er ging iets mis bij het opslaan van je stem.", "error");
  } else {
    console.log("✅ Stem opgeslagen:", data);
    showPopup("Je stem is goed ontvangen. Dankjewel voor je deelname!", "success");
  }
}


// 👇 Maak de functie beschikbaar in HTML
window.submitVote = submitVote;

// --- Auto laden bij opstart ---
loadArtists();
