// Global functions for HTML onclick handlers
function showMasterMessageView() {
    // Hide all other sections
    const vinLookupDiv = document.getElementById("vin-lookup");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const pickupMessageSection = document.getElementById("pickup-message-section");
    
    if (vinLookupDiv) vinLookupDiv.style.display = 'none';
    if (vinProfileDiv) vinProfileDiv.style.display = 'none';
    if (vinCreationDiv) vinCreationDiv.style.display = 'none';
    if (serviceRecordCreationDiv) serviceRecordCreationDiv.style.display = 'none';
    if (pickupMessageSection) pickupMessageSection.style.display = 'none';
    
    // Show master message view
    const masterView = document.getElementById('master-message-view');
    if (masterView) {
        masterView.style.display = 'block';
        // Default to reminder tab
        switchToTab('reminder');
    }
}

// Date helpers to fix timezone display behavior
function parseLocalDateFromYMD(ymdString) {
    // ymdString like '2025-08-09' → Date at local midnight
    if (!ymdString) return null;
    const [y, m, d] = ymdString.split('-').map(Number);
    return new Date(y, (m || 1) - 1, d || 1);
}
function dateFromUtcNaiveString(s) {
    // Backend sends naive UTC (no timezone). Append 'Z' for correct local conversion
    if (!s) return null;
    const hasTZ = /[zZ]|[+-]\d{2}:?\d{2}$/.test(s);
    return new Date(hasTZ ? s : s + 'Z');
}

// Global variables for message view state
let currentMessageTab = 'reminder';

function switchToTab(tabName) {
    currentMessageTab = tabName;
    
    // Update tab button styles
    document.getElementById('tab-pickup').style.backgroundColor = tabName === 'pickup' ? '#007bff' : '#6c757d';
    document.getElementById('tab-reminder').style.backgroundColor = tabName === 'reminder' ? '#007bff' : '#6c757d';
    document.getElementById('tab-sent-reminders').style.backgroundColor = tabName === 'sent' ? '#007bff' : '#6c757d';
    
    // Load the appropriate message type
    loadCurrentMessageType();
}

function loadCurrentMessageType(dateFilter = null) {
    // Get the date filter from the input if not provided
    if (dateFilter === null) {
        const dateInput = document.getElementById('date-filter');
        dateFilter = dateInput.value || null;
    }
    
    switch (currentMessageTab) {
        case 'pickup':
            loadPickupMessages(dateFilter);
            break;
        case 'reminder':
            loadReminderMessages(dateFilter);
            break;
        case 'sent':
            loadSentReminderMessages(dateFilter);
            break;
        default:
            loadReminderMessages(dateFilter);
            break;
    }
}

async function showInboundMessages() {
    // Mark all messages as read when the view is opened
    try {
        await makeApiCall('/messages/inbound/mark-as-read', 'POST');
        updateNotificationBadge(); // Update badge immediately
    } catch (error) {
        console.error("Error marking messages as read:", error);
    }

    // Hide all other sections
    const vinLookupDiv = document.getElementById("vin-lookup");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const pickupMessageSection = document.getElementById("pickup-message-section");

    if (vinLookupDiv) vinLookupDiv.style.display = 'none';
    if (vinProfileDiv) vinProfileDiv.style.display = 'none';
    if (vinCreationDiv) vinCreationDiv.style.display = 'none';
    if (serviceRecordCreationDiv) serviceRecordCreationDiv.style.display = 'none';
    if (pickupMessageSection) pickupMessageSection.style.display = 'none';

    // Show the master message view and load inbound messages
    const masterView = document.getElementById('master-message-view');
    if (!masterView) return;

    masterView.style.display = 'block';
    const content = document.getElementById('master-message-content');
    content.innerHTML = '<p>Loading inbound messages...</p>';

    try {
        const result = await makeApiCall('/messages/inbound');
        if (result.success) {
            const data = result.data;
            if (data.messages.length === 0) {
                content.innerHTML = '<p>No inbound messages found.</p>';
                return;
            }

            const messagesHtml = data.messages.map(msg => `
                <div class="master-message-item inbound">
                    <div class="message-header">
                        <strong>From: ${msg.contact_name || 'Unknown'}</strong> (${msg.from_number})
                    </div>
                    <div class="message-content">
                        <p>${msg.body}</p>
                    </div>
                    <div class="message-details">
                        <small><strong>Received:</strong> ${dateFromUtcNaiveString(msg.created_at).toLocaleString()}</small>
                    </div>
                </div>
            `).join('');

            content.innerHTML = `
                <div class="master-message-container">
                    <h3>📥 Inbound Messages</h3>
                    <p><strong>Total Messages:</strong> ${data.messages.length}</p>
                    ${messagesHtml}
                </div>
            `;
        } else {
            content.innerHTML = `<p>Error loading inbound messages: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading inbound messages:", error);
        content.innerHTML = '<p>An error occurred while loading inbound messages.</p>';
    }
}

// --- Notification System ---
async function updateNotificationBadge() {
    try {
        const result = await makeApiCall('/messages/inbound/unread-count');
        const badge = document.getElementById('inbound-notification-badge');
        const inboundButton = document.querySelector('button[onclick="showInboundMessages()"]');

        if (result.success && result.data.unread_count > 0) {
            badge.textContent = `[${result.data.unread_count}]`;
            badge.style.display = 'flex';
            if (inboundButton) {
                inboundButton.style.backgroundColor = '#dc3545'; // A standard red color
            }
        } else {
            badge.style.display = 'none';
            if (inboundButton) {
                inboundButton.style.backgroundColor = '#28a745'; // The original green color
            }
        }
    } catch (error) {
        console.error("Error updating notification badge:", error);
    }
}

// Check for new messages periodically
setInterval(updateNotificationBadge, 20000); // Check every 20 seconds

// Also check once on initial page load
document.addEventListener('DOMContentLoaded', updateNotificationBadge);

async function loadMasterMessages(dateFilter = null) {
    const content = document.getElementById('master-message-content');
    if (!content) return;
    
    content.innerHTML = '<p>Loading messages...</p>';

    try {
        const url = dateFilter ? `/messages/all-outbound?date=${dateFilter}` : '/messages/all-outbound';
        const result = await makeApiCall(url);
        
        if (result.success) {
            const data = result.data;
            if (data.messages.length === 0) {
                content.innerHTML = '<p>No messages found for the selected criteria.</p>';
                return;
            }

            const messagesHtml = data.messages.map(msg => `
                <div class="master-message-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="vehicle-info">
                        <strong>Vehicle:</strong> ${msg.vehicle_info} (${msg.vin_string})
                    </div>
                    <div class="message-content">
                        <p><strong>${msg.is_reminder ? '🔄 Reminder' : '📱 Pickup'}:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Scheduled:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                            ${msg.sent_at ? `<br><strong>Sent:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            content.innerHTML = `
                <div class="master-message-container">
                    <h3>All Outbound Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3>
                    <p><strong>Total Messages:</strong> ${data.total_messages}</p>
                    ${messagesHtml}
                </div>
            `;
        } else {
            content.innerHTML = `<p>Error loading messages: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading master messages:", error);
        content.innerHTML = '<p>Error loading messages.</p>';
    }
}

async function loadPickupMessages(dateFilter = null) {
    const content = document.getElementById('master-message-content');
    if (!content) return;
    
    content.innerHTML = '<p>Loading pickup messages...</p>';

    try {
        const url = dateFilter ? `/messages/pickup-messages?date=${dateFilter}` : '/messages/pickup-messages';
        const result = await makeApiCall(url);
        
        if (result.success) {
            const data = result.data;
            if (data.messages.length === 0) {
                content.innerHTML = '<p>No pickup messages found for the selected criteria.</p>';
                return;
            }

            const messagesHtml = data.messages.map(msg => `
                <div class="master-message-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="vehicle-info">
                        <strong>Vehicle:</strong> ${msg.vehicle_info} (${msg.vin_string})
                    </div>
                    <div class="message-content">
                        <p><strong>📱 Pickup:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Sent:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                            ${msg.sent_at ? `<br><strong>Delivered:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            content.innerHTML = `
                <div class="master-message-container">
                    <h3>📱 Pickup Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3>
                    <p><strong>Total Pickup Messages:</strong> ${data.total_messages}</p>
                    ${messagesHtml}
                </div>
            `;
        } else {
            content.innerHTML = `<p>Error loading pickup messages: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading pickup messages:", error);
        content.innerHTML = '<p>Error loading pickup messages.</p>';
    }
}

// Use created-date filter for reminders in master view
async function loadReminderMessages(dateFilter = null) {
    const content = document.getElementById('master-message-content');
    if (!content) return;
    
    content.innerHTML = '<p>Loading reminder messages...</p>';

    try {
        // Default: filter by created_at (when scheduled)
        const url = dateFilter ? `/messages/reminder-messages-created?date=${dateFilter}` : '/messages/reminder-messages-created';
        const result = await makeApiCall(url);
        
        if (result.success) {
            const data = result.data;
            if (data.messages.length === 0) {
                content.innerHTML = '<p>No reminder messages found for the selected criteria.</p>';
                return;
            }

            const messagesHtml = data.messages.map(msg => `
                <div class="master-message-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : msg.status === 'canceled' ? 'canceled' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="vehicle-info">
                        <strong>Vehicle:</strong> ${msg.vehicle_info} (${msg.vin_string})
                    </div>
                    <div class="message-content">
                        <p><strong>🔄 Reminder:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Scheduled for:</strong> ${new Date(msg.scheduled_time).toLocaleString()}<br>
                            <strong>Created:</strong> ${msg.created_at ? new Date(msg.created_at).toLocaleString() : '—'}
                            ${msg.sent_at ? `<br><strong>Sent:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            content.innerHTML = `
                <div class="master-message-container">
                    <h3>🔄 Reminder Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3>
                    <p><strong>Total Reminder Messages:</strong> ${data.total_messages}</p>
                    ${messagesHtml}
                </div>
            `;
        } else {
            content.innerHTML = `<p>Error loading reminder messages: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading reminder messages:", error);
        content.innerHTML = '<p>Error loading reminder messages.</p>';
    }
}

async function loadSentReminderMessages(dateFilter = null) {
    const content = document.getElementById('master-message-content');
    if (!content) return;
    content.innerHTML = '<p>Loading sent reminders...</p>';
    try {
        const url = dateFilter ? `/messages/sent-reminders?date=${dateFilter}` : '/messages/sent-reminders';
        const result = await makeApiCall(url);
        if (result.success) {
            const data = result.data;
            const html = withCancelMarkup('', data.messages); // no cancel shown because status is sent
            content.innerHTML = `<div class="master-message-container"><h3>✅ Sent Reminders ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3><p><strong>Total:</strong> ${data.total_messages}</p>${html}</div>`;
        } else {
            content.innerHTML = `<p>Error loading sent reminders: ${result.error.detail}</p>`;
        }
    } catch (e) {
        console.error('Error loading sent reminders', e);
        content.innerHTML = '<p>Error loading sent reminders.</p>';
    }
}

// Badge updater: show/hide the "Pickup Sent" badge for a given service record
async function updatePickupSentBadge(serviceRecordId) {
    try {
        const result = await makeApiCall(`/messages/service-record/${serviceRecordId}/pickup-sent`);
        const pickupSent = result && result.success && result.data && result.data.pickup_sent;
        const badge = document.getElementById(`pickup-badge-${serviceRecordId}`);
        if (badge) {
            badge.style.display = pickupSent ? 'inline-block' : 'none';
            if (pickupSent) {
                badge.title = 'A pickup message has already been sent for this service record.';
            }
        }
    } catch (err) {
        console.error('Failed to update pickup-sent badge for service record', serviceRecordId, err);
    }
}

// Global API call helper function
async function makeApiCall(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, options);
        // Clone the response so we can read its body multiple times if needed
        const clonedResponse = response.clone(); 

        let data;
        try {
            data = await response.json(); // Try to read original response as JSON
        } catch (jsonError) {
            // If JSON parsing fails, read the cloned response as text
            data = await clonedResponse.text(); 
        }

        if (response.ok) {
            return { success: true, data: data };
        } else {
            const errorMessage = (data && typeof data === 'object' && data.detail)
                                 ? data.detail
                                 : (data || `HTTP Error: ${response.status}`);
            return { success: false, error: { status: response.status, detail: errorMessage } };
        }
    } catch (networkError) {
        console.error("Network or unexpected error:", networkError);
        return { success: false, error: { status: 0, detail: "Network error or unexpected issue." } };
    }
}

async function loadMessageHistory(vinId) {
    const historyContent = document.getElementById('message-history-content');
    if (!historyContent) return;
    
    historyContent.innerHTML = '<p>Loading message history...</p>';

    try {
        const result = await makeApiCall(`/messages/vin/${vinId}/history`);
        
        if (result.success) {
            const history = result.data;
            if (history.message_history.length === 0) {
                historyContent.innerHTML = '<p>No message history found for this vehicle.</p>';
                return;
            }

            const historyHtml = history.message_history.map(msg => `
                <div class="message-history-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="message-content">
                        <p><strong>${msg.is_reminder ? '🔄 Reminder' : '📱 Pickup'}:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Scheduled:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                            ${msg.sent_at ? `<br><strong>Sent:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            historyContent.innerHTML = `
                <div class="master-message-container">
                    <h3>All Outbound Messages ${history.date_filter ? `(${history.date_filter})` : '(All Time)'}</h3>
                    <p><strong>Total Messages:</strong> ${history.total_messages}</p>
                    ${historyHtml}
                </div>
            `;
        } else {
            historyContent.innerHTML = `<p>Error loading message history: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading message history:", error);
        historyContent.innerHTML = '<p>Error loading message history.</p>';
    }
}

async function loadPickupHistory(vinId) {
    const historyContent = document.getElementById('message-history-content');
    if (!historyContent) return;
    
    historyContent.innerHTML = '<p>Loading pickup history...</p>';

    try {
        const result = await makeApiCall(`/messages/vin/${vinId}/pickup-history`);
        
        if (result.success) {
            const history = result.data;
            if (history.pickup_history.length === 0) {
                historyContent.innerHTML = '<p>No pickup messages found for this vehicle.</p>';
                return;
            }

            const historyHtml = history.pickup_history.map(msg => `
                <div class="message-history-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="message-content">
                        <p><strong>📱 Pickup:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Sent:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                            ${msg.sent_at ? `<br><strong>Delivered:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            historyContent.innerHTML = `
                <div class="message-history-container">
                    <h5>📱 Pickup Messages - ${history.vehicle_info} (${history.vin_string})</h5>
                    ${historyHtml}
                </div>
            `;
        } else {
            historyContent.innerHTML = `<p>Error loading pickup history: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading pickup history:", error);
        historyContent.innerHTML = '<p>Error loading pickup history.</p>';
    }
}

async function loadReminderHistory(vinId) {
    const historyContent = document.getElementById('message-history-content');
    if (!historyContent) return;
    
    historyContent.innerHTML = '<p>Loading reminder history...</p>';

    try {
        const result = await makeApiCall(`/messages/vin/${vinId}/reminder-history`);
        
        if (result.success) {
            const history = result.data;
            if (history.reminder_history.length === 0) {
                historyContent.innerHTML = '<p>No reminder messages found for this vehicle.</p>';
                return;
            }

            const historyHtml = history.reminder_history.map(msg => `
                <div class="message-history-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : 'pending'}">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                    </div>
                    <div class="message-content">
                        <p><strong>🔄 Reminder:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Scheduled for:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                            ${msg.sent_at ? `<br><strong>Sent:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                        </small>
                    </div>
                </div>
            `).join('');

            historyContent.innerHTML = `
                <div class="message-history-container">
                    <h5>🔄 Reminder Messages - ${history.vehicle_info} (${history.vin_string})</h5>
                    ${historyHtml}
                </div>
            `;
        } else {
            historyContent.innerHTML = `<p>Error loading reminder history: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error("Error loading reminder history:", error);
        historyContent.innerHTML = '<p>Error loading reminder history.</p>';
    }
}

// Global function for VIN message tab switching
function switchVinMessageTab(tabName, vinId) {
    // Update tab button styles
    document.getElementById('vin-tab-pickup').style.backgroundColor = tabName === 'pickup' ? '#007bff' : '#6c757d';
    document.getElementById('vin-tab-reminder').style.backgroundColor = tabName === 'reminder' ? '#007bff' : '#6c757d';
    const sentBtn = document.getElementById('vin-tab-sent-reminders');
    if (sentBtn) sentBtn.style.backgroundColor = tabName === 'sent' ? '#007bff' : '#6c757d';
    
    // Load the appropriate message type
    switch (tabName) {
        case 'pickup':
            loadPickupHistory(vinId);
            break;
        case 'reminder':
            loadReminderHistory(vinId);
            break;
        case 'sent':
            loadSentReminderHistory(vinId);
            break;
        default:
            loadPickupHistory(vinId);
            break;
    }
}

// VIN-specific Sent Reminders loader (filters reminder history for status sent)
async function loadSentReminderHistory(vinId) {
    const historyContent = document.getElementById('message-history-content');
    if (!historyContent) return;

    historyContent.innerHTML = '<p>Loading sent reminders...</p>';

    try {
        const result = await makeApiCall(`/messages/vin/${vinId}/reminder-history`);
        if (result.success) {
            const history = result.data;
            const sentOnly = (history.reminder_history || []).filter(msg => msg.status === 'sent');
            if (sentOnly.length === 0) {
                historyContent.innerHTML = '<p>No sent reminders for this vehicle yet.</p>';
                return;
            }

            const historyHtml = sentOnly.map(msg => `
                <div class="message-history-item sent">
                    <div class="message-header">
                        <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                        <span class="message-status sent">SENT</span>
                    </div>
                    <div class="message-content">
                        <p><strong>🔄 Reminder:</strong> ${msg.message_content}</p>
                    </div>
                    <div class="message-details">
                        <small>
                            <strong>Scheduled for:</strong> ${new Date(msg.scheduled_time).toLocaleString()}<br>
                            <strong>Sent:</strong> ${msg.sent_at ? new Date(msg.sent_at).toLocaleString() : '—'}
                        </small>
                    </div>
                </div>
            `).join('');

            historyContent.innerHTML = `
                <div class="message-history-container">
                    <h5>✅ Sent Reminders - ${history.vehicle_info} (${history.vin_string})</h5>
                    ${historyHtml}
                </div>
            `;
        } else {
            historyContent.innerHTML = `<p>Error loading sent reminders: ${result.error.detail}</p>`;
        }
    } catch (error) {
        console.error('Error loading sent reminders:', error);
        historyContent.innerHTML = '<p>Error loading sent reminders.</p>';
    }
}

// Global function for service record pickup flow
async function handlePickupFlow(serviceRecordId) {
    console.log("DEBUG: Starting pickup flow for service record ID:", serviceRecordId);
    
    // Get DOM elements
    const vinLookupDiv = document.getElementById("vin-lookup");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const pickupMessageSection = document.getElementById("pickup-message-section");

    if (!pickupMessageSection) {
        console.error("Pickup message section not found");
        return;
    }

    // 1. Hide the main content and show the pickup section
    if (vinLookupDiv) vinLookupDiv.style.display = 'none';
    if (vinProfileDiv) vinProfileDiv.style.display = 'none';
    if (vinCreationDiv) vinCreationDiv.style.display = 'none';
    if (serviceRecordCreationDiv) serviceRecordCreationDiv.style.display = 'none';
    pickupMessageSection.style.display = 'block';

    // Show loading state
    pickupMessageSection.innerHTML = '<h2>Loading service record...</h2>';

    // 2. Fetch the service record data
    const result = await makeApiCall(`/service-record/${serviceRecordId}`);
    console.log("DEBUG: Service record API result:", result);

    if (!result.success) {
        pickupMessageSection.innerHTML = `
            <div style="text-align: center; margin-bottom: 20px;">
                <button onclick="window.location.href='./'" style="background-color: #6c757d; margin-bottom: 10px;">← Back to Main</button>
            </div>
            <h2>Error Loading Service Record</h2>
            <p>Could not load service record data: ${result.error.detail}</p>
        `;
        return;
    }

    const serviceRecord = result.data;
    const vin = serviceRecord.vin; // This is the VIN object nested inside the service record
    console.log("DEBUG: Service record data:", serviceRecord);
    console.log("DEBUG: VIN data:", vin);
    
    if (!vin) {
        pickupMessageSection.innerHTML = `
            <div style="text-align: center; margin-bottom: 20px;">
                <button onclick="window.location.href='./'" style="background-color: #6c757d; margin-bottom: 10px;">← Back to Main</button>
            </div>
            <h2>Error</h2>
            <p>VIN data is missing from the service record.</p>
        `;
        return;
    }
    const contacts = vin.contacts || []; // Access contacts from the vin object
    console.log("DEBUG: Contacts for pickup flow:", contacts);

    // 3. Render the initial UI for the pickup flow
    renderPickupUI(serviceRecord, vin, contacts);

    // 4. Setup event listeners for the new UI
    setupPickupFlowEvents(serviceRecord, vin, contacts);
}

// Global confirmation functions for safety
function confirmSendToAllContacts(serviceRecordId, contactCount) {
    if (confirm(`Are you sure you want to send pickup messages to all ${contactCount} contacts?\n\nThis action cannot be undone.`)) {
        // Get the contacts from the current pickup flow
        const contactCards = document.querySelectorAll('#pickup-contact-list .contact-card');
        const contacts = Array.from(contactCards).map(card => ({
            id: card.querySelector('.send-msg-btn').dataset.contactId
        }));
        sendToAllContacts(serviceRecordId, contacts);
    }
}

function confirmSkipMessages() {
    if (confirm("Are you sure you want to skip sending messages?\n\nYou can always come back to send messages later.")) {
        window.location.href = './';
    }
}

// Global functions for pickup flow
function renderPickupUI(serviceRecord, vin, contacts) {
    console.log("DEBUG: Contacts received by renderPickupUI:", contacts);
    const pickupMessageSection = document.getElementById("pickup-message-section");
    if (!pickupMessageSection) {
        console.error("Pickup message section not found");
        return;
    }

    const contactsHtml = contacts.length > 0
        ? contacts.map(contact => `
            <div class="contact-card">
                <p><strong>Name:</strong> <span>${contact.name}</span></p>
                <p><strong>Phone:</strong> <span>${contact.phone_number}</span></p>
                <button class="send-msg-btn" data-contact-id="${contact.id}">📱 Send Pickup Message</button>
                <div class="message-status" id="status-${contact.id}" style="display: none;">
                    <span style="color: #28a745; font-size: 12px;">✓ Message sent</span>
                </div>
            </div>
        `).join("")
        : "<p>No contacts associated with this vehicle. Please add a contact below to send a pickup message.</p>";

    pickupMessageSection.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="window.location.href='./'" style="background-color: #6c757d; margin-bottom: 10px;">← Back to Main</button>
            <button onclick="window.location.href='./'" style="background-color: #28a745; margin-left: 10px;">✓ Done</button>
        </div>
        <h2>Send Pickup Message</h2>
        <h3>Vehicle: ${vin.year} ${vin.make} ${vin.model} (${vin.vin})</h3>
        <p><strong>Service Date:</strong> ${serviceRecord.service_date}</p>
        <p><strong>Mileage:</strong> ${serviceRecord.mileage_at_service}</p>
        
        <div style="margin: 20px 0; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #28a745;">
            <h4 style="margin-top: 0; color: #155724;">Service Summary:</h4>
            <p><strong>Oil Type:</strong> ${serviceRecord.oil_type} (${serviceRecord.oil_viscosity})</p>
            <p><strong>Next Service:</strong> ${serviceRecord.next_service_date_due} or ${serviceRecord.next_service_mileage_due} miles</p>
            ${serviceRecord.notes ? `<p><strong>Notes:</strong> ${serviceRecord.notes}</p>` : ''}
        </div>
        
        ${contacts.length > 0 ? `
            <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h4 style="margin-top: 0;">Quick Actions:</h4>
                <button onclick="confirmSendToAllContacts(${serviceRecord.id}, ${contacts.length})" style="background-color: #007bff; margin-right: 10px;">
                    📤 Send to All Contacts (${contacts.length})
                </button>
                <button onclick="confirmSkipMessages()" style="background-color: #ffc107; color: #000;">
                    ⏭️ Skip Messages
                </button>
            </div>
        ` : ''}
        
        <h4>Select a contact to notify:</h4>
        <div id="pickup-contact-list">
            ${contactsHtml}
        </div>

        <hr>

        <h4>Or add a new contact:</h4>
        <div id="contact-management-pickup">
            <h5>Create New Contact</h5>
            <form id="create-contact-form-pickup">
                <input type="text" name="name" placeholder="Name" required>
                <input type="text" name="phone_number" placeholder="Phone Number" required>
                <input type="email" name="email" placeholder="Email (Optional)">
                <button type="submit">Create and Add Contact</button>
            </form>

            <h5>Link Existing Contact</h5>
            <form id="link-contact-form-pickup">
                <input type="text" id="search_contact_phone_pickup" placeholder="Search by Phone Number">
                <div id="search_results_list_pickup"></div>
                <input type="hidden" id="selected_contact_id_pickup">
                <button type="submit" id="link_contact_button_pickup" disabled>Link Selected Contact</button>
            </form>
        </div>
    `;
}

function setupPickupFlowEvents(serviceRecord, vin, contacts) {
    const pickupContactList = document.getElementById('pickup-contact-list');
    if (!pickupContactList) {
        console.error("Pickup contact list not found");
        return;
    }

    pickupContactList.addEventListener('click', (e) => {
        if (e.target.classList.contains('send-msg-btn')) {
            const contactId = e.target.dataset.contactId;
            const contact = contacts.find(c => c.id == contactId);
            if (contact) {
                showPickupMessageComposer(serviceRecord, vin, contact);
            }
        }
    });

    // Setup event listeners for contact management forms in pickup flow
    setupPickupContactEvents(serviceRecord.vin.id, serviceRecord.vin.vin, serviceRecord, contacts);
}

function showPickupMessageComposer(serviceRecord, vin, contact) {
    const modal = document.getElementById('message-composer-modal');
    const closeBtn = modal.querySelector('.close-btn');

    // Populate composer fields
    document.getElementById('composer-title').textContent = `Send Pickup Message to ${contact.name}`;
    document.getElementById('composer-contact-name').textContent = contact.name;
    document.getElementById('composer-contact-phone').textContent = contact.phone_number;
    document.getElementById('composer_contact_id').value = contact.id;
    document.getElementById('composer_service_record_id').value = serviceRecord.id;

    // Pre-populate the immediate message
    const immediateMessage = (
        `Hi ${contact.name}, your ${vin.make} ${vin.model} is ready! ` +
        `${serviceRecord.oil_type.replace('_', ' ')} (${serviceRecord.oil_viscosity}) done at ${serviceRecord.mileage_at_service} mi. ` +
        `Next due: ${serviceRecord.next_service_mileage_due} on ${parseLocalDateFromYMD(serviceRecord.next_service_date_due).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}. ` +
        "Thank you for choosing Montebello Lube N' Tune - 2130 W Beverly Blvd. Mon-Sat 8-5. (323) 727-2883. " +
        "Reply STOP to unsubscribe."
    );
    document.getElementById('composer_message').value = immediateMessage;

    // Show reminder details
    const formattedNextDate = parseLocalDateFromYMD(serviceRecord.next_service_date_due).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    document.getElementById('reminder-date').textContent = formattedNextDate;
    document.getElementById('reminder-mileage').textContent = serviceRecord.next_service_mileage_due;
    const oilHuman = serviceRecord.oil_type ? serviceRecord.oil_type.replace(/_/g, ' ') : '';
    const lastMileage = serviceRecord.mileage_at_service; // fallback; backend uses previous service if available
    const reminderPreview = (
        `Hi ${contact.name}! Your ${vin.model} is due soon: ` +
        `${serviceRecord.next_service_mileage_due} mi on ${formattedNextDate}. ` +
        `Last: ${lastMileage} with ${oilHuman} (${serviceRecord.oil_viscosity}). ` +
        "Thank you for choosing Montebello Lube N' Tune - 2130 W Beverly Blvd. Mon-Sat 8-5. (323) 727-2883. " +
        "Reply STOP to unsubscribe."
    );
    // Render with line breaks removed for concise SMS
    const previewEl = document.getElementById('reminder-message-preview');
    if (previewEl) {
        previewEl.innerHTML = reminderPreview;
    }

    // Show the modal
    modal.style.display = 'block';

    // Close button functionality
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Close modal if user clicks outside of it
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Handle message form submission
    const sendMessageForm = document.getElementById('send-message-form');
    sendMessageForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(sendMessageForm);
        const messageData = Object.fromEntries(formData.entries());

        // Show loading state
        const submitButton = sendMessageForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Sending...';
        submitButton.disabled = true;

        try {
            const result = await makeApiCall("/messages/send", 'POST', {
                service_record_id: parseInt(messageData.service_record_id),
                contact_id: parseInt(messageData.contact_id),
                immediate_message_content: messageData.message
            });

            if (result.success) {
                const deliveryStatus = result.data.sms_sent ? "✅ Sent via SMS" : "⚠️ SMS not configured, but reminder scheduled";
                alert(`Message sent and reminder scheduled successfully!\n\n${deliveryStatus}`);
                modal.style.display = 'none';
                
                // Redirect to VIN profile for this vehicle so the user can see logs
                const targetUrl = `${window.location.pathname}?vin_or_last6=${encodeURIComponent(vin.vin)}`;
                window.location.href = targetUrl;
            } else {
                alert(`Error sending message: ${result.error.detail}`);
            }
        } catch (error) {
            console.error("Error sending message:", error);
            alert("An unexpected error occurred while sending the message.");
        } finally {
            // Restore button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    };
}

function setupPickupContactEvents(currentVinId, currentVinString, serviceRecord, contacts) {
    let searchTimeout;

    // Event listener for pickup contact forms
    const pickupMessageSection = document.getElementById("pickup-message-section");
    if (!pickupMessageSection) return;

    pickupMessageSection.addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;

        if (form.id === "create-contact-form-pickup") {
            const formData = new FormData(form);
            const contactData = Object.fromEntries(formData.entries());

            const result = await makeApiCall("/contacts/", 'POST', contactData);

            if (result.success) {
                alert(`Contact ${result.data.name} created successfully! Now linking to VIN.`);
                const linkResult = await linkContactToVin(result.data.id, currentVinId);
                if (linkResult.success) {
                    alert("Contact linked successfully!");
                    // Update the local contacts list instead of page reload
                    contacts.push(result.data);
                    renderPickupUI(serviceRecord, serviceRecord.vin, contacts);
                } else {
                    alert(`Error linking contact: ${linkResult.error.detail}`);
                }
                form.reset();
            } else {
                alert(`Error creating contact: ${result.error.detail}`);
            }
        } else if (form.id === "link-contact-form-pickup") {
            const selectedContactIdInput = document.getElementById("selected_contact_id_pickup");
            const contactIdToLink = selectedContactIdInput.value;
            if (!contactIdToLink) {
                alert("Please select a contact to link from the search results.");
                return;
            }
            const result = await linkContactToVin(contactIdToLink, currentVinId);
            if (result.success) {
                alert("Contact linked successfully!");
                // Refresh the pickup UI to show the new contact
                handlePickupFlow(serviceRecord.id);
            } else if (result.error && result.error.detail === "Contact already linked to this VIN") {
                alert("This contact is already linked to the current VIN.");
            } else {
                alert(`Error linking contact: ${result.error.detail}`);
            }
        }
    });

    // Event listener for input changes in pickup flow
    pickupMessageSection.addEventListener("input", async (e) => {
        if (e.target.id === "search_contact_phone_pickup") {
            const searchContactPhoneInput = e.target;
            const searchResultsList = document.getElementById("search_results_list_pickup");
            const selectedContactIdInput = document.getElementById("selected_contact_id_pickup");
            const linkContactButton = document.getElementById("link_contact_button_pickup");

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                const phoneNumber = searchContactPhoneInput.value.trim();
                if (phoneNumber.length >= 3) {
                    const foundContacts = await searchContacts(phoneNumber);
                    searchResultsList.innerHTML = ""; // Clear previous results
                    if (foundContacts.length === 0) {
                        searchResultsList.innerHTML = "<p>No contacts found.</p>";
                        selectedContactIdInput.value = "";
                        linkContactButton.disabled = true;
                        return;
                    }

                    foundContacts.forEach(contact => {
                        const resultItem = document.createElement("div");
                        resultItem.classList.add("search-result-item");
                        resultItem.innerHTML = `<strong>${contact.name}</strong> (${contact.phone_number})`;
                        resultItem.dataset.contactId = contact.id;
                        resultItem.addEventListener("click", () => {
                            selectedContactIdInput.value = contact.id;
                            searchContactPhoneInput.value = `${contact.name} (${contact.phone_number})`;
                            searchResultsList.innerHTML = "";
                            linkContactButton.disabled = false;
                        });
                        searchResultsList.appendChild(resultItem);
                    });
                } else {
                    searchResultsList.innerHTML = "";
                    selectedContactIdInput.value = "";
                    linkContactButton.disabled = true;
                }
            }, 300);
        }
    });

    // Event listener for clicks in pickup flow
    pickupMessageSection.addEventListener("click", (e) => {
        const resultItem = e.target.closest(".search-result-item");
        if (resultItem) {
            const selectedContactIdInput = document.getElementById("selected_contact_id_pickup");
            const searchContactPhoneInput = document.getElementById("search_contact_phone_pickup");
            const searchResultsList = document.getElementById("search_results_list_pickup");
            const linkContactButton = document.getElementById("link_contact_button_pickup");

            const contactId = resultItem.dataset.contactId;
            const contactNamePhone = resultItem.textContent;

            selectedContactIdInput.value = contactId;
            searchContactPhoneInput.value = contactNamePhone;
            searchResultsList.innerHTML = "";
            linkContactButton.disabled = false;
        }
    });
}

// Helper functions that need to be global
async function searchContacts(phoneNumber) {
    try {
        const response = await fetch(`/contacts/search?phone_number=${phoneNumber}`);
        if (response.ok) {
            const contacts = await response.json();
            return contacts;
        } else {
            console.error("Failed to search contacts.");
            return [];
        }
    } catch (error) {
        console.error("Error searching contacts:", error);
        return [];
    }
}

async function linkContactToVin(contactId, vinId) {
    const result = await makeApiCall(`/contacts/${contactId}/link_to_vin/${vinId}`, 'POST');
    return result;
}
    
    async function sendToAllContacts(serviceRecordId, contacts) {
        if (!confirm(`Send pickup message to all ${contacts.length} contacts?`)) {
            return;
        }

        const immediateMessage = `Your vehicle is ready for pickup. Service completed.`;
        
        for (const contact of contacts) {
            try {
                const result = await makeApiCall("/messages/send", 'POST', {
                    service_record_id: serviceRecordId,
                    contact_id: contact.id,
                    immediate_message_content: immediateMessage
                });

                if (result.success) {
                    console.log(`Message sent to ${contact.name}`);
                } else {
                    console.error(`Failed to send to ${contact.name}: ${result.error.detail}`);
                }
            } catch (error) {
                console.error(`Error sending to ${contact.name}:`, error);
            }
        }

        alert(`Messages sent to ${contacts.length} contacts!`);
    window.location.href = window.location.pathname;
}

// Add cancel action rendering in message items (master views)
function renderCancelButton(msg) {
    if (msg.status !== 'pending') return '';
    return `<button class="cancel-msg-btn" data-message-id="${msg.id}" style="background:#dc3545;margin-left:8px;">Cancel</button>`;
}

// Hook master view containers to cancel clicks
function attachMasterCancelHandlers() {
    const content = document.getElementById('master-message-content');
    if (!content) return;
    if (content.dataset.cancelHandlerAttached === 'true') return; // attach once
    content.addEventListener('click', async (e) => {
        const btn = e.target.closest('.cancel-msg-btn');
        if (!btn) return;
        const id = btn.getAttribute('data-message-id');
        if (!confirm('Cancel this scheduled message?')) return;
        const res = await makeApiCall(`/messages/message/${id}/cancel`, 'POST');
        if (res.success) {
            const item = btn.closest('.master-message-item');
            if (item) {
                const statusEl = item.querySelector('.message-status');
                if (statusEl) {
                    statusEl.textContent = 'CANCELED';
                    statusEl.className = 'message-status canceled';
                }
            }
            btn.remove();
            } else {
            alert(`Failed to cancel: ${res.error?.detail || 'Unknown error'}`);
        }
    });
    content.dataset.cancelHandlerAttached = 'true';
}

// Inject cancel buttons into master list renderers
// Patch loadMasterMessages
const _origLoadMasterMessages = loadMasterMessages;
loadMasterMessages = async function(dateFilter = null){
    await _origLoadMasterMessages.apply(this, [dateFilter]);
    attachMasterCancelHandlers();
    const content = document.getElementById('master-message-content');
    if (!content) return;
    content.querySelectorAll('.master-message-item').forEach((node, idx) => {
        const idMatch = node.innerHTML.match(/data-message-id=\"(\d+)\"/);
        if (!idMatch) {
            // best-effort: cannot inject id after render; re-render with buttons next time
        }
    });
}

// Override list builders to include cancel button
function withCancelMarkup(messagesHtml, messages) {
    // naive replace by rebuilding items with buttons
    return messages.map(msg => `
        <div class="master-message-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : msg.status === 'canceled' ? 'canceled' : 'pending'}">
            <div class="message-header">
                <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                ${renderCancelButton(msg)}
            </div>
            <div class="vehicle-info">
                <strong>Vehicle:</strong> ${msg.vehicle_info} (${msg.vin_string})
            </div>
            <div class="message-content">
                <p><strong>${msg.is_reminder ? '🔄 Reminder' : '📱 Pickup'}:</strong> ${msg.message_content}</p>
            </div>
            <div class="message-details">
                <small>
                    <strong>Scheduled:</strong> ${dateFromUtcNaiveString(msg.scheduled_time).toLocaleString()}
                    ${msg.sent_at ? `<br><strong>Sent:</strong> ${dateFromUtcNaiveString(msg.sent_at).toLocaleString()}` : ''}
                </small>
            </div>
        </div>
    `).join('');
}

// Wrap master loaders to use cancel markup
const _lm = loadMasterMessages;
loadMasterMessages = async function(dateFilter = null){
    const content = document.getElementById('master-message-content');
    if (!content) return;
    content.innerHTML = '<p>Loading messages...</p>';
    const url = dateFilter ? `/messages/all-outbound?date=${dateFilter}` : '/messages/all-outbound';
    const result = await makeApiCall(url);
    if (result.success) {
        const data = result.data;
        const html = withCancelMarkup('', data.messages);
        content.innerHTML = `<div class="master-message-container"><h3>All Outbound Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3><p><strong>Total Messages:</strong> ${data.total_messages}</p>${html}</div>`;
        attachMasterCancelHandlers();
    } else {
        content.innerHTML = `<p>Error loading messages: ${result.error.detail}</p>`;
    }
}

// Do the same for reminder-only and pickup-only views
const _lpm = loadPickupMessages;
loadPickupMessages = async function(dateFilter = null){
    const content = document.getElementById('master-message-content');
    if (!content) return;
    content.innerHTML = '<p>Loading pickup messages...</p>';
    const url = dateFilter ? `/messages/pickup-messages?date=${dateFilter}` : '/messages/pickup-messages';
    const result = await makeApiCall(url);
    if (result.success) {
        const data = result.data;
        const html = withCancelMarkup('', data.messages);
        content.innerHTML = `<div class="master-message-container"><h3>📱 Pickup Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3><p><strong>Total Pickup Messages:</strong> ${data.total_messages}</p>${html}</div>`;
        attachMasterCancelHandlers();
    } else {
        content.innerHTML = `<p>Error loading pickup messages: ${result.error.detail}</p>`;
    }
}

const _lrm = loadReminderMessages;
loadReminderMessages = async function(dateFilter = null){
    const content = document.getElementById('master-message-content');
    if (!content) return;
    content.innerHTML = '<p>Loading reminder messages...</p>';
    const url = dateFilter ? `/messages/reminder-messages?date=${dateFilter}` : '/messages/reminder-messages';
    const result = await makeApiCall(url);
    if (result.success) {
        const data = result.data;
        const html = withCancelMarkup('', data.messages);
        content.innerHTML = `<div class="master-message-container"><h3>🔄 Reminder Messages ${data.date_filter ? `(${data.date_filter})` : '(All Time)'}</h3><p><strong>Total Reminder Messages:</strong> ${data.total_messages}</p>${html}</div>`;
        attachMasterCancelHandlers();
    } else {
        content.innerHTML = `<p>Error loading reminder messages: ${result.error.detail}</p>`;
    }
}

// VIN history: add cancel for pending reminders
function attachVinHistoryCancelHandlers() {
    const container = document.getElementById('message-history-content');
    if (!container) return;
    if (container.dataset.cancelHandlerAttached === 'true') return; // attach once
    container.addEventListener('click', async (e) => {
        const btn = e.target.closest('.cancel-msg-btn');
        if (!btn) return;
        const id = btn.getAttribute('data-message-id');
        if (!confirm('Cancel this scheduled message?')) return;
        const res = await makeApiCall(`/messages/message/${id}/cancel`, 'POST');
        if (res.success) {
            const status = btn.closest('.message-history-item').querySelector('.message-status');
            status.textContent = 'CANCELED';
            status.className = 'message-status canceled';
            btn.remove();
        } else {
            alert(`Failed to cancel: ${res.error?.detail || 'Unknown error'}`);
        }
    });
    container.dataset.cancelHandlerAttached = 'true';
}

function decorateHistoryWithCancel(html, list) {
    return list.map(msg => `
        <div class="message-history-item ${msg.status === 'sent' ? 'sent' : msg.status === 'failed' ? 'failed' : msg.status === 'canceled' ? 'canceled' : 'pending'}">
            <div class="message-header">
                <strong>${msg.contact_name}</strong> (${msg.contact_phone})
                <span class="message-status ${msg.status}">${msg.status.toUpperCase()}</span>
                ${msg.status === 'pending' ? `<button class="cancel-msg-btn" data-message-id="${msg.id}" style="background:#dc3545;margin-left:8px;">Cancel</button>` : ''}
            </div>
            <div class="message-content">
                <p>${msg.is_reminder ? '🔄 Reminder' : '📱 Pickup'}: ${msg.message_content}</p>
            </div>
            <div class="message-details">
                <small>
                    <strong>Scheduled:</strong> ${new Date(msg.scheduled_time).toLocaleString()}
                    ${msg.sent_at ? `<br><strong>Sent:</strong> ${new Date(msg.sent_at).toLocaleString()}` : ''}
                </small>
            </div>
        </div>`).join('');
}

// Wrap history loaders to include cancel buttons
const _origLoadHistory = loadMessageHistory;
loadMessageHistory = async function(vinId){
    const historyContent = document.getElementById('message-history-content');
    if (!historyContent) return;
    historyContent.innerHTML = '<p>Loading message history...</p>';
    const result = await makeApiCall(`/messages/vin/${vinId}/history`);
    if (result.success) {
        const history = result.data;
        const html = decorateHistoryWithCancel('', history.message_history);
        historyContent.innerHTML = `<div class="message-history-container"><h5>${history.vehicle_info} (${history.vin_string})</h5>${html}</div>`;
        attachVinHistoryCancelHandlers();
    } else {
        historyContent.innerHTML = `<p>Error loading message history: ${result.error.detail}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const vinLookupDiv = document.getElementById("vin-lookup");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const createVinForm = document.getElementById("create-vin-form");
    const decodeVinBtn = document.getElementById("decode-vin-btn");
    const createServiceRecordForm = document.getElementById("create-service-record-form");
    const pickupMessageSection = document.getElementById("pickup-message-section");

    // Get current path for redirects
    const currentPath = window.location.pathname;

    // --- Page Load Logic ---
    const urlParams = new URLSearchParams(window.location.search);
    const newServiceId = urlParams.get('new_service_id');
    const vinParam = urlParams.get('vin');
    const vinOrLast6Param = urlParams.get('vin_or_last6');

    if (newServiceId) {
        // If a new service ID is present, start the pickup message flow
        handlePickupFlow(newServiceId);
    } else if (vinParam || vinOrLast6Param) {
        // If a VIN is present in the URL, set it in the search box and load the profile
        const vinOrLast6Input = document.getElementById("vin_or_last6");
        if (vinOrLast6Input) {
            vinOrLast6Input.value = vinParam || vinOrLast6Param;
        }
        const getVinProfileForm = document.getElementById("get-vin-profile-form");
        if (getVinProfileForm) {
            getVinProfileForm.dispatchEvent(new Event("submit"));
        }
    } else {
        // Otherwise, show the default VIN lookup form
        vinLookupDiv.style.display = 'block';
    }

    // --- Top-Level Event Listeners (Stable Elements) ---

    const getVinProfileForm = document.getElementById("get-vin-profile-form");

    getVinProfileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const vinOrLast6 = document.getElementById("vin_or_last6").value;
        vinProfileDiv.innerHTML = ""; // Clear previous profile
        vinCreationDiv.style.display = "none";
        serviceRecordCreationDiv.style.display = "none";

        try {
            const response = await fetch(`/vin/${vinOrLast6}`);
            if (response.ok) {
                const data = await response.json();
                displayVinProfile(data); // Renders HTML and calls setupVinProfileContactEvents
                serviceRecordCreationDiv.style.display = "block";
                document.getElementById("service-vin").value = data.vin;
            } else {
                vinProfileDiv.innerHTML = "<p>VIN not found. Please create a new profile.</p>";
                vinCreationDiv.style.display = "block";
                document.getElementById("vin").value = vinOrLast6; // Populate VIN field
            }
        } catch (error) {
            console.error("Error:", error);
            vinProfileDiv.innerHTML = "<p>An error occurred while fetching the VIN profile.</p>";
        }
    });

    // After listener is attached, auto-load VIN if present in URL
    const qp = new URLSearchParams(window.location.search);
    const vinFromUrl = qp.get('vin') || qp.get('vin_or_last6');
    if (vinFromUrl) {
        const vinInput = document.getElementById('vin_or_last6');
        if (vinInput) vinInput.value = vinFromUrl;
        getVinProfileForm.dispatchEvent(new Event('submit'));
    }

    decodeVinBtn.addEventListener("click", async () => {
        const vin = document.getElementById("vin").value;
        if (vin.length !== 17) {
            alert("Please enter a 17-character VIN.");
            return;
        }

        try {
            const response = await fetch(`/vin/decode_vin/${vin}`);
            if (response.ok) {
                const data = await response.json();
                document.getElementById("make").value = data.make || "";
                document.getElementById("model").value = data.model || "";
                document.getElementById("year").value = data.year || "";
                document.getElementById("trim").value = data.trim || "";
            } else {
                alert("Failed to decode VIN.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while decoding the VIN.");
        }
    });

    createVinForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(createVinForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/vin/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                alert("VIN created successfully!");
                createVinForm.reset();
                vinCreationDiv.style.display = "none";
                const vin = data.vin;
                document.getElementById("vin_or_last6").value = vin;
                getVinProfileForm.dispatchEvent(new Event("submit"));
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while creating the VIN.");
        }
    });

    createServiceRecordForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(createServiceRecordForm);
        const data = Object.fromEntries(formData.entries());

        // Convert mileage fields to numbers
        data.mileage_at_service = parseInt(data.mileage_at_service, 10);
        data.next_service_mileage_due = parseInt(data.next_service_mileage_due, 10);

        try {
            const response = await fetch("/service-record/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                const result = await response.json();
                alert("Service record created successfully!");
                createServiceRecordForm.reset();
                // Redirect with the new service record ID
                window.location.href = currentPath + '?new_service_id=' + result.id;
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while creating the service record.");
        }
    });

    // --- Display Function ---

    function displayVinProfile(data) {
        // Find the most recent service record
        let mostRecentService = null;
        if (data && data.service_records && Array.isArray(data.service_records) && data.service_records.length > 0) {
            mostRecentService = data.service_records.reduce((latest, current) => {
                const latestDate = new Date(latest.service_date);
                const currentDate = new Date(current.service_date);
                return currentDate > latestDate ? current : latest;
            });
        }

        const serviceRecordsHtml = (data && data.service_records && Array.isArray(data.service_records) && data.service_records.length > 0)
            ? `<div class="service-records-container">
                    ${data.service_records.map(record => {
                        const isMostRecent = mostRecentService && record.id === mostRecentService.id;
                        return `
                            <div class="service-record-card" style="position: relative; padding-top: ${isMostRecent ? '40px' : '15px'};">
                                <div style="position: absolute; top: 8px; right: 8px; display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end;">
                                    ${isMostRecent ? '<div style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">⭐ Most Recent</div>' : ''}
                                    <div id="pickup-badge-${record.id}" style="display:none; background-color: #0d6efd; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">📤 Pickup Sent</div>
                                </div>
                            <p><strong>Service Date:</strong> <span>${record.service_date}</span></p>
                            <p><strong>Mileage:</strong> <span>${record.mileage_at_service}</span></p>
                            <p><strong>Oil Type:</strong> <span>${record.oil_type}</span></p>
                            <p><strong>Oil Viscosity:</strong> <span>${record.oil_viscosity}</span></p>
                            <p><strong>Next Due (Miles):</strong> <span>${record.next_service_mileage_due}</span></p>
                            <p><strong>Next Due (Date):</strong> <span>${record.next_service_date_due}</span></p>
                            <p><strong>Notes:</strong> <span>${record.notes || 'N/A'}</span></p>
                            <button onclick="handlePickupFlow(${record.id})" style="background-color: #28a745; margin-top: 10px;">📱 Send Pickup Message</button>
                        </div>
                        `;
                    }).join("")}
                </div>`
            : "<p>No service records found.</p>";

        const associatedContactsHtml = (data && data.contacts && Array.isArray(data.contacts) && data.contacts.length > 0)
            ? `<div class="contacts-container">
                    ${data.contacts.map(contact => `
                        <div class="contact-card">
                            <p><strong>Name:</strong> <span>${contact.name}</span></p>
                            <p><strong>Phone:</strong> <span>${contact.phone_number}</span></p>
                            ${contact.email ? `<p><strong>Email:</strong> <span>${contact.email}</span></p>` : ''}
                        </div>
                    `).join("")}
                </div>`
            : "<p>No contacts associated yet.</p>";

        vinProfileDiv.innerHTML = `
            <h3>VIN: ${data.vin}</h3>
            <div class="vin-details-container">
                <p><strong>Make:</strong> <span>${data.make}</span></p>
                <p><strong>Model:</strong> <span>${data.model}</span></p>
                <p><strong>Year:</strong> <span>${data.year}</span></p>
                <p><strong>Trim:</strong> <span>${data.trim || "N/A"}</span></p>
                <p><strong>Plate:</strong> <span>${data.plate || "N/A"}</span></p>
            </div>
            <h4>Service Records:</h4>
            ${serviceRecordsHtml}

            <h4>Associated Contacts:</h4>
            <div id="associated-contacts">${associatedContactsHtml}</div>

            <h4>Message History:</h4>
            <div id="message-history">
                <!-- Message History Tabs -->
                <div style="margin: 10px 0; border-bottom: 2px solid #dee2e6;">
                    <button id="vin-tab-pickup" onclick="switchVinMessageTab('pickup', ${data.id})" style="background-color: #6c757d; color: white; border: none; padding: 8px 16px; margin-right: 5px; border-radius: 5px 5px 0 0;">📱 Pickup Messages</button>
                    <button id="vin-tab-reminder" onclick="switchVinMessageTab('reminder', ${data.id})" style="background-color: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 5px 5px 0 0;">🔄 Reminder Messages</button>
                    <button id="vin-tab-sent-reminders" onclick="switchVinMessageTab('sent', ${data.id})" style="background-color: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 5px 5px 0 0;">✅ Sent Reminders</button>
                </div>
                <div id="message-history-content"></div>
            </div>

            <h4>Manage Contacts:</h4>
            <div id="contact-management">
                <h5>Create New Contact</h5>
                <form id="create-contact-form">
                    <input type="text" id="new_contact_name" name="name" placeholder="Name" required>
                    <input type="text" id="new_contact_phone" name="phone_number" placeholder="Phone Number" required>
                    <input type="email" id="new_contact_email" name="email" placeholder="Email (Optional)">
                    <button type="submit">Create Contact</button>
                </form>

                <h5>Link Existing Contact</h5>
                <form id="link-contact-form">
                    <input type="text" id="search_contact_phone" placeholder="Search by Phone Number">
                    <div id="search_results_list"></div>
                    <input type="hidden" id="selected_contact_id">
                    <button type="submit" id="link_contact_button" disabled>Link Selected Contact</button>
                </form>
            </div>
        `;

        // Now that the HTML is rendered, set up delegated event listeners
        setupVinProfileContactEvents(data.id, data.vin); // Pass VIN ID and VIN string
        
        // Populate pickup-sent badges per service record
        if (data && data.service_records) {
            data.service_records.forEach(sr => updatePickupSentBadge(sr.id));
        }

        // Load the default message history
        switchVinMessageTab('pickup', data.id);
    }

    // --- Delegated Event Handling ---

    function setupVinProfileContactEvents(currentVinId, currentVinString) {
        let searchTimeout;

        // Event listener for forms within vinProfileDiv (submit event)
        vinProfileDiv.addEventListener("submit", async (e) => {
            e.preventDefault();
            const form = e.target;

            if (form.id === "create-contact-form") {
                const formData = new FormData(form);
                const contactData = Object.fromEntries(formData.entries());

                const result = await makeApiCall("/contacts/", 'POST', contactData);

                if (result.success) {
                    alert(`Contact ${result.data.name} created successfully! Now linking to VIN.`);
                    const linkResult = await linkContactToVin(result.data.id, currentVinId);
                    if (linkResult.success) {
                        alert("Contact linked successfully!");
                    }
                    form.reset();
                    // Re-fetch VIN profile to update contacts display
                    document.getElementById("vin_or_last6").value = currentVinString; // Use the current VIN string
                    getVinProfileForm.dispatchEvent(new Event("submit"));
                } else {
                    alert(`Error creating contact: ${result.error.detail}`);
                }
            } else if (form.id === "link-contact-form") {
                const selectedContactIdInput = document.getElementById("selected_contact_id");
                const contactIdToLink = selectedContactIdInput.value;
                if (!contactIdToLink) {
                    alert("Please select a contact to link from the search results.");
                    return;
                }
                const result = await linkContactToVin(contactIdToLink, currentVinId);
                if (result.success) {
                    alert("Contact linked successfully!");
                } else if (result.error && result.error.detail === "Contact already linked to this VIN") {
                    alert("This contact is already linked to the current VIN.");
                } else {
                    alert(`Error linking contact: ${result.error.detail}`);
                }
                // Re-fetch VIN profile to update contacts display
                document.getElementById("vin_or_last6").value = currentVinString; // Use the current VIN string
                getVinProfileForm.dispatchEvent(new Event("submit"));
            }
        });

        // Event listener for input changes within vinProfileDiv (input event)
        vinProfileDiv.addEventListener("input", async (e) => {
            if (e.target.id === "search_contact_phone") {
                const searchContactPhoneInput = e.target;
                const searchResultsList = document.getElementById("search_results_list");
                const selectedContactIdInput = document.getElementById("selected_contact_id");
                const linkContactButton = document.getElementById("link_contact_button");

                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(async () => {
                    const phoneNumber = searchContactPhoneInput.value.trim();
                    if (phoneNumber.length >= 3) {
                        const foundContacts = await searchContacts(phoneNumber);
                        searchResultsList.innerHTML = ""; // Clear previous results
                        if (foundContacts.length === 0) {
                            searchResultsList.innerHTML = "<p>No contacts found.</p>";
                            selectedContactIdInput.value = "";
                            linkContactButton.disabled = true;
                            return;
                        }

                        foundContacts.forEach(contact => {
                            const resultItem = document.createElement("div");
                            resultItem.classList.add("search-result-item");
                            resultItem.innerHTML = `<strong>${contact.name}</strong> (${contact.phone_number})`;
                            resultItem.dataset.contactId = contact.id;
                            resultItem.addEventListener("click", () => { // Direct listener for search result item
                                selectedContactIdInput.value = contact.id;
                                searchContactPhoneInput.value = `${contact.name} (${contact.phone_number})`; // Display selected contact
                                searchResultsList.innerHTML = ""; // Clear results after selection
                                linkContactButton.disabled = false; // Enable link button
                            });
                            searchResultsList.appendChild(resultItem);
                        });
                    } else {
                        searchResultsList.innerHTML = "";
                        selectedContactIdInput.value = "";
                        linkContactButton.disabled = true;
                    }
                }, 300);
            }
        });

        // Event listener for clicks within vinProfileDiv (click event) - for search results selection
        vinProfileDiv.addEventListener("click", (e) => {
            const resultItem = e.target.closest(".search-result-item");
            if (resultItem) {
                const selectedContactIdInput = document.getElementById("selected_contact_id");
                const searchContactPhoneInput = document.getElementById("search_contact_phone");
                const searchResultsList = document.getElementById("search_results_list");
                const linkContactButton = document.getElementById("link_contact_button");

                const contactId = resultItem.dataset.contactId;
                const contactNamePhone = resultItem.textContent;

                selectedContactIdInput.value = contactId;
                searchContactPhoneInput.value = contactNamePhone; // Display selected contact
                searchResultsList.innerHTML = ""; // Clear results after selection
                linkContactButton.disabled = false; // Enable link button
            }
        });
    }
}); 