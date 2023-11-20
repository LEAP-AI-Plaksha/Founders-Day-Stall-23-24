import base64
from flask import Flask, jsonify, request
from datetime import datetime
from flask_cors import CORS
import requests
import os
import json
from werkzeug.utils import secure_filename
import subprocess
from pathlib import Path

app = Flask(__name__)
CORS(app)


@app.route("/api/animate", methods=["PUT"])
def put_animate():
    if request.method == "PUT":
        animation_id = request.args.get("animation")
        if animation_id is None:
            animation_id = 1

        # check if file is present
        file = request.files["file"]
        path = os.path.join(
            "raw_images",
            f"{datetime.now().isoformat()}_{secure_filename(file.filename)}",
        )
        file.save(path)

        # ensure docker container is running
        try:
            resp = requests.get("http://localhost:8080/ping")
        except requests.exceptions.ConnectionError:
            response = jsonify({"status": "failure"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        if resp.status_code == 200 and json.loads(resp.content)["status"] == "Healthy":
            print("Docker container is running")

        path2 = Path(
            f"animation_out/{datetime.now().isoformat()}_{secure_filename(file.filename.split('.')[0])}"
        )
        cmd = f"source ~/.zshrc; conda activate animated_drawings; python3 image_to_animation.py {Path(path).absolute()} {path2.absolute()}; conda deactivate"
        print(cmd)
        out = subprocess.run(
            cmd,
            shell=True,
            cwd="/Users/pranjalrastogi/repos/newtry/AnimatedDrawings/examples"
        )
        # the code above works from ANY terminal window, but does not work from flask.
        ogifpath = path2 / "video.gif"
        
        response = jsonify({"status": "success", "gif_path": str(ogifpath.absolute())})
        return response

@app.after_request
def after_request(response):
    response.access_control_allow_origin = "*"
    response.headers.add("Access-Control-Allow-Methods", "PUT, OPTIONS")
    print(response)
    return response

if __name__ == "__main__":
    app.run(port=3000)
