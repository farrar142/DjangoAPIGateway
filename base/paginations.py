from rest_framework.pagination import CursorPagination as _CursorPagination


class CursorPagination(_CursorPagination):
    ordering = "-created_at"
