'''
Unified error format for all API endpoints

Response format:
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human-readable description",
        "fields": { "field_name": ["error text"] } | null
    }
}
'''
from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


_STATUS_TO_CODE: dict[int, str] = {
    400: 'VALIDATION_ERROR',
    401: 'UNAUTHORIZED',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    405: 'METHOD_NOT_ALLOWED',
    409: 'CONFLICT',
    422: 'UNPROCESSABLE_ENTITY',
    429: 'THROTTLED',
    500: 'INTERNAL_SERVER_ERROR',
}


def custom_exception_handler(exc: Exception, context: Any) -> Response | None:
    response = exception_handler(exc, context)

    if response is None:
        return None

    data = response.data

    fields: dict[str, Any] | None = None
    message: str = 'An error occured.'

    if isinstance(data, dict):
        # ValidationError: {"field": ["error"], "non_field_errors": ["..."]}
        if any(isinstance(v, list) for v in data.values()):
            fields = {
                k: v if isinstance(v, list) else [v]
                for k, v in data.items()
                if k != 'detail'
            }

            # non_field_errors -> removed in message, not in fields
            if 'non_field_errors' in fields:
                non_field = fields.pop('non_field_errors')
                message = non_field[0] if non_field else message

            elif 'detail' in data:
                message = str(data['detail'])

        elif 'detail' in data:
            message = str(data['detail'])

    elif isinstance(data, str):
        message = data

    response.data = {
        'error': {
            'code': _STATUS_TO_CODE.get(response.status_code, 'ERROR'),
            'message': message,
            'fields': fields if fields else None,
        }
    }

    return response
