from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DatabaseError

from .logger import logger


class DatabaseInvalidResponseError(DatabaseError):
    pass


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(DatabaseError)
    def database_error_handler(
        request: Request,
        exc: DatabaseError,
    ) -> JSONResponse:
        logger.error(
            'Unhandled database error',
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'message': 'An unexpected error has occurred.'},
        )
