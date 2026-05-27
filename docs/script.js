const API_BASE = "http://127.0.0.1:8000";

let taskModal;
let logSocket = null;

// ───────────────────────────── init ─────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    taskModal = new bootstrap.Modal(document.getElementById("taskModal"));

    loadAccountsDropdown();
    loadAccountsTable();
    loadTasks();
    refreshSchedulerStatus();
    refreshSystemStatus();
    connectLogsWebSocket();

    setInterval(() => {
        loadTasks();
        refreshSchedulerStatus();
        refreshSystemStatus();
    }, 10000);
});

// ───────────────────────────── tasks ────────────────────────────

async function loadTasks() {
    const res = await fetch(`${API_BASE}/tasks`);
    const tasks = await res.json();

    const filterAccount = document.getElementById("accountFilter").value;
    const tbody = document.getElementById("taskTableBody");
    tbody.innerHTML = "";

    tasks
        .filter(t => !filterAccount || t.account_label === filterAccount)
        .forEach(task => {
            const timeStr = `${task.hour}:${String(task.minute).padStart(2, "0")}:${String(task.second).padStart(2, "0")} ${task.ampm}`;
            const enabledBadge = task.enabled
                ? '<span class="badge bg-success">Yes</span>'
                : '<span class="badge bg-secondary">No</span>';

            const lastRun = task.last_run ? new Date(task.last_run).toLocaleString() : "Never";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${task.retailer}</td>
                <td><a href="${task.product_url}" target="_blank">Link</a></td>
                <td>${task.account_label}</td>
                <td>${timeStr}</td>
                <td>${task.timezone}</td>
                <td>${task.desired_quantity}</td>
                <td>${task.max_quantity}</td>
                <td>${task.max_price}</td>
                <td>${task.max_spend}</td>
                <td>${enabledBadge}</td>
                <td>${lastRun}</td>
                <td>
                    <button class="btn btn-sm btn-warning me-1" onclick='editTask(${JSON.stringify(task)})'>Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">Delete</button>
                </td>
            `;
            tbody.appendChild(row);
        });
}

function openTaskModal() {
    document.getElementById("taskId").value = "";

    document.getElementById("retailer").value = "Walmart";
    document.getElementById("productUrl").value = "";
    document.getElementById("accountLabel").value = "";
    document.getElementById("loginEmail").value = "";
    document.getElementById("loginPassword").value = "";

    document.getElementById("hour").value = "";
    document.getElementById("minute").value = "";
    document.getElementById("second").value = "";
    document.getElementById("ampm").value = "AM";
    document.getElementById("timezone").value = "CST";

    document.getElementById("desiredQty").value = "";
    document.getElementById("maxQty").value = "";
    document.getElementById("maxPrice").value = "";
    document.getElementById("maxSpend").value = "";
    document.getElementById("enabled").value = "true";

    taskModal.show();
}

function editTask(task) {
    document.getElementById("taskId").value = task.id;

    document.getElementById("retailer").value = task.retailer;
    document.getElementById("productUrl").value = task.product_url;
    document.getElementById("accountLabel").value = task.account_label;
    document.getElementById("loginEmail").value = task.login_email;
    document.getElementById("loginPassword").value = task.login_password;

    document.getElementById("hour").value = task.hour;
    document.getElementById("minute").value = task.minute;
    document.getElementById("second").value = task.second;
    document.getElementById("ampm").value = task.ampm;
    document.getElementById("timezone").value = task.timezone;

    document.getElementById("desiredQty").value = task.desired_quantity;
    document.getElementById("maxQty").value = task.max_quantity;
    document.getElementById("maxPrice").value = task.max_price;
    document.getElementById("maxSpend").value = task.max_spend;
    document.getElementById("enabled").value = task.enabled ? "true" : "false";

    taskModal.show();
}

async function saveTask() {
    const id = document.getElementById("taskId").value;

    const payload = {
        retailer: document.getElementById("retailer").value,
        product_url: document.getElementById("productUrl").value,
        account_label: document.getElementById("accountLabel").value,
        login_email: document.getElementById("loginEmail").value,
        login_password: document.getElementById("loginPassword").value,

        hour: parseInt(document.getElementById("hour").value || "0"),
        minute: parseInt(document.getElementById("minute").value || "0"),
        second: parseInt(document.getElementById("second").value || "0"),
        ampm: document.getElementById("ampm").value,
        timezone: document.getElementById("timezone").value,

        desired_quantity: parseInt(document.getElementById("desiredQty").value || "0"),
        max_quantity: parseInt(document.getElementById("maxQty").value || "0"),
        max_price: parseFloat(document.getElementById("maxPrice").value || "0"),
        max_spend: parseFloat(document.getElementById("maxSpend").value || "0"),

        enabled: document.getElementById("enabled").value === "true"
    };

    const url = id
        ? `${API_BASE}/tasks/update?task_id=${encodeURIComponent(id)}`
        : `${API_BASE}/tasks/add`;

    await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    taskModal.hide();
    loadTasks();
}

async function deleteTask(id) {
    if (!confirm("Delete this task?")) return;

    await fetch(`${API_BASE}/tasks/delete?task_id=${encodeURIComponent(id)}`, {
        method: "POST"
    });

    loadTasks();
}

// ───────────────────────────── accounts ─────────────────────────

async function loadAccountsDropdown() {
    const res = await fetch(`${API_BASE}/accounts/list`);
    const accounts = await res.json();

    const select = document.getElementById("accountFilter");
    select.innerHTML = `<option value="">All accounts</option>`;
    accounts.forEach(acc => {
        const opt = document.createElement("option");
        opt.value = acc.label;
        opt.textContent = acc.label;
        select.appendChild(opt);
    });
}

async function loadAccountsTable() {
    const res = await fetch(`${API_BASE}/accounts/list`);
    const accounts = await res.json();

    const tbody = document.getElementById("accountsTableBody");
    tbody.innerHTML = "";
    accounts.forEach(acc => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${acc.label}</td>
            <td>${acc.email}</td>
        `;
        tbody.appendChild(row);
    });
}

// ───────────────────────────── scheduler ────────────────────────

async function startScheduler() {
    await fetch(`${API_BASE}/scheduler/start`, { method: "POST" });
    refreshSchedulerStatus();
    refreshSystemStatus();
}

async function stopScheduler() {
    await fetch(`${API_BASE}/scheduler/stop`, { method: "POST" });
    refreshSchedulerStatus();
    refreshSystemStatus();
}

async function refreshSchedulerStatus() {
    const res = await fetch(`${API_BASE}/scheduler/status`);
    const data = await res.json();

    const badge = document.getElementById("schedulerStatusBadge");
    const countSpan = document.getElementById("schedulerTaskCount");

    countSpan.textContent = data.task_count ?? 0;

    if (data.running) {
        badge.textContent = "Running";
        badge.className = "badge bg-success";
    } else {
        badge.textContent = "Stopped";
        badge.className = "badge bg-danger";
    }
}

// ───────────────────────────── system status ────────────────────

async function refreshSystemStatus() {
    const res = await fetch(`${API_BASE}/system/status`);
    const data = await res.json();

    document.getElementById("systemTaskCount").textContent = data.task_count ?? 0;
    document.getElementById("systemAccountCount").textContent = data.account_count ?? 0;

    const badge = document.getElementById("systemSchedulerBadge");
    if (data.scheduler_running) {
        badge.textContent = "Running";
        badge.className = "badge bg-success";
    } else {
        badge.textContent = "Stopped";
        badge.className = "badge bg-danger";
    }
}

// ───────────────────────────── logs / websocket ─────────────────

function connectLogsWebSocket() {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${location.hostname}:8000/logs/stream`;

    try {
        logSocket = new WebSocket(wsUrl);
    } catch (e) {
        appendLogLine("[client] Failed to open WebSocket");
        return;
    }

    logSocket.onopen = () => {
        appendLogLine("[client] Connected to log stream");
    };

    logSocket.onmessage = (event) => {
        appendLogLine(event.data);
    };

    logSocket.onclose = () => {
        appendLogLine("[client] Log stream closed, retrying in 5s...");
        setTimeout(connectLogsWebSocket, 5000);
    };

    logSocket.onerror = () => {
        appendLogLine("[client] WebSocket error");
    };
}

function appendLogLine(text) {
    const pre = document.getElementById("logConsole");
    pre.textContent += text + "\n";
    pre.scrollTop = pre.scrollHeight;
}

function clearLogs() {
    document.getElementById("logConsole").textContent = "";
}
