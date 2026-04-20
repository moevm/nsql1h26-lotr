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


def _flatten_errors(data: Any, parent_key: str = '') -> dict[str, list[str]]:
    '''Converts nested DRF errors to a flat list'''
    result: dict[str, list[str]] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ('non_field_errors', 'detail'):
                continue

            new_key = f"{parent_key}.{key}" if parent_key else key

            if isinstance(value, dict):
                if any(isinstance(v, list) for v in value.values()):
                    result.update(_flatten_errors(value, new_key))

            elif isinstance(value, list):
                result[new_key] = value

            elif isinstance(value, str):
                result[new_key] = [value]

    return result


def custom_exception_handler(exc: Exception, context: Any) -> Response | None:
    response = exception_handler(exc, context)

    if response is None:
        return None

    data = response.data

    fields: dict[str, Any] | None = None
    message: str = 'An error occurred.'

    if isinstance(data, dict):
        fields = _flatten_errors(data)

        if 'detail' in data:
            message = str(data['detail'])

        elif 'non_field_errors' in data:
            non_field = data['non_field_errors']
            message = non_field[0] if isinstance(non_field, list) else str(non_field)

        elif not fields:
            # fallback
            message = str(next(
                iter(data.values()),
                'An error occured [fallback].'
            ))
    elif isinstance(data, str):
        message = data

    elif isinstance(data, list):
        message = data[0] if data else 'An error occured.'

    response.data = {
        'error': {
            'code': _STATUS_TO_CODE.get(response.status_code, 'ERROR'),
            'message': message,
            'fields': fields if fields else None,
        }
    }
    return response
