import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def run():
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "api.routes:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    run()
