from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .logger import logger


class DatabaseInvalidResponseError(SQLAlchemyError):
    """БД вернула неожиданный ответ"""


def _validation_message(exc: RequestValidationError) -> str:
    """Получение короткого сообщения ошибки валидации."""
    for error in exc.errors():
        original = (error.get('ctx') or {}).get('error')
        if isinstance(original, ValueError):
            return str(original)
    return 'Некорректные параметры запроса'


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SQLAlchemyError)
    def database_error_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        logger.error('Unhandled database error', exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'message': 'An unexpected error has occurred.'},
        )

    @app.exception_handler(RequestValidationError)
    def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        message = _validation_message(exc)
        logger.warning('Validation error: %s', message, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'message': message},
        )
