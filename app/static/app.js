document.addEventListener("DOMContentLoaded", () => {
    const getVinProfileForm = document.getElementById("get-vin-profile-form");
    const vinProfileDiv = document.getElementById("vin-profile");
    const vinCreationDiv = document.getElementById("vin-creation");
    const serviceRecordCreationDiv = document.getElementById("service-record-creation");
    const showCreateVinFormBtn = document.getElementById("show-create-vin-form");
    const createVinForm = document.getElementById("create-vin-form");
    const decodeVinBtn = document.getElementById("decode-vin-btn");
    const createServiceRecordForm = document.getElementById("create-service-record-form");

    getVinProfileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const vinOrLast6 = document.getElementById("vin_or_last6").value;
        vinProfileDiv.innerHTML = "";
        vinCreationDiv.style.display = "none";
        serviceRecordCreationDiv.style.display = "none";
        showCreateVinFormBtn.style.display = "none";

        try {
            const response = await fetch(`/vin/${vinOrLast6}`);
            if (response.ok) {
                const data = await response.json();
                displayVinProfile(data);
                serviceRecordCreationDiv.style.display = "block";
                document.getElementById("service-vin").value = data.vin;
                document.getElementById('service_date').valueAsDate = new Date();
            } else {
                vinProfileDiv.innerHTML = "<p>VIN not found. Please create a new profile.</p>";
                vinCreationDiv.style.display = "block";
                showCreateVinFormBtn.style.display = "block";
            }
        } catch (error) {
            console.error("Error:", error);
            vinProfileDiv.innerHTML = "<p>An error occurred while fetching the VIN profile.</p>";
        }
    });

    showCreateVinFormBtn.addEventListener("click", () => {
        vinCreationDiv.style.display = "block";
        showCreateVinFormBtn.style.display = "none";
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
                alert("Service record created successfully!");
                createServiceRecordForm.reset();
                const vin = data.vin;
                document.getElementById("vin_or_last6").value = vin;
                getVinProfileForm.dispatchEvent(new Event("submit"));
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while creating the service record.");
        }
    });

    function displayVinProfile(data) {
        const serviceRecordsHtml = (data && data.service_records && Array.isArray(data.service_records)) 
            ? data.service_records.map(record => `
                <li>
                    <strong>Service Date:</strong> ${record.service_date}<br>
                    <strong>Oil Type:</strong> ${record.oil_type}<br>
                    <strong>Oil Viscosity:</strong> ${record.oil_viscosity}<br>
                    <strong>Mileage:</strong> ${record.mileage_at_service}<br>
                    <strong>Next Service Due:</strong> ${record.next_service_mileage_due} miles / ${record.next_service_date_due}<br>
                    <strong>Notes:</strong> ${record.notes || 'N/A'}
                </li>
            `).join("")
            : "<li>No service records found.</li>";

        vinProfileDiv.innerHTML = `
            <h3>VIN: ${data.vin}</h3>
            <p>Make: ${data.make}</p>
            <p>Model: ${data.model}</p>
            <p>Year: ${data.year}</p>
            <p>Trim: ${data.trim || "N/A"}</p>
            <p>Plate: ${data.plate || "N/A"}</p>
            <h4>Service Records:</h4>
            <ul>
                ${serviceRecordsHtml}
            </ul>
        `;
    }
});