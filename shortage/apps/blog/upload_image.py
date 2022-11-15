from django.views.decorators.csrf import csrf_exempt
from rest_framework import exceptions
from shortage.apps.file_paths import get_blog_image_path
from shortage.apps.storage import MediaStorage
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
def upload_image(request):
    file_obj = request.FILES.get("file")

    if not file_obj:
        raise exceptions.ParseError(detail="No file was sent")

    file_extension = file_obj.name.split(".")[-1]

    if file_extension.lower() not in [
        "jpg",
        "png",
        "gif",
        "jpeg",
    ]:
        raise exceptions.ParseError(
            detail='File extension "{extension}" is not supported'.format(
                extension=file_extension
            )
        )

    storage = MediaStorage()

    file_path = storage.save(
        get_blog_image_path(request.user.id, file_obj.name), file_obj
    )

    return Response(
        {
            "message": "Image uploaded successfully",
            "location": storage.url(file_path),
        }
    )
