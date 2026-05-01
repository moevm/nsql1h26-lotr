"""
Serializers for the comments app.

Only two are needed:
    CommentInputSerializer - validates POST body (text only).
    CommentOutputSerializer - shapes the response (read-only, assembled in services).

The output serializer is used purely for drf-spectacular schema generation via
@extend_schema; the actual data is a plain dict built in services.py.
"""

from rest_framework import serializers

from .services import MAX_COMMENT_LENGTH


class CommentInputSerializer(serializers.Serializer):
    text = serializers.CharField(
        min_length=1,
        max_length=MAX_COMMENT_LENGTH,
        trim_whitespace=True,
        help_text=f'Comment body. Max {MAX_COMMENT_LENGTH} characters'
    )


class _AuthorSerializer(serializers.Serializer):
    username = serializers.CharField()
    avatar_url = serializers.URLField(allow_null=True)


class CommentOutputSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text=(
            "Neo4j element ID of the comment node (string, e.g. '4:abc:0'). "
            "Use this value in DELETE /pages/{slug}/comments/{id}/."
        )
    )
    text = serializers.CharField()
    author = _AuthorSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
