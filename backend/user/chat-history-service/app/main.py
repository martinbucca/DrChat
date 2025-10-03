import uvicorn
from app.services.driver import Neo4jDriver
from app.api.api import API
from app.api.endpoints.update_session_name import UpdateSessionNameEndpoint
from app.api.endpoints.get_user_sessions import GetUserSessionsEndpoint
from app.api.endpoints.delete_session import DeleteSessionEndpoint
from app.api.endpoints.create_session import CreateSessionEndpoint
from app.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


driver_instance = Neo4jDriver.get_instance(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
driver = driver_instance.driver

api_instance = API.get_instance()

app = api_instance.app

GetUserSessionsEndpoint.register(app, driver)
UpdateSessionNameEndpoint.register(app, driver)
DeleteSessionEndpoint.register(app, driver)
CreateSessionEndpoint.register(app, driver)

@app.on_event("shutdown")
def shutdown_event():
    driver.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)