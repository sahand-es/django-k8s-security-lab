const $ = (id) => document.getElementById(id);
const text = (id, v) => $(id).textContent = v;

const SAFE_TARGETS = new Set(["api", "worker", "database", "scheduler"]);

async function getJson(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function loadWorkspace() {
  const data = await getJson("/api/targets/");
  text("user", data.user);
  $("avatar").textContent = data.user.slice(0, 2).toUpperCase();
  text("shift", data.shift);
  text("role", "on-call shadow");

  const chips = $("target-chips");
  chips.replaceChildren();
  data.targets.forEach((t) => {
    const el = document.createElement("span");
    el.className = "chip";
    el.innerHTML = `<span class="chip-dot"></span>${t}`;
    chips.appendChild(el);
  });

  const sel = $("target-select");
  sel.replaceChildren();
  data.targets.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    sel.appendChild(opt);
  });
}

$("diag-button").addEventListener("click", async () => {
  const target = $("target-select").value;
  if (!SAFE_TARGETS.has(target)) {
    $("diag-output").textContent = "The console only runs diagnostics for known service targets.";
    return;
  }
  try {
    const data = await getJson(`/api/diag/run/?target=${encodeURIComponent(target)}`);
    $("diag-output").textContent = `${data.preview}\n— ${data.note}`;
  } catch (e) {
    $("diag-output").textContent = e.message;
  }
});

$("url-button").addEventListener("click", async () => {
  const raw = $("url-input").value.trim();
  if (!/^https?:\/\/[A-Za-z0-9._:\/-]+$/.test(raw)) {
    $("url-output").textContent = "The console only sends test payloads to plain http(s) URLs.";
    return;
  }
  try {
    const data = await getJson(`/webhooks/test/?url=${encodeURIComponent(raw)}`);
    $("url-output").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    $("url-output").textContent = e.message;
  }
});

loadWorkspace().catch((e) => {
  $("diag-output").textContent = e.message;
});
