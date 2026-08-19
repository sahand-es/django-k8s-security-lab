const state = {
  queueId: null,
  allowedTicketIds: new Set(),
};

const $ = (id) => document.getElementById(id);
const text = (id, v) => $(id).textContent = v;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function ticketBadges(ticket) {
  let html = "";
  if (ticket.staff_only) {
    html += `<span class="badge badge-staff">STAFF</span> `;
  }
  html += `<span class="badge badge-open">OPEN</span>`;
  return html;
}

function renderTicketList(tickets) {
  const list = $("ticket-list");
  list.replaceChildren();
  if (!tickets.length) {
    list.innerHTML = `<div class="ticket-item"><span class="ttitle" style="color:var(--muted)">No tickets assigned.</span></div>`;
    return;
  }
  tickets.forEach((t) => {
    state.allowedTicketIds.add(t.id);
    const el = document.createElement("div");
    el.className = "ticket-item";
    el.innerHTML = `
      <span class="badge badge-p2">P2</span>
      <span class="tid">#${t.id}</span>
      <span class="ttitle">${escapeHtml(t.title)}</span>
      <span class="badge badge-open">OPEN</span>
    `;
    list.appendChild(el);
  });
}

function renderTicketDetail(ticket) {
  if (ticket.error) {
    $("ticket-output").textContent = ticket.error;
    return;
  }
  const p0 = ticket.staff_only ? `<span class="badge badge-p0">P0</span>` : `<span class="badge badge-p2">P2</span>`;
  const staff = ticket.staff_only ? `<span class="badge badge-staff">STAFF</span>` : "";
  const handover = ticket.handover_url
    ? `<a class="handover-link" href="${ticket.handover_url}">→ Staff handover</a>`
    : "";
  $("ticket-output").innerHTML = `
    <div class="ticket-detail">
      <div class="ticket-detail-header">
        ${p0} ${staff}
        <span class="tid">#${ticket.id}</span>
        <span class="ttitle">${escapeHtml(ticket.title)}</span>
      </div>
      <p class="summary">${escapeHtml(ticket.summary)}</p>
      <div class="body">${escapeHtml(ticket.body)}</div>
      ${handover}
    </div>
  `;
}

function renderSearchResults(data) {
  const out = $("search-output");
  $("search-count").textContent = `${data.results.length} result${data.results.length === 1 ? "" : "s"}`;
  if (!data.results.length) {
    out.innerHTML = `<span style="color:var(--muted);font-style:italic">No matches.</span>`;
    return;
  }
  out.innerHTML = data.results.map((t) => `
    <div class="ticket-item" style="margin-bottom:6px">
      ${t.title.includes("P0") ? `<span class="badge badge-p0">P0</span>` : `<span class="badge badge-p2">P2</span>`}
      <span class="tid">#${t.id}</span>
      <span class="ttitle">${escapeHtml(t.title)}</span>
    </div>
    <div style="font-size:12px;color:var(--muted);margin:-2px 0 8px 42px">${escapeHtml(t.summary)}</div>
  `).join("");
}

async function getJson(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function loadWorkspace() {
  const session = await getJson("/api/session/");
  state.queueId = session.queue.id;
  text("user", session.user);
  $("avatar").textContent = session.user.slice(0, 2).toUpperCase();
  text("queue-name", session.queue.name);
  text("queue-squad", session.queue.squad);
  text("queue-id", session.queue.id);

  const queue = await getJson(`/api/queues/${session.queue.id}/`);
  text("queue-note", queue.note);
  renderTicketList(queue.tickets);

  const sel = $("ticket-select");
  sel.replaceChildren();
  queue.tickets.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = String(t.id);
    opt.textContent = `#${t.id} — ${t.title}`;
    sel.appendChild(opt);
  });
}

$("search-button").addEventListener("click", async () => {
  const input = $("search-input");
  const q = input.value.replace(/[^a-zA-Z0-9 -]/g, "").slice(0, 40);
  input.value = q;
  try {
    const data = await getJson(`/api/tickets/search/?q=${encodeURIComponent(q)}`);
    renderSearchResults(data);
  } catch (e) {
    $("search-output").textContent = e.message;
  }
});

$("preview-button").addEventListener("click", async () => {
  const id = Number($("ticket-select").value);
  if (!state.allowedTicketIds.has(id)) {
    $("ticket-output").textContent = "The frontend only opens tickets assigned to this intern.";
    return;
  }
  try {
    const ticket = await getJson(`/api/tickets/${id}/`);
    renderTicketDetail(ticket);
  } catch (e) {
    $("ticket-output").textContent = e.message;
  }
});

loadWorkspace().catch((e) => {
  $("ticket-output").textContent = e.message;
});
