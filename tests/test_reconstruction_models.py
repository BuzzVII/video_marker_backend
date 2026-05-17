from collections.abc import Generator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app


@contextmanager
def make_test_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_reconstruction_model_round_trips_wall_fields() -> None:
    with make_test_client() as client:
        project_response = client.post("/api/projects", json={"name": "House scan"})
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        model_id = "model-roundtrip"
        model_data = {
            "cuboidsById": {},
            "pointVertexConstraintsById": {},
            "imageLineEdgeConstraintsById": {},
            "edgeLengthConstraintsById": {},
            "faceAssociationsById": {
                "face-association-1": {
                    "id": "face-association-1",
                    "kind": "same_wall",
                    "faces": [
                        {"cuboidId": "cuboid-a", "faceId": "right"},
                        {"cuboidId": "cuboid-b", "faceId": "left"},
                    ],
                    "source": "manual",
                    "confidence": 1.0,
                    "createdAt": "2026-04-30T00:00:00Z",
                    "futureField": {"preserve": True},
                }
            },
            "wallFeaturesById": {
                "wall-feature-1": {
                    "id": "wall-feature-1",
                    "kind": "door",
                    "hostFace": {"cuboidId": "cuboid-a", "faceId": "right"},
                    "connectsTo": {"cuboidId": "cuboid-b", "faceId": "left"},
                    "dimensions": {
                        "width": 0.82,
                        "height": 2.04,
                        "depth": 0.12,
                        "unit": "m",
                    },
                    "localRect": {"u0": 0.2, "v0": 0.0, "u1": 0.6, "v1": 0.85},
                    "observationsByFrameId": {},
                    "source": "manual",
                    "createdAt": "2026-04-30T00:00:00Z",
                }
            },
            "activeCuboidId": None,
            "activeVertex": None,
            "activeEdge": None,
            "activeFaces": [{"cuboidId": "cuboid-a", "faceId": "right"}],
            "unknownTopLevelKey": {"also": "preserved"},
        }

        put_response = client.put(
            f"/api/projects/{project_id}/models/{model_id}",
            json={"source": "manual", "data_json": model_data},
        )
        assert put_response.status_code == 200
        assert put_response.json()["data_json"]["faceAssociationsById"] == model_data[
            "faceAssociationsById"
        ]
        assert put_response.json()["data_json"]["wallFeaturesById"] == model_data[
            "wallFeaturesById"
        ]

        latest_response = client.get(f"/api/projects/{project_id}/models/latest")
        assert latest_response.status_code == 200
        latest_data = latest_response.json()["data_json"]
        assert latest_data["faceAssociationsById"] == model_data["faceAssociationsById"]
        assert latest_data["wallFeaturesById"] == model_data["wallFeaturesById"]
        assert latest_data["activeFaces"] == model_data["activeFaces"]
        assert latest_data["unknownTopLevelKey"] == model_data["unknownTopLevelKey"]

        by_id_response = client.get(f"/api/projects/{project_id}/models/{model_id}")
        assert by_id_response.status_code == 200
        by_id_data = by_id_response.json()["data_json"]
        assert by_id_data["faceAssociationsById"] == model_data["faceAssociationsById"]
        assert by_id_data["wallFeaturesById"] == model_data["wallFeaturesById"]


def test_reconstruction_model_defaults_new_fields_for_old_payloads() -> None:
    with make_test_client() as client:
        project_id = client.post("/api/projects", json={"name": "Old model"}).json()["id"]
        response = client.post(
            f"/api/projects/{project_id}/models",
            json={"data_json": {"cuboidsById": {}}},
        )
        assert response.status_code == 201
        data = response.json()["data_json"]
        assert data["faceAssociationsById"] == {}
        assert data["wallFeaturesById"] == {}
        assert data["activeFaces"] == []
        assert data["imageLineEdgeConstraintsById"] == {}
