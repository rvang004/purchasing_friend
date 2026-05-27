const API_URL = "https://purchasingfriend-production.up.railway.app";

// Load tasks on startup
document.addEventListener("DOMContentLoaded", () => {
    loadTasks();
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
                <td>${task.account_label}</td>
                <td>${task.hour}:${task.minute}:${task.second} ${task.ampm}</td>
                <td>${task.timezone}</td>
                <td>${task.desired_quantity}</td>
                <td>${task.max_quantity}</td>
                <td>${task.max_price}</td>
                <td>${task.max_spend}</td>
                <td>${task.enabled ? "Yes" : "No"}</td>
                <td>${task.last_run || "Never"}</td>
                <td>
                    <button class="btn btn-warning btn-sm" onclick='editTask(${JSON.stringify(task)})'>Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteTask('${task.id}')">Delete</button>
                </td>
            </tr>
        `;
    });
}

function openTaskModal() {
    document.getElementById("taskId").value = "";
    [
        "retailer","productUrl","accountLabel","loginEmail","loginPassword",
        "hour","minute","second","ampm","timezone",
        "desiredQty","maxQty","maxPrice","maxSpend","enabled"
    ].forEach(id => document.getElementById(id).value = "");

    new bootstrap.Modal(document.getElementById("taskModal")).show();
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
    document.getElementById("enabled").value = task.enabled;

    new bootstrap.Modal(document.getElementById("taskModal")).show();
}

async function saveTask() {
    const id = document.getElementById("taskId").value;

    const payload = {
        retailer: document.getElementById("retailer").value,
        product_url: document.getElementById("productUrl").value,
        account_label: document.getElementById("accountLabel").value,
        login_email: document.getElementById("loginEmail").value,
        login_password: document.getElementById("loginPassword").value,

        hour: parseInt(document.getElementById("hour").value),
        minute: parseInt(document.getElementById("minute").value),
        second: parseInt(document.getElementById("second").value),
        ampm: document.getElementById("ampm").value,
        timezone: document.getElementById("timezone").value,

        desired_quantity: parseInt(document.getElementById("desiredQty").value),
        max_quantity: parseInt(document.getElementById("maxQty").value),
        max_price: parseFloat(document.getElementById("maxPrice").value),
        max_spend: parseFloat(document.getElementById("maxSpend").value),

        enabled: document.getElementById("enabled").value === "true"
    };

    const url = id ? `${API_URL}/tasks/update?task_id=${id}` : `${API_URL}/tasks/add`;

    await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    loadTasks();
    bootstrap.Modal.getInstance(document.getElementById("taskModal")).hide();
}

async function deleteTask(id) {
    await fetch(`${API_URL}/tasks/delete?task_id=${id}`, { method: "POST" });
    loadTasks();
}
