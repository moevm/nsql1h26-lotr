"""
Serializers for the categories app.

Used for request validation and drf-spectacular schema generation.
Actual data is built in services.py and returned as dicts; output serializers
serve purely as schema documentation.
"""

from rest_framework import serializers


class CategoryCreateInputSerializer(serializers.Serializer):
    slug = serializers.CharField(
        required=False,
        help_text=(
            'Optional slug. If not provided, it will be '
            'auto-generated from name.'
        ),
    )
    name = serializers.CharField(
        required=True,
        help_text='Category name.',
    )
    parent_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=(
            'Slug of the parent category. '
            'Omit or set to null for a root category.'
        ),
    )


class CategoryUpdateInputSerializer(serializers.Serializer):
    name = serializers.CharField(
        required=False,
        help_text=(
            'New name for the category. '
            'Omit to keep the current one.'
        ),
    )
    parent_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=(
            'New parent slug. Omit to keep the current parent; '
            'set to null to make it a root category.'
        ),
    )


class ParentInfoSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()


class ChildCategorySerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    page_count = serializers.IntegerField()


class PageSummarySerializer(serializers.Serializer):
    slug = serializers.CharField()
    type = serializers.CharField()
    name = serializers.CharField()
    image_url = serializers.URLField(allow_null=True)


class PaginatedPagesSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = PageSummarySerializer(many=True)


class CategoryDetailOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    parent_slug = serializers.CharField(allow_null=True)
    child_count = serializers.IntegerField()
    page_count = serializers.IntegerField()
    parent = ParentInfoSerializer(allow_null=True)
    children = ChildCategorySerializer(many=True)
    pages = PaginatedPagesSerializer()


class CategoryListItemSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    parent_slug = serializers.CharField(allow_null=True)
    child_count = serializers.IntegerField()
    page_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class PaginatedCategoryListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = CategoryListItemSerializer(many=True)


class CategoryTreeItemSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    page_count = serializers.IntegerField()
    children = serializers.ListField(child=serializers.DictField())


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.DictField(
        child=serializers.CharField(),
        help_text='Error object with code, message, and optional fields.',
    )
