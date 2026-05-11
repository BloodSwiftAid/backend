from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler



def error_400(message):
    return Response(
        {
            "code": status.HTTP_400_BAD_REQUEST,
            "status": "error",
            "message": message,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def error_404(message):
    return Response(
        {
            "code": status.HTTP_404_NOT_FOUND,
            "status": "error",
            "message": message,
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def error_401(message):
    return Response(
        {
            "code": status.HTTP_401_UNAUTHORIZED,
            "status": "error",
            "message": message,
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


class CustomValidationError(APIException):
    default_detail = "A validation error occurred."
    default_code = "validation_error"

    def __init__(self, message, status_code):
        self.detail = {
            "code": status_code,
            "status": False,
            "message": "Validation error",
            "data": {},
            "error": message,
        }

        self.status_code = status_code


def serializer_error_400(
    message=None, error_key=None, status_code=status.HTTP_400_BAD_REQUEST
):
    if message is None:
        message = "Validation error"
    if error_key is None:
        error_key = "error"
    raise CustomValidationError(message, status_code)
    # raise serializers.ValidationError({error_key: message})


# def serializer_error_400(message):
#     return serializers.ValidationError(
#         {"code": 400, "status": "error", "message": message}
#     )


    return error_messages


def custom_exception_handler(exc, context):
    """
    Unified error handler that returns errors in a consistent format:
    {
        "status_code": <int>,
        "message": <string>
    }
    """
    # Call DRF's default exception handler first to get the standard error response
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        message = ""

        if isinstance(data, dict):
            # Collect all error messages from all fields
            all_messages = []
            for field, errors in data.items():
                field_name = field.replace('_', ' ').capitalize()
                if isinstance(errors, list):
                    for e in errors:
                        msg = str(e).strip().rstrip('.')
                        all_messages.append(f"{field_name}: {msg}")
                else:
                    msg = str(errors).strip().rstrip('.')
                    all_messages.append(f"{field_name}: {msg}")
            
            # Join all unique messages with a comma and space
            unique_messages = []
            for msg in all_messages:
                if msg not in unique_messages:
                    unique_messages.append(msg)
            
            message = ", ".join(unique_messages)
            if message:
                message += "."
        elif isinstance(data, list):
            message = ". ".join([str(e).strip().rstrip('.') for e in data])
            if message:
                message += "."
        else:
            message = str(data).strip()

        # Final cleanup for common DRF prefixes
        prefixes_to_remove = ["Detail: ", "detail: ", "Error: ", "error: "]
        for prefix in prefixes_to_remove:
            if message.startswith(prefix):
                message = message.replace(prefix, "", 1)
                break

        response.data = {
            "status_code": response.status_code,
            "message": message or "An error occurred."
        }
    else:
        # Handle non-DRF exceptions (500 errors)
        response = Response({
            "status_code": 500,
            "message": "An internal server error occurred. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response



# def serializer_errors(default_errors):
#     print("errors:",default_errors)
#     error_messages = ""
#     for field_name, field_errors in default_errors.items():
#         if isinstance(field_errors, (list, tuple)) and field_errors:
#             first_error = field_errors[0]

#             if hasattr(first_error, "code"):
#                 if first_error.code == "unique":
#                     error_messages += f"{field_name} already exists, "
#                 else:
#                     error_messages += f"{field_name} is {first_error.code}, "
#             else:
#                 # Fallback if it's just a string
#                 error_messages += f"{field_name} error: {str(first_error)}, "
#         else:
#             error_messages += f"{field_name} has an error, "
#     return error_messages.strip(", ")
