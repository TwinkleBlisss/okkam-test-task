import logging
from typing import Annotated

from fastapi import FastAPI, Query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

app = FastAPI()


AudienceParam = Annotated[
    str,
    Query(
        min_length=3,
        max_length=500,
        examples=[
            "Age BETWEEN 18 AND 35",
            "Sex = 2 AND Age >= 18",
        ],
    ),
]


@app.get("/getPercent")
def get_percent(
    audience1: AudienceParam,
    audience2: AudienceParam,
):
    logger.info(f"{audience1=}; {audience2=}")

    # TODO: проверять sql фильтры аудиторий

    return {"percent": "55%"}
