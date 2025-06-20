class APIException(Exception):
    status_code = 500
    message = "An internal server error occurred."

    def __init__(self, message=None, status_code=None, payload=None):
        Exception.__init__(self)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class UnauthorizedError(APIException):
    status_code = 401
    message = "Authentication is required."

class ForbiddenError(APIException):
    status_code = 403
    message = "You do not have permission to perform this action."

class NotFoundError(APIException):
    status_code = 404
    message = "The requested resource was not found."