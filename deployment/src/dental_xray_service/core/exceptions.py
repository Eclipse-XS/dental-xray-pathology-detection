class ServiceError(Exception):
    """Base expected application error."""


class InvalidImageError(ServiceError):
    pass


class ModelNotReadyError(ServiceError):
    pass


class InferenceError(ServiceError):
    pass


class StorageError(ServiceError):
    pass


class PersistenceError(ServiceError):
    pass
