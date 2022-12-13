from rest_framework import permissions, exceptions
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.response import Response
from shortage.apps.storage import MediaStorage
from shortage.apps.file_paths import get_blog_post_content_uploads_path


@api_view(["POST"])
@schema(AutoSchema("Private", "Blog"))
@permission_classes((permissions.IsAuthenticated,))
def upload_image(request):
    """Upload an image file and store it in MediaStorage for use in blog posts"""

    file_obj = request.FILES.get("file")

    # check file was sent
    if not file_obj:
        raise exceptions.ParseError(detail="No file was sent")

    # check file extension
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

    # save file to media storage
    storage = MediaStorage()
    file_path = storage.save(
        get_blog_post_content_uploads_path(request.user.id, file_obj.name), file_obj
    )

    # return absolute link to the uploaded image
    return Response(
        {
            "message": "Image uploaded successfully",
            "location": storage.url(file_path),
        }
    )
