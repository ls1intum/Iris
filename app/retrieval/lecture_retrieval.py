from typing import List

from weaviate import WeaviateClient
from weaviate.classes.query import Filter

from app.domain import IrisMessageRole, PyrisMessage
from app.domain.data.text_message_content_dto import TextMessageContentDTO
from app.llm import BasicRequestHandler, CompletionArguments
from app.pipeline.shared.reranker_pipeline import RerankerPipeline
from app.retrieval.abstract_retrieval import AbstractRetrieval
from app.vector_database.lecture_schema import init_lecture_schema, LectureSchema


def merge_retrieved_chunks(
    basic_retrieved_lecture_chunks, hyde_retrieved_lecture_chunks
) -> List[dict]:
    """
    Merge the retrieved chunks from the basic and hyde retrieval methods. This function ensures that for any
    duplicate IDs, the properties from hyde_retrieved_lecture_chunks will overwrite those from
    basic_retrieved_lecture_chunks.
    """
    merged_chunks = {}
    for chunk in basic_retrieved_lecture_chunks:
        merged_chunks[chunk["id"]] = chunk["properties"]

    for chunk in hyde_retrieved_lecture_chunks:
        merged_chunks[chunk["id"]] = chunk["properties"]

    return [properties for uuid, properties in merged_chunks.items()]


class LectureRetrieval(AbstractRetrieval):
    """
    Class for retrieving lecture data from the database.
    """

    def __init__(self, client: WeaviateClient):
        self.collection = init_lecture_schema(client)
        self.llm = BasicRequestHandler("azure-gpt-35-turbo")
        self.llm_embedding = BasicRequestHandler("embedding-small")
        self.reranker_pipeline = RerankerPipeline()

    def retrieval_pipeline(
        self,
        chat_history: list[PyrisMessage],
        student_query: str,
        result_limit: int,
        course_name: str = None,
        course_id: int = None,
    ) -> List[dict]:
        """
        Retrieve lecture data from the database.
        """
        course_language = (
            self.collection.query.fetch_objects(
                limit=1, return_properties=[LectureSchema.COURSE_LANGUAGE.value]
            )
            .objects[0]
            .properties.get(LectureSchema.COURSE_LANGUAGE.value)
        )
        rewritten_query = self.rewrite_student_query(
            chat_history,
            student_query,
            course_language,
        )

        hypothetical_answer_query = self.rewrite_elaborated_query(
            rewritten_query, course_language, course_name
        )

        response = self.search_in_db(rewritten_query, 0.5, result_limit, course_id)
        response_hyde = self.search_in_db(
            hypothetical_answer_query, 0.5, result_limit, course_id
        )

        basic_retrieved_lecture_chunks: list[dict[str, dict]] = [
            {"id": obj.uuid.int, "properties": obj.properties}
            for obj in response.objects
        ]
        hyde_retrieved_lecture_chunks: list[dict[str, dict]] = [
            {"id": obj.uuid.int, "properties": obj.properties}
            for obj in response_hyde.objects
        ]
        merged_chunks = merge_retrieved_chunks(
            basic_retrieved_lecture_chunks, hyde_retrieved_lecture_chunks
        )

        selected_chunks_index = self.reranker_pipeline(
            paragraphs=merged_chunks, query=student_query, chat_history=chat_history
        )
        return [merged_chunks[int(i)] for i in selected_chunks_index]

    def rewrite_student_query(
        self, chat_history: list[PyrisMessage], student_query: str, course_language: str
    ) -> str:
        """
        Rewrite the student query to generate fitting lecture content and embed it.
        To extract more relevant content from the vector database.
        """
        text_chat_history = [
            chat_history[-i - 1].contents[0].text_content
            for i in range(min(10, len(chat_history)))  # Ensure no out-of-bounds error
        ][
            ::-1
        ]  # Reverse to get the messages in chronological order of their appearance
        num_messages = len(text_chat_history)
        messages_formatted = "\n".join(f" {msg}" for msg in text_chat_history)
        prompt = f"""
                You are serving as an AI assistant on the Artemis Learning Platform at
                 the Technical University of Munich.
                Here are the last {num_messages} student messages in the chat history:
                    {messages_formatted}
                The student has sent the following message:
                    {student_query}.
                If there is a reference to a previous message,
                please rewrite the query by removing any reference to previous messages
                 and replacing them with the details needed.
                Ensure the context and semantic meaning are preserved.
                Translate the rewritten message into {course_language}
                 if it's not already in {course_language}.
                 ANSWER ONLY WITH THE REWRITTEN MESSAGE. DO NOT ADD ANY ADDITIONAL INFORMATION.
                Here is an example how you should rewrite the message:
                    EXAMPLE 1:
                    message 1: Here are the last 1 student messages in the chat history:
                    message 2: Can you explain me the tower of hanoi slides step by step
                    current message: Can you explain me it's code
                Response:
                        Can you explain the code of the tower of hanoi.
                """
        iris_message = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[TextMessageContentDTO(text_content=prompt)],
        )
        response = self.llm.chat(
            [iris_message], CompletionArguments(temperature=0.2, max_tokens=1000)
        )
        return response.contents[0].text_content

    def rewrite_elaborated_query(
        self, student_query: str, course_language: str, course_name: str
    ) -> str:
        """
        Translate the student query to the course language. For better retrieval.
        """
        prompt = f"""You are an AI assistant operating on the Artemis Learning Platform at the Technical University of
             Munich. A student has sent a query regarding the lecture {course_name}. The query is: '{student_query}'.
             Please provide a response in {course_language}. Craft your response to closely reflect the style and
             content of university lecture materials."""

        iris_message = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[TextMessageContentDTO(text_content=prompt)],
        )
        response = self.llm.chat(
            [iris_message], CompletionArguments(temperature=0.2, max_tokens=1000)
        )
        return response.contents[0].text_content

    def search_in_db(
        self, query: str, hybrid_factor: float, result_limit: int, course_id: int = None
    ):
        """
        Search the query in the database and return the results.
        """
        return self.collection.query.hybrid(
            query=query,
            filters=(
                Filter.by_property(LectureSchema.LECTURE_ID.value).equal(course_id)
                if course_id
                else None
            ),
            alpha=hybrid_factor,
            vector=self.llm_embedding.embed(query),
            return_properties=[
                LectureSchema.PAGE_TEXT_CONTENT.value,
                LectureSchema.PAGE_IMAGE_DESCRIPTION.value,
                LectureSchema.COURSE_NAME.value,
                LectureSchema.LECTURE_NAME.value,
                LectureSchema.PAGE_NUMBER.value,
            ],
            limit=result_limit,
        )
