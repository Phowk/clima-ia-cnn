const form = document.getElementById("uploadForm");
const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");

imageInput.addEventListener("change", function () {

    const file = this.files[0];

    if (file) {

        previewImage.src = URL.createObjectURL(file);

    }

});

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    if (!imageInput.files.length) {

        alert("Seleccione una imagen");
        return;

    }

    const formData = new FormData();

    formData.append(
        "imagen",
        imageInput.files[0]
    );

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/deshielo/analizar",
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            throw new Error(
                "Error en la API"
            );

        }

        const data = await response.json();

        updateResults(data);

    }
    catch (error) {

        console.error(error);

        alert(
            "Error procesando la imagen"
        );

    }

});

function updateResults(data) {

    // Cobertura de hielo

    document.getElementById(
        "icePercent"
    ).textContent =
        data.cobertura_hielo.toFixed(2) + "%";

    // Estado

    const status =
        document.getElementById(
            "iceStatus"
        );

    status.textContent =
        data.estado;

    status.className =
        "metric-status";

    if (data.estado === "Conservado") {

        status.classList.add(
            "status-good"
        );

    }
    else if (
        data.estado === "Vulnerable"
    ) {

        status.classList.add(
            "status-warning"
        );

    }
    else {

        status.classList.add(
            "status-danger"
        );

    }

    // Imágenes

    document.getElementById(
        "heatmapImage"
    ).src =
        "data:image/png;base64," +
        data.heatmap;

    document.getElementById(
        "maskImage"
    ).src =
        "data:image/png;base64," +
        data.mask;

    document.getElementById(
        "overlayImage"
    ).src =
        "data:image/png;base64," +
        data.overlay;

    // Grid

    renderGrid(
        data.grid
    );

    // Interpretación

    updateReport(
        data
    );

}

function renderGrid(grid) {

    const container =
        document.getElementById(
            "analysisGrid"
        );

    container.innerHTML = "";

    grid.forEach(row => {

        row.forEach(value => {

            const cell =
                document.createElement(
                    "div"
                );

            cell.textContent =
                value.toFixed(1) + "%";

            if (value < 30) {

                cell.style.background =
                    "#22c55e";

            }
            else if (value < 60) {

                cell.style.background =
                    "#f59e0b";

            }
            else {

                cell.style.background =
                    "#dc2626";

            }

            container.appendChild(
                cell
            );

        });

    });

}

function updateReport(data) {

    const report =
        document.getElementById(
            "reportText"
        );

    report.innerHTML = `
        Cobertura de hielo detectada:
        <strong>${data.cobertura_hielo.toFixed(2)}%</strong>.
        <br><br>

        Nivel estimado de deshielo:
        <strong>${data.deshielo.toFixed(2)}%</strong>.
        <br><br>

        Estado general:
        <strong>${data.estado}</strong>.
    `;

}