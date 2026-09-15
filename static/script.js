
const taskInput = document.getElementById("task-input");
const runBtn = document.getElementById("run-btn");

const emptyState = document.getElementById("empty-state");
const pipeline = document.getElementById("pipeline");

const providerList = document.getElementById("provider-list");
const failToggleList = document.getElementById("fail-toggle-list");

const logToggle = document.getElementById("log-toggle");
const rawLog = document.getElementById("raw-log");


let providers = {};
let lastResult = null;


/* ============================================================
   BASIC HELPERS
   ============================================================ */

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* ============================================================
   MARKDOWN RENDERING
   ============================================================ */

function renderMarkdown(content) {

    if (!content) {
        return "";
    }

    /*
     * Marked converts Markdown returned by the LLM into HTML.
     *
     * Examples:
     *
     * **bold**
     * ## Heading
     * - list
     * | table |
     * ```python
     * code
     * ```
     */

    if (typeof marked === "undefined") {
        return escapeHtml(content);
    }

    return marked.parse(String(content), {
        gfm: true,
        breaks: true
    });
}


/* ============================================================
   IMAGE RESULT
   ============================================================ */

function renderImageResult(content) {

    if (!content) {
        return `
            <div class="image-error">
                Image path was not returned by the provider.
            </div>
        `;
    }

    let imageUrl;

    try {

        imageUrl = new URL(
            content,
            window.location.origin
        ).href;

    } catch (error) {

        imageUrl = content;
    }


    return `
        <div class="image-result">

            <div class="image-loading">
                Loading generated image...
            </div>

            <img
                class="exec-image"
                src="${escapeHtml(imageUrl)}"
                alt="Generated image"
                loading="lazy"
                onload="handleImageLoad(this)"
                onerror="handleImageError(this)"
            />

            <div class="image-url">
                ${escapeHtml(imageUrl)}
            </div>

        </div>
    `;
}


function handleImageLoad(image) {

    const container = image.closest(".image-result");

    if (!container) {
        return;
    }

    const loading = container.querySelector(".image-loading");

    if (loading) {
        loading.remove();
    }

    image.style.display = "block";
}


function handleImageError(image) {

    const container = image.closest(".image-result");

    if (!container) {
        return;
    }

    image.style.display = "none";

    const loading = container.querySelector(".image-loading");

    if (loading) {
        loading.remove();
    }

    const existingError = container.querySelector(".image-error");

    if (existingError) {
        return;
    }

    const error = document.createElement("div");

    error.className = "image-error";

    error.innerHTML = `
        <strong>Image could not be displayed.</strong>
        <br>
        The backend generated a result, but the browser
        could not load the image file.
    `;

    container.insertBefore(error, container.querySelector(".image-url"));
}


/* ============================================================
   PROVIDER LIST
   ============================================================ */

async function loadProviders() {

    providerList.innerHTML = `
        <div class="availability-status">
            Checking providers...
        </div>
    `;

    failToggleList.innerHTML = "";


    try {

        const response = await fetch("/api/providers");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        providers = await response.json();


        providerList.innerHTML = "";

        Object.entries(providers).forEach(([name, info]) => {

            const item = document.createElement("div");

            item.className = "provider-item";


            let statusText;

            if (info.available) {

                statusText = info.demo
                    ? "demo"
                    : "live";

            } else {

                statusText = "unavailable";
            }


            item.innerHTML = `
                <div class="provider-name">
                    ${escapeHtml(name)}
                </div>

                <div class="provider-model">
                    ${escapeHtml(info.model_name || "")}
                </div>

                <div class="provider-status ${info.available ? "available" : "unavailable"}">
                    ${escapeHtml(statusText)}
                </div>
            `;


            providerList.appendChild(item);


            /*
             * Failure simulation checkbox
             */

            const failItem = document.createElement("label");

            failItem.className = "fail-toggle";


            failItem.innerHTML = `
                <input
                    type="checkbox"
                    value="${escapeHtml(name)}"
                >

                <span>
                    ${escapeHtml(name)}
                </span>
            `;


            failToggleList.appendChild(failItem);

        });

    } catch (error) {

        providerList.innerHTML = `
            <div class="availability-status error">
                Failed to load providers.
            </div>
        `;

        console.error("Provider loading error:", error);
    }
}


/* ============================================================
   PIPELINE HELPERS
   ============================================================ */

function stageTitle(stage) {

    const titles = {
        analysis: "Task Analyzer",
        availability: "Provider Availability",
        routing: "Smart Router",
        selection: "Model Selected",
        execution: "Execution",
        recovery: "Recovery Engine",
        exhausted: "No Providers Left"
    };

    return titles[stage] || stage;
}


function createStageElement(stage, index) {

    const element = document.createElement("div");

    element.className = "pipeline-stage";

    element.dataset.stage = stage.stage;

    element.style.animationDelay = `${index * 60}ms`;

    return element;
}


/* ============================================================
   ANALYSIS STAGE
   ============================================================ */

function renderAnalysisStage(stage) {

    const detail = stage.detail || {};

    return `
        <div class="stage-header">

            <div class="stage-number">
                01
            </div>

            <div>
                <div class="stage-label">
                    Task Analyzer
                </div>

                <div class="stage-sub">
                    Classification and difficulty estimation
                </div>
            </div>

        </div>


        <div class="analysis-grid">

            <div class="analysis-item">
                <span class="analysis-label">Type</span>
                <strong>${escapeHtml(detail.task_type)}</strong>
            </div>

            <div class="analysis-item">
                <span class="analysis-label">Difficulty</span>
                <strong>${escapeHtml(detail.difficulty)}</strong>
            </div>

            <div class="analysis-item">
                <span class="analysis-label">Words</span>
                <strong>${escapeHtml(detail.word_count)}</strong>
            </div>

        </div>
    `;
}


/* ============================================================
   AVAILABILITY STAGE
   ============================================================ */

function renderAvailabilityStage(stage) {

    const detail = stage.detail || {};

    let rows = "";

    Object.entries(detail).forEach(([name, info]) => {

        if (!info) {
            return;
        }

        const available = info.available;

        const status = available
            ? (info.demo ? "demo" : "live")
            : "unavailable";


        rows += `
            <div class="availability-row">

                <span class="availability-provider">
                    ${escapeHtml(name)}
                </span>

                <span class="availability-model">
                    ${escapeHtml(info.model_name || "")}
                </span>

                <span class="availability-badge ${available ? "available" : "unavailable"}">
                    ${escapeHtml(status)}
                </span>

            </div>
        `;
    });


    return `
        <div class="stage-header">

            <div class="stage-number">
                02
            </div>

            <div>
                <div class="stage-label">
                    Provider Availability
                </div>

                <div class="stage-sub">
                    Live and demo provider status
                </div>
            </div>

        </div>

        <div class="availability-list">
            ${rows}
        </div>
    `;
}


/* ============================================================
   ROUTING STAGE
   ============================================================ */

function renderRoutingStage(stage) {

    const ranked = stage.detail?.ranked || [];

    let rows = "";

    ranked.forEach((item, index) => {

        rows += `
            <div class="ranking-row">

                <span class="rank-number">
                    ${index + 1}
                </span>

                <span class="rank-provider">
                    ${escapeHtml(item.provider)}
                </span>

                <span class="rank-score">
                    ${escapeHtml(item.score)}
                </span>

            </div>
        `;
    });


    return `
        <div class="stage-header">

            <div class="stage-number">
                03
            </div>

            <div>
                <div class="stage-label">
                    Smart Router
                </div>

                <div class="stage-sub">
                    Providers ranked for this task
                </div>
            </div>

        </div>

        <div class="ranking-list">
            ${rows}
        </div>
    `;
}


/* ============================================================
   SELECTION STAGE
   ============================================================ */

function renderSelectionStage(stage) {

    const detail = stage.detail || {};

    return `
        <div class="stage-header">

            <div class="stage-number">
                04
            </div>

            <div>
                <div class="stage-label">
                    Model Selected
                </div>

                <div class="stage-sub">
                    Best available provider
                </div>
            </div>

        </div>


        <div class="selection-card">

            <div class="selection-provider">
                ${escapeHtml(detail.provider)}
            </div>

            <div class="selection-score">
                Score: ${escapeHtml(detail.score)}
            </div>

            <div class="selection-mode">
                ${detail.demo ? "demo call" : "live call"}
            </div>

        </div>
    `;
}


/* ============================================================
   EXECUTION STAGE
   ============================================================ */

function renderExecutionStage(stage) {

    const detail = stage.detail || {};

    const contentType = detail.content_type || "text";

    let output = "";


    if (contentType === "image") {

        output = renderImageResult(detail.content);

    } else {

        output = `
            <div class="exec-content markdown-content">
                ${renderMarkdown(detail.content || "")}
            </div>
        `;
    }


    const statusClass = detail.status === "success"
        ? "success"
        : "failed";


    return `
        <div class="stage-header">

            <div class="stage-number">
                05
            </div>

            <div>
                <div class="stage-label">
                    ${escapeHtml(stage.label || "Execution")}
                </div>

                <div class="stage-sub">
                    ${detail.demo ? "Demo execution" : "Live provider call"}
                </div>
            </div>

        </div>


        <div class="execution-meta">

            <span class="execution-provider">
                ${escapeHtml(detail.model || "")}
            </span>

            <span class="execution-status ${statusClass}">
                ${escapeHtml(detail.status || "")}
            </span>

            <span class="execution-latency">
                ${escapeHtml(detail.latency_ms || 0)} ms
            </span>

        </div>


        <div class="execution-output">

            ${output}

        </div>


        ${
            detail.error
                ? `
                    <div class="execution-error">
                        ${escapeHtml(detail.error)}
                    </div>
                `
                : ""
        }
    `;
}


/* ============================================================
   RECOVERY STAGE
   ============================================================ */

function renderRecoveryStage(stage) {

    const detail = stage.detail || {};

    return `
        <div class="stage-header">

            <div class="stage-number">
                ↻
            </div>

            <div>
                <div class="stage-label">
                    Recovery Engine
                </div>

                <div class="stage-sub">
                    Provider failure detected
                </div>
            </div>

        </div>


        <div class="recovery-card">

            <div class="recovery-provider">
                Failed provider:
                <strong>
                    ${escapeHtml(detail.failed_provider)}
                </strong>
            </div>

            <div class="recovery-error">
                ${escapeHtml(detail.error || "")}
            </div>

            <div class="recovery-message">
                ${escapeHtml(detail.message || "")}
            </div>

        </div>
    `;
}


/* ============================================================
   EXHAUSTED STAGE
   ============================================================ */

function renderExhaustedStage(stage) {

    const detail = stage.detail || {};

    return `
        <div class="stage-header">

            <div class="stage-number">
                !
            </div>

            <div>
                <div class="stage-label">
                    No Providers Left
                </div>

                <div class="stage-sub">
                    Task could not be completed
                </div>
            </div>

        </div>


        <div class="execution-error">
            ${escapeHtml(detail.message || "All providers failed.")}
        </div>
    `;
}


/* ============================================================
   GENERIC STAGE RENDERER
   ============================================================ */

function renderStage(stage, index) {

    const element = createStageElement(stage, index);

    switch (stage.stage) {

        case "analysis":
            element.innerHTML = renderAnalysisStage(stage);
            break;

        case "availability":
            element.innerHTML = renderAvailabilityStage(stage);
            break;

        case "routing":
            element.innerHTML = renderRoutingStage(stage);
            break;

        case "selection":
            element.innerHTML = renderSelectionStage(stage);
            break;

        case "execution":
            element.innerHTML = renderExecutionStage(stage);
            break;

        case "recovery":
            element.innerHTML = renderRecoveryStage(stage);
            break;

        case "exhausted":
            element.innerHTML = renderExhaustedStage(stage);
            break;

        default:

            element.innerHTML = `
                <div class="stage-header">

                    <div class="stage-number">
                        ?
                    </div>

                    <div>
                        <div class="stage-label">
                            ${escapeHtml(stageTitle(stage.stage))}
                        </div>
                    </div>

                </div>
            `;
    }


    return element;
}


/* ============================================================
   COMPLETE PIPELINE
   ============================================================ */

function renderPipeline(result) {

    pipeline.innerHTML = "";

    const trace = result.trace || [];


    trace.forEach((stage, index) => {

        const element = renderStage(stage, index);

        pipeline.appendChild(element);

    });


    emptyState.hidden = true;

    pipeline.hidden = false;


    /*
     * Show raw trace
     */

    rawLog.textContent = JSON.stringify(result, null, 2);

    logToggle.hidden = false;

    rawLog.hidden = true;

    logToggle.textContent = "Raw trace ▾";
}


/* ============================================================
   RUN TASK
   ============================================================ */

async function runTask() {

    const task = taskInput.value.trim();


    if (!task) {

        taskInput.focus();

        return;
    }


    runBtn.disabled = true;

    runBtn.textContent = "Running...";


    pipeline.innerHTML = "";

    emptyState.hidden = true;

    pipeline.hidden = false;

    logToggle.hidden = true;

    rawLog.hidden = true;


    const failureCheckboxes =
        failToggleList.querySelectorAll(
            'input[type="checkbox"]:checked'
        );


    const simulateFailureOn =
        Array.from(failureCheckboxes)
            .map(input => input.value);


    pipeline.innerHTML = `
        <div class="pipeline-loading">
            <div class="loading-spinner"></div>
            <div>
                Running ModelPilot pipeline...
            </div>
        </div>
    `;


    try {

        const response = await fetch("/api/run", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                task: task,
                simulate_failure_on: simulateFailureOn
            })

        });


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.error || `HTTP ${response.status}`
            );
        }


        lastResult = result;

        renderPipeline(result);


    } catch (error) {

        console.error("Run error:", error);


        pipeline.innerHTML = `
            <div class="execution-error">

                <strong>
                    Request failed
                </strong>

                <br><br>

                ${escapeHtml(error.message)}

            </div>
        `;

        pipeline.hidden = false;

    } finally {

        runBtn.disabled = false;

        runBtn.textContent = "Run task";
    }
}


/* ============================================================
   RAW TRACE TOGGLE
   ============================================================ */

logToggle.addEventListener("click", () => {

    const isHidden = rawLog.hidden;

    rawLog.hidden = !isHidden;

    logToggle.textContent =
        isHidden
            ? "Raw trace ▴"
            : "Raw trace ▾";
});


/* ============================================================
   RUN BUTTON
   ============================================================ */

runBtn.addEventListener("click", runTask);


/* ============================================================
   CTRL + ENTER
   ============================================================ */

taskInput.addEventListener("keydown", (event) => {

    if (
        event.key === "Enter" &&
        (event.ctrlKey || event.metaKey)
    ) {

        event.preventDefault();

        runTask();
    }
});


/* ============================================================
   INITIAL LOAD
   ============================================================ */

loadProviders();

