import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from shortage.apps.file_paths import get_blog_image_path
from shortage.apps.storage import MediaStorage


@csrf_exempt
def upload_image(request):
    if request.method == "POST":
        file_obj = request.FILES["file"]
        file_name_suffix = file_obj.name.split(".")[-1]

        if file_name_suffix not in [
            "jpg",
            "png",
            "gif",
            "jpeg",
        ]:
            return JsonResponse({"message": "Wrong file format"})

        storage = MediaStorage()

        file_path = storage.save(get_blog_image_path(file_obj.name), file_obj)

        return JsonResponse(
            {
                "message": "Image uploaded successfully",
                "location": storage.url(file_path),
            }
        )

    return JsonResponse({"detail": "Wrong request"})
