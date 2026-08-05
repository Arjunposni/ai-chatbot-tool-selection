function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatIntent(intent) {
    if (Array.isArray(intent)) {
        return intent.join(", ");
    }
    return intent;
}

function renderAppointments(appointments) {
    let html = `
        <div class="result-card">
            <h4>📅 Appointments</h4>
    `;

    appointments.forEach(app => {
        html += `
            <div class="result-item">
                <b>Specialty:</b>
                ${escapeHtml(app.specialty)}<br>

                <b>Date:</b>
                ${escapeHtml(app.date)}<br>

                <b>Status:</b>
                ${escapeHtml(app.status)}
            </div>
        `;
    });

    html += "</div>";
    return html;
}

function renderLabResults(results) {
    let html = `
        <div class="result-card">
            <h4>🧪 Lab Results</h4>
    `;

    results.forEach(result => {
        html += `
            <div class="result-item">
                <b>Test:</b>
                ${escapeHtml(result.test_name)}<br>

                <b>Result:</b>
                ${escapeHtml(result.result)}<br>

                <b>Date:</b>
                ${escapeHtml(result.date)}
            </div>
        `;
    });

    html += "</div>";
    return html;
}

function renderPrescription(medication) {
    return `
        <div class="result-card">
            <h4>💊 Prescription</h4>
            <b>Medication:</b>
            ${escapeHtml(medication)}
        </div>
    `;
}

async function sendMessage() {

    const input = document.getElementById("message");
    const chat = document.getElementById("chat-box");
    const button = document.querySelector("button");

    const text = input.value.trim();

    if (!text) return;

    input.disabled = true;
    button.disabled = true;

    // ----------------------------
    // User Message
    // ----------------------------
    chat.innerHTML += `
        <div class="user-message">
            ${escapeHtml(text)}
        </div>
    `;

    input.value = "";
    chat.scrollTop = chat.scrollHeight;

    // ----------------------------
    // Thinking...
    // ----------------------------
    chat.innerHTML += `
        <div class="bot-message" id="typing">
            🤖 Thinking...
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text
            })
        });

        const data = await response.json();

        const typing = document.getElementById("typing");
        if (typing) typing.remove();

        // ----------------------------
        // Tool execution info
        // ----------------------------
        let toolInfo = "";

        if (
            data.intent_detected &&
            data.intent_detected !== "faq_lookup"
        ) {

            toolInfo = `
                <div class="tool-card">

                    <strong>🛠 Tool Execution</strong><br><br>

                    <b>Intent:</b>
                    ${escapeHtml(formatIntent(data.intent_detected))}<br>

                    <b>Method:</b>
                    ${escapeHtml(data.method_used)}

                </div>
            `;
        }

        // ----------------------------
        // Extra Details
        // ----------------------------
        let details = "";

        // Multi-intent results — unpack each nested tool_result
        if (
            data.tool_result &&
            data.tool_result.multi_results
        ) {

            data.tool_result.multi_results.forEach(item => {

                const result = item.result;

                if (result.appointments && result.appointments.length > 0) {
                    details += renderAppointments(result.appointments);
                }

                if (result.results && result.results.length > 0) {
                    details += renderLabResults(result.results);
                }

                if (result.medication) {
                    details += renderPrescription(result.medication);
                }
            });
        }

        // Appointment List (single-intent path)
        if (
            data.tool_result &&
            data.tool_result.appointments &&
            data.tool_result.appointments.length > 0
        ) {
            details += renderAppointments(data.tool_result.appointments);
        }

        // Lab Results (single-intent path)
        if (
            data.tool_result &&
            data.tool_result.results &&
            data.tool_result.results.length > 0
        ) {
            details += renderLabResults(data.tool_result.results);
        }

        // Prescription Details (single-intent path)
        if (
            data.tool_result &&
            data.tool_result.medication
        ) {
            details += renderPrescription(data.tool_result.medication);
        }

        // ----------------------------
        // Bot Message
        // ----------------------------
        chat.innerHTML += `
            <div class="bot-message">

                ${toolInfo}

                <div class="response-text">
                    ${escapeHtml(data.response)}
                </div>

                ${details}

            </div>
        `;

    }
    catch (error) {

        const typing = document.getElementById("typing");

        if (typing) typing.remove();

        chat.innerHTML += `
            <div class="bot-message">
                ❌ Unable to connect to the Healthcare AI server.
            </div>
        `;

        console.error(error);
    }
    finally {

        input.disabled = false;
        button.disabled = false;

        input.focus();

        chat.scrollTop = chat.scrollHeight;
    }
}

// -----------------------------------
// Press Enter to Send
// -----------------------------------

document
    .getElementById("message")
    .addEventListener("keydown", function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            sendMessage();
        }

    });