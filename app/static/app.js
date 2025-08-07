document.addEventListener("DOMContentLoaded", () => {
    const getVinProfileForm = document.getElementById("get-vin-profile-form");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const createVinForm = document.getElementById("create-vin-form");
    const decodeVinBtn = document.getElementById("decode-vin-btn");
    const createServiceRecordForm = document.getElementById("create-service-record-form");

    // --- Top-Level Event Listeners (Stable Elements) ---

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
                displayVinProfile(data); // Renders HTML and calls setupDelegatedContactEvents
                serviceRecordCreationDiv.style.display = "block";
                document.getElementById("service-vin").value = data.vin;
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                document.getElementById('service_date').valueAsDate = today;
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
                window.location.href = window.location.pathname + '?new_service_id=' + result.id;
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while creating the service record.");
        }
    });

    // --- Helper Functions (Globally Accessible within DOMContentLoaded) ---

    async function linkContactToVin(contactId, vinId) {
        const result = await makeApiCall(`/contacts/${contactId}/link_to_vin/${vinId}`, 'POST');
        return result;
    }

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

    // --- New makeApiCall Helper Function ---
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
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                // If response is not JSON, get it as text
                data = await response.text();
            }

            if (response.ok) {
                return { success: true, data: data };
            } else {
                // Backend errors typically have a 'detail' field
                const errorMessage = data.detail || data || `HTTP Error: ${response.status}`;
                return { success: false, error: { status: response.status, detail: errorMessage } };
            }
        } catch (networkError) {
            console.error("Network or unexpected error:", networkError);
            return { success: false, error: { status: 0, detail: "Network error or unexpected issue." } };
        }
    }

    // --- Display Function ---

    function displayVinProfile(data) {
        const serviceRecordsHtml = (data && data.service_records && Array.isArray(data.service_records) && data.service_records.length > 0)
            ? `<div class="service-records-container">
                    ${data.service_records.map(record => `
                        <div class="service-record-card">
                            <p><strong>Service Date:</strong> <span>${record.service_date}</span></p>
                            <p><strong>Mileage:</strong> <span>${record.mileage_at_service}</span></p>
                            <p><strong>Oil Type:</strong> <span>${record.oil_type}</span></p>
                            <p><strong>Oil Viscosity:</strong> <span>${record.oil_viscosity}</span></p>
                            <p><strong>Next Due (Miles):</strong> <span>${record.next_service_mileage_due}</span></p>
                            <p><strong>Next Due (Date):</strong> <span>${record.next_service_date_due}</span></p>
                            <p><strong>Notes:</strong> <span>${record.notes || 'N/A'}</span></p>
                        </div>
                    `).join("")}
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
        setupDelegatedContactEvents(data.id, data.vin); // Pass VIN ID and VIN string
    }

    // --- Delegated Event Handling ---

    function setupDelegatedContactEvents(currentVinId, currentVinString) {
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
                    } else {
                        alert(`Error linking contact: ${linkResult.error.detail}`);
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
                        const contacts = await searchContacts(phoneNumber);
                        searchResultsList.innerHTML = ""; // Clear previous results
                        if (contacts.length === 0) {
                            searchResultsList.innerHTML = "<p>No contacts found.</p>";
                            selectedContactIdInput.value = "";
                            linkContactButton.disabled = true;
                            return;
                        }

                        contacts.forEach(contact => {
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