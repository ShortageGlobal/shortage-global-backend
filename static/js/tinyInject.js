var script = document.createElement('script');
script.type = 'text/javascript';
script.src = "https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js"
document.head.appendChild(script);

script.onload = function(){
	tinymce.init({
		selector: 'textarea',  // change this value according to your HTML

        images_upload_credentials: true,
		images_upload_url: '/api/upload_image/',
		relative_urls: false,
		remove_script_host: false,
		convert_urls: true,
	})
}
