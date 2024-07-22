document.getElementById('generate-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var form = event.target;
    var formData = new FormData(form);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', form.action, true);
    xhr.onload = function() {
        var response = JSON.parse(xhr.responseText);
        if (response.success) {
            showSnackbar("PDF wurde erfolgreich erstellt.");
            showStatusMessage("PDF wurde erfolgreich erstellt. <a href='/manage'>Hier klicken, um zu bearbeiten</a>");
        } else {
            showSnackbar("Fehler: " + response.error);
        }
    };
    xhr.send(formData);
    showStatusMessage("Bitte warten Sie, während die PDF erstellt wird...");
});

function showStatusMessage(message) {
    var statusMessage = document.getElementById("status-message");
    statusMessage.innerHTML = message;
}

document.getElementById('customer-name-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var form = event.target;
    var formData = new FormData(form);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/save_customer_name', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        var response = JSON.parse(xhr.responseText);
        if (response.new_filename) {
            document.getElementById('filename').innerText = response.new_filename;
            form.reset();
        } else {
            showSnackbar("Fehler: " + response.error);
        }
    };
    var customerName = formData.get('customer_name');
    var filename = document.getElementById('filename').innerText;
    xhr.send(JSON.stringify({customer_name: customerName, filename: filename}));
});

function showSnackbar(message) {
    var snackbar = document.getElementById("snackbar");
    snackbar.innerText = message;
    snackbar.className = "show";
    setTimeout(function() { snackbar.className = snackbar.className.replace("show", ""); }, 3000);
}

document.addEventListener("DOMContentLoaded", function() {
    const dropzones = document.querySelectorAll(".dropzone");

    dropzones.forEach(dropzone => {
        dropzone.addEventListener("dragover", function(event) {
            event.preventDefault();
            dropzone.classList.add("dragover");
        });

        dropzone.addEventListener("dragleave", function() {
            dropzone.classList.remove("dragover");
        });

        dropzone.addEventListener("drop", function(event) {
            event.preventDefault();
            dropzone.classList.remove("dragover");

            const files = event.dataTransfer.files;
            const section = dropzone.dataset.section;

            uploadFiles(section, files);
        });

        dropzone.addEventListener("click", function() {
            const input = document.createElement("input");
            input.type = "file";
            input.multiple = true;
            input.addEventListener("change", function() {
                const files = input.files;
                const section = dropzone.dataset.section;
                uploadFiles(section, files);
            });
            input.click();
        });
    });

    function uploadFiles(section, files) {
        const formData = new FormData();
        formData.append("section", section);
        for (let i = 0; i < files.length; i++) {
            formData.append("file", files[i]);
        }

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);
        xhr.onload = function() {
            if (xhr.status === 200) {
                showSnackbar("Dateien wurden erfolgreich hochgeladen.");
            } else {
                showSnackbar("Fehler beim Hochladen der Dateien.");
            }
        };
        xhr.send(formData);
    }
});
