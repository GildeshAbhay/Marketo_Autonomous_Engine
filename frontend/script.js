// frontend/script.js - minimal frontend to talk to FastAPI backend
const sendBtn = document.getElementById("sendBtn");
const historyBtn = document.getElementById("historyBtn");
const resultEl = document.getElementById("result");

sendBtn.addEventListener("click", async () => {
  const mode = document.getElementById("mode").value;
  const command = document.getElementById("command").value.trim();
  const payloadText = document.getElementById("payload").value.trim();
  let payload = null;
  if (payloadText) {
    try {
      payload = JSON.parse(payloadText);
    } catch (e) {
      resultEl.textContent = "Payload JSON parse error: " + e.message;
      return;
    }
  }

  if (!command) {
    resultEl.textContent = "Please enter a command or prompt.";
    return;
  }

  resultEl.textContent = "Sending...";
  sendBtn.disabled = true;

  try {
    const endpoint = mode === "query" ? "/query" : "/action";
    const body = { command, payload };
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultEl.textContent = "Network error: " + (err && err.message);
  } finally {
    sendBtn.disabled = false;
  }
});

historyBtn.addEventListener("click", async () => {
  resultEl.textContent = "Fetching history...";
  try {
    const resp = await fetch("/history");
    const data = await resp.json();
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultEl.textContent = "History fetch error: " + (err && err.message);
  }
});
