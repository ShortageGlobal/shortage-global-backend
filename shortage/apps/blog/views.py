from rest_framework import viewsets, permissions, exceptions
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.response import Response
from shortage.apps.storage import MediaStorage
from shortage.apps.blog.models import BlogPost
from shortage.apps.blog.serializers import PrivateBlogPostSerializer
from shortage.apps.file_paths import get_blog_image_path


@api_view(["POST"])
@schema(AutoSchema("Private", "Blog"))
@permission_classes((permissions.IsAuthenticated,))
def upload_image(request):
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
        get_blog_image_path(request.user.id, file_obj.name), file_obj
    )

    # return absolute link to the uploaded image
    return Response(
        {
            "message": "Image uploaded successfully",
            "location": storage.url(file_path),
        }
    )


class BlogPostViewSet(viewsets.ModelViewSet):
    schema = AutoSchema(
        tags=["Private", "Blog"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateBlogPostSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        is_published = self.request.query_params.get("is_published")

        if is_published:
            is_published = is_published.lower()

            if is_published != "true" and is_published != "false":
                raise ValueError("is_published should be either true or false")

            queryset = queryset.filter(is_published=is_published)

        return queryset

    def perform_destroy(self, instance):
        # TODO: Delete all related images
        super().perform_destroy(instance)
