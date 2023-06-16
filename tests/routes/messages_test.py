from freezegun import freeze_time
from app.models.dtos import Content, ContentType
from app.services.guidance_wrapper import GuidanceWrapper


@freeze_time("2023-06-16 03:21:34 +02:00")
def test_send_message(test_client, mocker):
    mocker.patch.object(
        GuidanceWrapper,
        "query",
        return_value=Content(
            type=ContentType.TEXT, textContent="some content"
        ),
        autospec=True,
    )

    body = {
        "template": {
            "templateId": 123,
            "template": "{{#user~}}I want a response to the following query:\
            {{query}}{{~/user}}{{#assistant~}}\
            {{gen 'response' temperature=0.0 max_tokens=500}}{{~/assistant}}",
        },
        "preferredModel": "gpt-3.5-turbo",
        "parameters": {
            "course": "Intro to Java",
            "exercise": "Fun With Sets",
            "query": "Some query",
        },
    }
    response = test_client.post("/api/v1/messages", json=body)
    assert response.status_code == 200
    assert response.json() == {
        "usedModel": "gpt-3.5-turbo",
        "message": {
            "sentAt": "2023-06-16T01:21:34+00:00",
            "content": {"textContent": "some content", "type": "text"},
        },
    }


def test_send_message_missing_params(test_client):
    response = test_client.post("/api/v1/messages", json={})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "template"],
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ["body", "preferredModel"],
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ["body", "parameters"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ]
    }
