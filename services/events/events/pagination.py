from rest_framework.pagination import LimitOffsetPagination


class EventLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200
