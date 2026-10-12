import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    if isinstance(exc, DatabaseError):
        logger.exception("Database error in %s", context["view"].__class__.__name__)
        return Response({"detail": "Database is temporarily unavailable."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return exception_handler(exc, context)
