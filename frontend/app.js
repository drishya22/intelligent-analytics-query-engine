const API_URL = "http://127.0.0.1:8000/api/query";

function setQuery(query) {
    document.getElementById("query").value = query;
}

async function runQuery() {

    const query = document.getElementById("query").value.trim();
    const fileInput = document.getElementById("csvFile");

    if (!query) {
        showError("Please enter an analytics question.");
        return;
    }

    const loading = document.getElementById("loading");
    const error = document.getElementById("error");
    const results = document.getElementById("results");

    loading.classList.remove("hidden");
    error.classList.add("hidden");
    results.classList.add("hidden");

    try {

        const formData = new FormData();

        formData.append("query", query);

        if (fileInput.files.length > 0) {
            formData.append("file", fileInput.files[0]);
        }

        const response = await fetch(API_URL, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Query failed."
            );
        }

        renderResults(data);

    } catch (err) {

        showError(err.message);

    } finally {

        loading.classList.add("hidden");
    }
}

function renderResults(data) {

    document
        .getElementById("results")
        .classList.remove("hidden");

    document.getElementById("confidence").textContent =
        Number(data.confidence).toFixed(2);

    document.getElementById("planner").textContent =
        data.planner || "deterministic";

    document.getElementById("rowCount").textContent =
        data.result ? data.result.length : 0;

    document.getElementById("explanation").textContent =
        data.explanation || "No explanation available.";

    document.getElementById("plan").textContent =
        JSON.stringify(data.plan, null, 2);

    renderTable(data.result || []);
}

function renderTable(rows) {

    const container = document.getElementById("table");

    if (!rows.length) {
        container.innerHTML = "<p>No results returned.</p>";
        return;
    }

    const columns = Object.keys(rows[0]);

    let html = "<table><thead><tr>";

    for (const column of columns) {
        html += `<th>${escapeHtml(column)}</th>`;
    }

    html += "</tr></thead><tbody>";

    for (const row of rows) {

        html += "<tr>";

        for (const column of columns) {
            html += `<td>${escapeHtml(String(row[column] ?? ""))}</td>`;
        }

        html += "</tr>";
    }

    html += "</tbody></table>";

    container.innerHTML = html;
}

function showError(message) {

    const error = document.getElementById("error");

    error.textContent = message;
    error.classList.remove("hidden");
}

function escapeHtml(value) {

    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}