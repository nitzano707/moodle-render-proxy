import os
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

MOODLE_URL = "https://moodle4.talpiot.ac.il/webservice/rest/server.php"

MOODLE_TOKEN = os.environ.get("MOODLE_TOKEN")
PROXY_SECRET = os.environ.get("PROXY_SECRET")

ALLOWED_FUNCTIONS = {
    "core_webservice_get_site_info",
    "core_enrol_get_users_courses",
    "core_enrol_get_enrolled_users",
    "mod_assign_get_assignments",
    "mod_assign_get_submissions",
}


@app.get("/")
def health():
    return jsonify({
        "status": "ok",
        "service": "moodle-render-proxy"
    })


@app.post("/moodle")
def moodle_proxy():
    proxy_key = request.headers.get("X-Proxy-Key")

    if not PROXY_SECRET or proxy_key != PROXY_SECRET:
        return Response("Unauthorized", status=401)

    if not MOODLE_TOKEN:
        return Response("MOODLE_TOKEN is not configured", status=500)

    data = request.get_json(silent=True) or {}

    wsfunction = data.get("wsfunction")
    params = data.get("params", {})

    if wsfunction not in ALLOWED_FUNCTIONS:
        return Response("Function not allowed", status=403)

    payload = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
    }

    if isinstance(params, dict):
        payload.update(params)

    try:
        response = requests.post(
            MOODLE_URL,
            data=payload,
            timeout=30
        )
    except requests.RequestException as e:
        return jsonify({
            "error": "Could not reach Moodle",
            "details": str(e)
        }), 502

    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get(
            "Content-Type",
            "application/json"
        )
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
