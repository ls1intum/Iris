import guidance

from app.config import settings
from app.models.dtos import Content, ContentType, LLMModel


class GuidanceWrapper:
    def __init__(
        self, model: LLMModel, handlebars: str, parameters: dict = {}
    ) -> None:
        self.model = model
        self.handlebars = handlebars
        self.parameters = parameters

    def query(self) -> Content:
        template = guidance(self.handlebars)
        result = template(
            llm=self._get_llm(),
            **self.parameters,
        )

        return Content(type=ContentType.TEXT, textContent=result["response"])

    def _get_llm(self):
        return guidance.llms.OpenAI(
            model=self.model.value,
            token=settings.openai_token,
            api_base=settings.openai_api_base,
            api_type=settings.openai_api_type,
            api_version=settings.openai_api_version,
            deployment_id=settings.openai_deployment_id,
        )
