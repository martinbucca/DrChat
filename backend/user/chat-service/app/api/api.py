from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

class API:
    """
    Singleton API class for initializing and configuring a FastAPI application.
    Attributes:
        _instance (API): Singleton instance of the API class.
        _app (FastAPI): The FastAPI application instance.
    Methods:
        __init__():
            Initializes the FastAPI application and adds CORS middleware with default settings.
        get_instance(allowed_origins=None):
            Returns the singleton instance of the API class. If it does not exist, creates one.
            Args:
                allowed_origins (list, optional): List of allowed origins for CORS. Currently unused.
            Returns:
                API: The singleton API instance.
        app:
            Returns the FastAPI application instance.
    """

    _instance = None

    def __init__(self):
        self._app = FastAPI()
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def app(self):   
        return self._app