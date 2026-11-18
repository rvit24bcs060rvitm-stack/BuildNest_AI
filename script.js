document.getElementById("costForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const area = document.getElementById("area").value;
    const floors = document.getElementById("floors").value;
    const quality = document.getElementById("quality").value;

    const errorMessage = document.getElementById("errorMessage");
    errorMessage.textContent = "";

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                area: area,
                floors: floors,
                quality: quality
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong");
        }

        document.getElementById("results").hidden = false;

        document.getElementById("totalCost").textContent =
            "₹" + data.total_cost.toLocaleString("en-IN");

        document.getElementById("totalArea").textContent =
            data.area.toLocaleString("en-IN") + " sq. ft.";

        const details = document.getElementById("materialDetails");
        details.innerHTML = "";

        for (const [material, cost] of Object.entries(data.materials)) {
            const item = document.createElement("p");
            item.textContent = material + ": ₹" +
                cost.toLocaleString("en-IN");
            details.appendChild(item);
        }

        if (window.costChart instanceof Chart) {
            window.costChart.destroy();
        }

        window.costChart = new Chart(
            document.getElementById("costChart"),
            {
                type: "pie",
                data: {
                    labels: Object.keys(data.materials),
                    datasets: [{
                        data: Object.values(data.materials)
                    }]
                },
                options: {
                    responsive: true
                }
            }
        );

    } catch (error) {
        errorMessage.textContent = error.message;
    }
});