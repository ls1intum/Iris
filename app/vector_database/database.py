import os
import logging
from asyncio.log import logger

import weaviate
from .lecture_schema import init_lecture_schema
from .repository_schema import init_repository_schema
from weaviate.classes.query import Filter

import yaml
logger = logging.getLogger(__name__)

def load_config(file_path):
    """
    Load the configuration file
    """
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


weaviate_config = load_config(os.environ.get("APPLICATION_YML_PATH"))
env_vars = weaviate_config.get("env_vars", {})
host = env_vars.get("WEAVIATE_HOST")
port: int = env_vars.get("WEAVIATE_PORT")
grpc_port: int = env_vars.get("WEAVIATE_GRPC_PORT")


class VectorDatabase:
    """
    Class to interact with the Weaviate vector database
    """

    def __init__(self):
        self.client = weaviate.connect_to_local(
            host=host, port=port, grpc_port=grpc_port
        )
        self.repositories = init_repository_schema(self.client)
        self.lectures = init_lecture_schema(self.client)

    def __del__(self):
        self.client.close()

    def delete_collection(self, collection_name):
        """
        Delete a collection from the database
        """
        if self.client.collections.exists(collection_name):
            if self.client.collections.delete(collection_name):
                logger.info(f"Collection {collection_name} deleted")
            else:
                logger.error(f"Collection {collection_name} failed to delete")

    def delete_object(self, collection_name, property_name, object_property):
        """
        Delete an object from the collection inside the databse
        """
        collection = self.client.collections.get(collection_name)
        collection.data.delete_many(
            where=Filter.by_property(property_name).equal(object_property)
        )

    def get_client(self):
        """
        Get the Weaviate client
        """
        return self.client
