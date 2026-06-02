const form = document.getElementById("uploadForm");
const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');

imageInput.addEventListener('change', function () {

    const file = this.files[0];

    if (file) {

        previewImage.src = URL.createObjectURL(file);

    }

});


form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const fileInput = document.getElementById("imageInput");

    if (!fileInput.files.length) {
        alert("Seleccione una imagen");
        return;
    }

    const formData = new FormData();

    formData.append(
        "imagen",
        fileInput.files[0]
    );

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/deforestacion/analizar",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        updateResults(data);

    } catch (error) {

        console.error(error);

        alert("Error procesando la imagen");

    }

});

function updateResults(data) {

    document.getElementById(
        "deforestationPercentage"
    ).textContent =
        data.porcentaje.toFixed(2) + "%";

    const risk = document.getElementById(
        "riskLevel"
    );

    risk.textContent = data.riesgo;

    risk.className = "metric-risk";

    if (data.riesgo === "Bajo")
        risk.classList.add("risk-low");

    else if (data.riesgo === "Medio")
        risk.classList.add("risk-medium");

    else
        risk.classList.add("risk-high");

    document.getElementById(
        "heatmapImage"
    ).src =
        "data:image/png;base64," + data.heatmap;

    document.getElementById(
        "maskImage"
    ).src =
        "data:image/png;base64," + data.mask;

    document.getElementById(
        "overlayImage"
    ).src =
        "data:image/png;base64," + data.overlay;

    renderGrid(data.grid);
}

function renderGrid(grid) {

    const container =
        document.getElementById("analysisGrid");

    container.innerHTML = "";

    grid.forEach(row => {

        row.forEach(value => {

            const cell =
                document.createElement("div");

            cell.textContent =
                value.toFixed(1) + "%";

            if (value < 20)
                cell.style.background = "#22c55e";

            else if (value < 40)
                cell.style.background = "#f59e0b";

            else
                cell.style.background = "#dc2626";

            container.appendChild(cell);

        });

    });

}