from typing import cast

import guidance

from app.config import LLMModelConfig, OpenAIConfig, StrategyLLMConfig
from app.models.dtos import Content, ContentType
from app.services.guidance_functions import truncate
from app.llms.strategy_llm import StrategyLLM


class GuidanceWrapper:
    """A wrapper service to all guidance package's methods."""

    def __new__(cls, *_, **__):
        return super(GuidanceWrapper, cls).__new__(cls)

    def __init__(
        self, model: LLMModelConfig, handlebars="", parameters=None
    ) -> None:
        if parameters is None:
            parameters = {}

        self.model = model
        self.handlebars = handlebars
        self.parameters = parameters

    def query(self) -> Content:
        """Get response from a chosen LLM model.

        Returns:
            Text content object with LLM's response.

        Raises:
            Reraises exception from guidance package
            ValueError: if handlebars do not generate 'response'
        """

        template = guidance(self.handlebars)
        result = template(
            llm=self._get_llm(),
            truncate=truncate,
            **self.parameters,
        )

        if isinstance(result._exception, Exception):
            raise result._exception

        if "response" not in result:
            raise ValueError("The handlebars do not generate 'response'")

        return Content(type=ContentType.TEXT, textContent=result["response"])

    def is_up(self) -> bool:
        """Check if the chosen LLM model is up.

        Returns:
            True if the model is up, False otherwise.
        """

        guidance.llms.OpenAI.cache.clear()
        handlebars = """
        {{#user~}}Say 1{{~/user}}
        {{#assistant~}}
            {{gen 'response' temperature=0.0 max_tokens=1}}
        {{~/assistant}}
        """
        content = (
            GuidanceWrapper(model=self.model, handlebars=handlebars)
            .query()
            .text_content
        )
        return content == "1"

    def _get_llm(self):
        if isinstance(self.model, OpenAIConfig):
            return guidance.llms.OpenAI(
                **cast(OpenAIConfig, self.model).llm_credentials
            )
        elif isinstance(self.model, StrategyLLMConfig):
            return StrategyLLM(cast(StrategyLLMConfig, self.model).llms)
        else:
            raise ValueError("Invalid model type: " + str(type(self.model)))
