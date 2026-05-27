const API_URL = "https://purchasingfriend-production.up.railway.app";

// Load tasks on startup
document.addEventListener("DOMContentLoaded", () => {
    loadTasks();
    loadSchedulerStatus();
    loadLogs();
});

// ---------------- TASKS ----------------

async function loadTasks() {
    const res = await fetch(`${API_URL}/tasks`);
    const tasks = await res.json();

    const tbody = document.getElementById("taskTableBody");
    tbody.innerHTML = "";

    tasks.forEach(task => {
        tbody.innerHTML += `
            <tr>
                <td>${task.retailer}</td>
                <td><a href="${task.product_url}" target="_blank">Link</a></td>
                <td>${task.account_email}</td>
                <td>${task.schedule_time}</td>
                <td>${task.enabled ? "Yes" : "No"}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick='editTask(${JSON.stringify(task)})'>Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">Delete</button>
                </td>
            </tr>
        `;
    });
}

function openTaskModal() {
    document.getElementById("taskId").value = "";
    document.getElementById("retailer").value = "";
    document.getElementById("productUrl").value = "";
    document.getElementById("accountEmail").value = "";
    document.getElementById("scheduleTime").value = "";
    document.getElementById("maxQty").value = "";
    document.getElementById("enabled").value = "true";

    new bootstrap.Modal(document.getElementById("taskModal")).show();
}

function editTask(task) {
    document.getElementById("taskId").value = task.id;
    document.getElementById("retailer").value = task.retailer;
    document.getElementById("productUrl").value = task.product_url;
    document.getElementById("accountEmail").value = task.account_email;
    document.getElementById("scheduleTime").value = task.schedule_time;
    document.getElementById("maxQty").value = task.max_quantity;
    document.getElementById("enabled").value = task.enabled;

    new bootstrap.Modal(document.getElementById("taskModal")).show();
}

async function saveTask() {
    const id = document.getElementById("taskId").value;

    const payload = {
        retailer: document.getElementById("retailer").value,
        product_url: document.getElementById("productUrl").value,
        account_email: document.getElementById("accountEmail").value,
        schedule_time: document.getElementById("scheduleTime").value,
        max_quantity: parseInt(document.getElementById("maxQty").value),
        enabled: document.getElementById("enabled").value === "true"
    };

    const method = id ? "PUT" : "POST";
    const url = id ? `${API_URL}/tasks/${id}` : `${API_URL}/tasks`;

    await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    loadTasks();
    bootstrap.Modal.getInstance(document.getElementById("taskModal")).hide();
}

async function deleteTask(id) {
    await fetch(`${API_URL}/tasks/${id}`, { method: "DELETE" });
    loadTasks();
}

// ---------------- SCHEDULER ----------------

async function loadSchedulerStatus() {
    const res = await fetch(`${API_URL}/scheduler/status`);
    const data = await res.json();

    document.getElementById("schedulerStatus").innerText = data.running ? "Running" : "Stopped";
    document.getElementById("nextRun").innerText = data.next_run || "N/A";
}

async function startScheduler() {
    await fetch(`${API_URL}/scheduler/start`, { method: "POST" });
    loadSchedulerStatus();
}

async function stopScheduler() {
    await fetch(`${API_URL}/scheduler/stop`, { method: "POST" });
    loadSchedulerStatus();
}

// ---------------- LOGS ----------------

async function loadLogs() {
    const res = await fetch(`${API_URL}/logs`);
    const text = await res.text();
    document.getElementById("logOutput").innerText = text;
}
