import uvicorn
from jonex_core.sidecar import get_sidecar_app

app = get_sidecar_app().get_app()
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
