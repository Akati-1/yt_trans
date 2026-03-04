document.addEventListener("DOMContentLoaded", function () {
    new TomSelect("#targetLang", {
        create: false,
        sortField: { field: "text", direction: "asc" }
    });
});

async function processURL() {

    const url = document.getElementById("urlInput").value;
    const targetLang = document.getElementById("targetLang").value;

    const formData = new FormData();
    formData.append("url", url);
    formData.append("target_lang", targetLang);

    const response = await fetch("/process", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    document.getElementById("detectedLang").innerText =
        data.detected_language;

    document.getElementById("originalText").value =
        data.original_text;

    document.getElementById("translatedText").value =
        data.translated_text;
}
