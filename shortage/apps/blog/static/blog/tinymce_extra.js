// See: https://www.tiny.cloud/docs/configure/file-image-upload/#exampleusingimages_upload_handler
// Note: latest tinymce version (6.0+) has another signature for images_upload_handler
window.tinymceImageUploadHandler = (blobInfo, success, failure, progress) => {
    var xhr, formData;

    xhr = new XMLHttpRequest();
    xhr.withCredentials = false;

    // parse images_upload_url from config
    const mceConfig = JSON.parse(document.querySelector('textarea.tinymce').dataset.mceConf)
    xhr.open("POST", mceConfig.images_upload_url);

    // !!! set CSRF token header. This is why we have this file
    const csrftoken = getCookie("csrftoken");
    xhr.setRequestHeader("X-CSRFTOKEN", csrftoken);

    xhr.upload.onprogress = function (e) {
        progress((e.loaded / e.total) * 100);
    };

    xhr.onload = function () {
        var json;

        if (xhr.status === 403) {
            failure("HTTP Error: " + xhr.status, { remove: true });
            return;
        }

        if (xhr.status < 200 || xhr.status >= 300) {
            failure("HTTP Error: " + xhr.status);
            return;
        }

        json = JSON.parse(xhr.responseText);

        if (!json || typeof json.location != "string") {
            failure("Invalid JSON: " + xhr.responseText);
            return;
        }

        success(json.location);
    };

    xhr.onerror = function () {
        failure(
            "Image upload failed due to a XHR Transport error. Code: " +
                xhr.status
        );
    };

    formData = new FormData();
    formData.append("file", blobInfo.blob(), blobInfo.filename());

    xhr.send(formData);
};

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(";");
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == " ") {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
