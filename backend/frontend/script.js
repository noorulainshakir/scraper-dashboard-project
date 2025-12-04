// ===================== CONFIGURATION =====================
const CONFIG = {
    API_BASE_URL: '', // Add your API base URL here
    TOAST_DURATION: 3000,
    DEBOUNCE_DELAY: 300
};

// ===================== TEMPORARY SCRAPER DATA =====================
const scrapers = [
    { id: 'luxottica', name: "Luxottica", status: "stopped", lastRun: "Not Available", nextRun: "Not Scheduled" },
    { id: 'safilo', name: "Safilo", status: "stopped", lastRun: "Not Available", nextRun: "Not Scheduled" }
];

// ===================== DETECT CURRENT PAGE =====================
const currentPage = window.location.pathname.split("/").pop() || "index.html";

// ===================== UTILITY FUNCTIONS =====================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateString) {
    if (!dateString || dateString === "Not Available") return "Not Available";
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// ===================== TOAST NOTIFICATIONS =====================
function showToast(message, type = 'success') {
    let toast = document.getElementById("toast");
    
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast";
        toast.className = "toast";
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add("show");
    
    setTimeout(() => {
        toast.classList.remove("show");
    }, CONFIG.TOAST_DURATION);
}

// ===================== MODAL MANAGEMENT =====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.add("modal-open");
    document.body.style.overflow = "hidden";
    
    // Focus management
    const firstInput = modal.querySelector('input, select, button');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
    
    // Close on Escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            closeModal(modalId);
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.remove("modal-open");
    document.body.style.overflow = "";
}

function setupModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    const backdrop = modal.querySelector('.modal-backdrop');
    const closeButtons = modal.querySelectorAll('.close-btn, [id*="close"], [id*="cancel"]');
    
    // Close on backdrop click
    if (backdrop) {
        backdrop.addEventListener('click', () => closeModal(modalId));
    }
    
    // Close on close button click
    closeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeModal(modalId);
        });
    });
    
    // Prevent modal content clicks from closing
    const dialog = modal.querySelector('.modal-dialog');
    if (dialog) {
        dialog.addEventListener('click', (e) => e.stopPropagation());
    }
}

// ===================== RENDER SCRAPERS =====================
function renderScrapers() {
    const container = document.getElementById("scraperList");
    if (!container) return;
    
    if (scrapers.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                <p style="font-size: 1.25rem; margin-bottom: 0.5rem;">No scrapers found</p>
                <p>Add a scraper to get started</p>
            </div>
        `;
        return;
    }
    
    // Build HTML string first to avoid multiple innerHTML updates
    let htmlString = "";
    
    scrapers.forEach(scraper => {
        const statusClass = scraper.status || 'stopped';
        const isRunning = scraper.status === 'running';
        
        let actionsHTML = `
            <button class="start-btn ${isRunning ? 'disabled' : ''}" 
                    data-id="${scraper.id}" 
                    ${isRunning ? 'disabled' : ''}
                    aria-label="Start ${scraper.name}">
                Start
            </button>
            <button class="stop-btn ${!isRunning ? 'disabled' : ''}" 
                    data-id="${scraper.id}"
                    ${!isRunning ? 'disabled' : ''}
                    aria-label="Stop ${scraper.name}">
                Stop
            </button>
        `;
        
        if (currentPage === "services.html") {
            actionsHTML += `
                <button class="schedule-btn" data-id="${scraper.id}" aria-label="Schedule ${scraper.name}">
                    Schedule
                </button>
                <button class="view-log-btn" data-id="${scraper.id}" aria-label="View logs for ${scraper.name}">
                    View Logs
                </button>
            `;
        }
        
        if (currentPage === "schedules.html") {
            actionsHTML += `
                <button class="edit-schedule-btn" data-id="${scraper.id}" aria-label="Edit schedule for ${scraper.name}">
                    Edit
                </button>
                <button class="remove-schedule-btn" data-id="${scraper.id}" aria-label="Remove schedule for ${scraper.name}">
                    Remove
                </button>
            `;
        }
        
        htmlString += `
            <div class="scraper-card" data-id="${scraper.id}" data-status="${statusClass}">
                <h3>${scraper.name}</h3>
                <p>Status: <span class="status ${statusClass}">${statusClass.toUpperCase()}</span></p>
                <p>Last Run: ${scraper.lastRun}</p>
                <p class="next-run">Next Run: ${scraper.nextRun}</p>
                <div class="actions">
                    ${actionsHTML}
                </div>
            </div>
        `;
    });
    
    // Set innerHTML once
    container.innerHTML = htmlString;
    
    // Attach event listeners after DOM is updated
    attachScraperEvents();
}

// ===================== BUTTON EVENTS =====================
function attachScraperEvents() {
    // Start buttons - attach to all buttons, check disabled state in handler
    document.querySelectorAll(".start-btn").forEach(btn => {
        // Only attach if not already attached (check for data attribute)
        if (!btn.dataset.listenerAttached) {
            btn.dataset.listenerAttached = 'true';
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // Check if button is disabled
                if (this.disabled || this.classList.contains('disabled')) {
                    return;
                }
                const id = this.dataset.id || this.closest('[data-id]')?.dataset.id;
                if (id) {
                    startScraper(id, this);
                }
            });
        }
    });
    
    // Stop buttons - attach to all buttons, check disabled state in handler
    document.querySelectorAll(".stop-btn").forEach(btn => {
        // Only attach if not already attached (check for data attribute)
        if (!btn.dataset.listenerAttached) {
            btn.dataset.listenerAttached = 'true';
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // Check if button is disabled
                if (this.disabled || this.classList.contains('disabled')) {
                    return;
                }
                const id = this.dataset.id || this.closest('[data-id]')?.dataset.id;
                if (id) {
                    stopScraper(id, this);
                }
            });
        }
    });
    
    // Schedule buttons (services.html)
    if (currentPage === "services.html") {
        document.querySelectorAll(".schedule-btn").forEach(btn => {
            btn.onclick = (e) => {
                const id = e.target.dataset.id || e.target.closest('[data-id]')?.dataset.id;
                const card = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                            document.querySelector(`tr[data-id="${id}"]`);
                if (card && id) {
                    openScheduleModal(id, card);
                }
            };
        });
    }
    
    // Edit buttons (schedules.html)
    if (currentPage === "schedules.html") {
        document.querySelectorAll(".edit-schedule-btn").forEach(btn => {
            btn.onclick = (e) => {
                const id = e.target.dataset.id || e.target.closest('[data-id]')?.dataset.id;
                const card = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                            document.querySelector(`tr[data-id="${id}"]`);
                if (card && id) {
                    openScheduleModal(id, card);
                }
            };
        });
        
        // Remove buttons
        document.querySelectorAll(".remove-schedule-btn").forEach(btn => {
            btn.onclick = (e) => {
                const id = e.target.dataset.id || e.target.closest('[data-id]')?.dataset.id;
                if (id && confirm(`Are you sure you want to remove the schedule for this scraper?`)) {
                    removeSchedule(id);
                }
            };
        });
    }
}

// ===================== START / STOP FUNCTIONS =====================
async function startScraper(id, buttonElement) {
    const element = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                   document.querySelector(`tr[data-id="${id}"]`);
    if (!element) return;
    
    showLoading(buttonElement);
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        element.dataset.status = "running";
        const statusEl = element.querySelector(".status");
        if (statusEl) {
            statusEl.textContent = "RUNNING";
            statusEl.className = "status running";
        }
        
        const startBtn = element.querySelector(".start-btn");
        const stopBtn = element.querySelector(".stop-btn");
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.classList.add('disabled');
        }
        if (stopBtn) {
            stopBtn.disabled = false;
            stopBtn.classList.remove('disabled');
        }
        
        // Update scraper data
        const scraper = scrapers.find(s => s.id === id);
        if (scraper) scraper.status = "running";
        
        showToast(`Scraper "${id}" started successfully`, 'success');
    } catch (error) {
        showToast(`Failed to start scraper: ${error.message}`, 'error');
    } finally {
        hideLoading(buttonElement);
    }
}

async function stopScraper(id, buttonElement) {
    const element = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                   document.querySelector(`tr[data-id="${id}"]`);
    if (!element) return;
    
    showLoading(buttonElement);
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        element.dataset.status = "stopped";
        const statusEl = element.querySelector(".status");
        if (statusEl) {
            statusEl.textContent = "STOPPED";
            statusEl.className = "status stopped";
        }
        
        const startBtn = element.querySelector(".start-btn");
        const stopBtn = element.querySelector(".stop-btn");
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.classList.remove('disabled');
        }
        if (stopBtn) {
            stopBtn.disabled = true;
            stopBtn.classList.add('disabled');
        }
        
        // Update scraper data
        const scraper = scrapers.find(s => s.id === id);
        if (scraper) scraper.status = "stopped";
        
        showToast(`Scraper "${id}" stopped successfully`, 'success');
    } catch (error) {
        showToast(`Failed to stop scraper: ${error.message}`, 'error');
    } finally {
        hideLoading(buttonElement);
    }
}

// ===================== SCHEDULE MODAL =====================
function openScheduleModal(id, element) {
    // Try to get name from h3 (card view) or first td (table view)
    const name = element.querySelector("h3")?.textContent.trim() || 
                 element.querySelector("td:first-child")?.textContent.trim() || 
                 element.querySelector("td:nth-child(2)")?.textContent.trim() || 
                 id;
    
    const scraperIdInput = document.getElementById("schedScraperId");
    const scraperNameInput = document.getElementById("schedScraperName");
    if (scraperIdInput) scraperIdInput.value = id;
    if (scraperNameInput) scraperNameInput.value = name;
    
    // Set default date/time
    const now = new Date();
    const dateInput = document.getElementById("schedDate");
    const timeInput = document.getElementById("schedTime");
    
    if (dateInput) {
        dateInput.value = now.toISOString().split('T')[0];
    }
    if (timeInput) {
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        timeInput.value = `${hours}:${minutes}`;
    }
    
    openModal("scheduleModal");
}

function setupScheduleModal() {
    if (currentPage !== "services.html" && currentPage !== "schedules.html") return;
    
    setupModal("scheduleModal");
    
    const freqSelect = document.getElementById("schedFreq");
    const cronInput = document.getElementById("schedCron");
    const errorMsg = document.getElementById("schedError");
    
    // Enable/disable cron input based on frequency
    if (freqSelect && cronInput) {
        freqSelect.addEventListener("change", (e) => {
            if (e.target.value === "custom") {
                cronInput.disabled = false;
                cronInput.setAttribute('aria-disabled', 'false');
                cronInput.required = true;
            } else {
                cronInput.disabled = true;
                cronInput.setAttribute('aria-disabled', 'true');
                cronInput.required = false;
                cronInput.value = "";
            }
        });
    }
    
    // Form validation and submission
    const saveBtn = document.getElementById("saveScheduleBtn");
    const cancelBtn = document.getElementById("cancelScheduleBtn");
    const form = document.getElementById("scheduleForm");
    
    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            if (!validateScheduleForm()) return;
            
            const id = document.getElementById("schedScraperId").value;
            const freq = document.getElementById("schedFreq").value;
            const cron = document.getElementById("schedCron").value;
            const date = document.getElementById("schedDate").value;
            const time = document.getElementById("schedTime").value;
            
            showLoading(saveBtn);
            
            try {
                // Simulate API call
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                const element = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                               document.querySelector(`tr[data-id="${id}"]`);
                if (element) {
                    const nextRunP = element.querySelector(".next-run");
                    if (nextRunP) {
                        if (freq === "custom") {
                            nextRunP.textContent = `Next Run: Cron: ${cron}`;
                        } else {
                            const nextRunDate = new Date(`${date}T${time}`);
                            nextRunP.textContent = `Next Run: ${formatDate(nextRunDate.toISOString())}`;
                        }
                    }
                }
                
                closeModal("scheduleModal");
                showToast("Schedule saved successfully", 'success');
            } catch (error) {
                showToast(`Failed to save schedule: ${error.message}`, 'error');
            } finally {
                hideLoading(saveBtn);
            }
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            closeModal("scheduleModal");
            if (form) form.reset();
            if (errorMsg) {
                errorMsg.classList.remove('show');
                errorMsg.textContent = '';
            }
        });
    }
}

function validateScheduleForm() {
    const errorMsg = document.getElementById("schedError");
    const freq = document.getElementById("schedFreq")?.value;
    const cron = document.getElementById("schedCron")?.value;
    const date = document.getElementById("schedDate")?.value;
    const time = document.getElementById("schedTime")?.value;
    
    if (!date || !time) {
        showFormError("Please select both date and time");
        return false;
    }
    
    if (freq === "custom" && !cron) {
        showFormError("Please enter a valid cron expression");
        return false;
    }
    
    if (freq === "custom" && cron) {
        // Basic cron validation
        const cronPattern = /^(\*|([0-9]|[1-5][0-9])|\*\/([0-9]|[1-5][0-9]))\s+(\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3]))\s+(\*|([1-9]|[12][0-9]|3[01])|\*\/([1-9]|[12][0-9]|3[01]))\s+(\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2]))\s+(\*|([0-6])|\*\/([0-6]))$/;
        if (!cronPattern.test(cron)) {
            showFormError("Invalid cron expression format. Use: minute hour day month weekday");
            return false;
        }
    }
    
    hideFormError();
    return true;
}

function showFormError(message) {
    const errorMsg = document.getElementById("schedError");
    if (errorMsg) {
        errorMsg.textContent = message;
        errorMsg.classList.add('show');
    }
}

function hideFormError() {
    const errorMsg = document.getElementById("schedError");
    if (errorMsg) {
        errorMsg.classList.remove('show');
        errorMsg.textContent = '';
    }
}

function removeSchedule(id) {
    const element = document.querySelector(`.scraper-card[data-id="${id}"]`) || 
                   document.querySelector(`tr[data-id="${id}"]`);
    if (element) {
        element.style.transition = 'opacity 0.3s, transform 0.3s';
        element.style.opacity = '0';
        element.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            element.remove();
            showToast("Schedule removed successfully", 'success');
        }, 300);
    }
}

// ===================== LOGS PAGE =====================
const logs = [
    { id: '1', name: "Luxottica", status: "completed", timestamp: new Date().toISOString(), error: "-" },
    { id: '2', name: "Safilo", status: "failed", timestamp: new Date(Date.now() - 30 * 60000).toISOString(), error: "Timeout Error" }
];

function renderLogs() {
    const tbody = document.getElementById("logsTableBody");
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                    No logs available
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = "";
    logs.forEach(log => {
        tbody.innerHTML += `
            <tr data-id="${log.id}">
                <td>${log.name}</td>
                <td><span class="status ${log.status}">${log.status.toUpperCase()}</span></td>
                <td>${formatDate(log.timestamp)}</td>
                <td>${log.error}</td>
                <td>
                    <button class="view-log-btn" data-id="${log.id}" aria-label="View log details">
                        View logs
                    </button>
                </td>
            </tr>
        `;
    });
    
    // Attach log view events
    document.querySelectorAll(".view-log-btn").forEach(btn => {
        btn.onclick = (e) => {
            const logId = e.target.dataset.id || e.target.closest('[data-id]')?.dataset.id;
            const logData = logs.find(l => l.id === logId);
            if (logData) {
                showLogDetails(logData);
            }
        };
    });
}

function showLogDetails(logData) {
    const modalBody = document.getElementById("modalBody");
    if (modalBody) {
        modalBody.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div>
                    <strong style="color: var(--text-secondary); font-size: 0.875rem;">Scraper ID:</strong>
                    <p style="margin-top: 0.25rem;">${logData.id || 'N/A'}</p>
                </div>
                <div>
                    <strong style="color: var(--text-secondary); font-size: 0.875rem;">Name:</strong>
                    <p style="margin-top: 0.25rem;">${logData.name}</p>
                </div>
                <div>
                    <strong style="color: var(--text-secondary); font-size: 0.875rem;">Status:</strong>
                    <p style="margin-top: 0.25rem;">
                        <span class="status ${logData.status}">${logData.status.toUpperCase()}</span>
                    </p>
                </div>
                <div>
                    <strong style="color: var(--text-secondary); font-size: 0.875rem;">Timestamp:</strong>
                    <p style="margin-top: 0.25rem;">${formatDate(logData.timestamp)}</p>
                </div>
                <div>
                    <strong style="color: var(--text-secondary); font-size: 0.875rem;">Error:</strong>
                    <p style="margin-top: 0.25rem; color: ${logData.error !== '-' ? 'var(--danger)' : 'var(--text-secondary)'};">
                        ${logData.error}
                    </p>
                </div>
            </div>
        `;
        openModal("logModal");
    }
}

// ===================== SERVICE LOGS =====================
const serviceLogs = {
    "001": [
        { timestamp: new Date().toISOString(), status: "completed", message: "Sync finished successfully" },
        { timestamp: new Date(Date.now() - 30 * 60000).toISOString(), status: "failed", message: "Timeout error" }
    ],
    "002": [
        { timestamp: new Date(Date.now() - 120 * 60000).toISOString(), status: "completed", message: "Product push done" }
    ]
};

function attachServiceLogEvents() {
    document.querySelectorAll("tr[data-id] .view-log-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const row = e.target.closest("tr");
            const id = row?.dataset.id;
            
            if (!id) return;
            
            const logs = serviceLogs[id] || [];
            const body = document.getElementById("serviceLogBody");
            
            if (body) {
                if (logs.length === 0) {
                    body.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                            <p>No logs available for this service.</p>
                        </div>
                    `;
                } else {
                    body.innerHTML = logs.map(log => `
                        <div style="padding: 0.75rem; margin-bottom: 0.5rem; border-left: 3px solid ${log.status === 'completed' ? 'var(--success)' : 'var(--danger)'}; background: var(--bg-tertiary); border-radius: var(--radius-md);">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                <strong style="font-size: 0.875rem;">${formatDate(log.timestamp)}</strong>
                                <span class="status ${log.status}">${log.status.toUpperCase()}</span>
                            </div>
                            <p style="margin: 0; color: var(--text-secondary); font-size: 0.875rem;">${log.message}</p>
                        </div>
                    `).join("");
                }
                
                openModal("serviceLogModal");
            }
        });
    });
}

// ===================== INITIALIZE =====================
document.addEventListener("DOMContentLoaded", () => {
    // Initialize modals
    setupModal("logModal");
    setupModal("serviceLogModal");
    setupScheduleModal();
    
    // Render content based on page
    if (currentPage === "index.html") {
        renderScrapers();
    } else {
        attachScraperEvents();
        attachServiceLogEvents();
    }
    
    if (currentPage === "logs.html") {
        renderLogs();
    }
    
    // Handle table row events for services and schedules pages
    if (currentPage === "services.html" || currentPage === "schedules.html") {
        document.querySelectorAll("tr[data-id]").forEach(row => {
            const startBtn = row.querySelector(".start-btn");
            const stopBtn = row.querySelector(".stop-btn");
            const scheduleBtn = row.querySelector(".schedule-btn");
            const editBtn = row.querySelector(".edit-schedule-btn");
            const removeBtn = row.querySelector(".remove-schedule-btn");
            const viewLogBtn = row.querySelector(".view-log-btn");
            
            const id = row.dataset.id;
            
            if (startBtn && !startBtn.disabled) {
                startBtn.onclick = () => startScraper(id, startBtn);
            }
            
            if (stopBtn && !stopBtn.disabled) {
                stopBtn.onclick = () => stopScraper(id, stopBtn);
            }
            
            if (scheduleBtn) {
                scheduleBtn.onclick = () => openScheduleModal(id, row);
            }
            
            if (editBtn) {
                editBtn.onclick = () => openScheduleModal(id, row);
            }
            
            if (removeBtn) {
                removeBtn.onclick = () => {
                    if (confirm(`Are you sure you want to remove the schedule for this scraper?`)) {
                        removeSchedule(id);
                    }
                };
            }
        });
    }
    
    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.modal-open').forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
});
