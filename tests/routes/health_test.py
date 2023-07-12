from app.models.dtos import LLMModel


def test_checkhealth(test_client, headers, mocker):
    objA = mocker.Mock()
    objB = mocker.Mock()
    objC = mocker.Mock()

    def side_effect_func(*_, **kwargs):
        if kwargs["model"] == LLMModel.GPT35_TURBO:
            return objA
        elif kwargs["model"] == LLMModel.GPT35_TURBO_16K_0613:
            return objB
        elif kwargs["model"] == LLMModel.GPT35_TURBO_0613:
            return objC

    mocker.patch(
        "app.services.guidance_wrapper.GuidanceWrapper.__new__",
        side_effect=side_effect_func,
    )
    mocker.patch.object(objA, "is_up", return_value=True)
    mocker.patch.object(objB, "is_up", return_value=False)
    mocker.patch.object(objC, "is_up", return_value=True)

    response = test_client.get("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {"model": "GPT35_TURBO", "status": "UP"},
        {"model": "GPT35_TURBO_16K_0613", "status": "DOWN"},
        {"model": "GPT35_TURBO_0613", "status": "UP"},
    ]

    # Assert the second call is cached
    test_client.get("/api/v1/health", headers=headers)
    objA.is_up.assert_called_once()
    objB.is_up.assert_called_once()
    objC.is_up.assert_called_once()


def test_checkhealth_with_wrong_api_key(test_client):
    headers = {"Authorization": "wrong api key"}
    response = test_client.get("/api/v1/health", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == {
        "type": "not_authorized",
        "errorMessage": "Permission denied",
    }


def test_checkhealth_without_authorization_header(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 401
    assert response.json()["detail"] == {
        "type": "not_authenticated",
        "errorMessage": "Requires authentication",
    }
