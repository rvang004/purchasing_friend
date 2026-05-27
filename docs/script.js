const API_URL = "https://purchasingfriend-production.up.railway.app";

// Example: fetch tasks from backend
async function loadTasks() {
    const response = await fetch(`${API_URL}/tasks`);
    const data = await response.json();
    console.log("Tasks:", data);
}

loadTasks();
