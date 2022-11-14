var script = document.createElement('script');
script.type = 'text/javascript';
script.src = "https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js"
document.head.appendChild(script);

script.onload = function(){
	tinymce.init({
		selector: 'textarea',  // change this value according to your HTML

		// For more info regarding local upload in tinymce https://www.tiny.cloud/docs/demo/local-upload/
		images_upload_url: '/api/upload_image/', // Image upload address in Django route
	})
}
