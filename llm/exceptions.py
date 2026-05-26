class ModelException(Exception):
    pass


class ModelTimeoutError(ModelException):
    pass


class ModelRateLimitError(ModelException):
    pass


class ModelAuthenticationError(ModelException):
    pass


class ModelConnectionError(ModelException):
    pass
