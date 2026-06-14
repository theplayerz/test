from flask import Flask, request, jsonify
import subprocess
import re

app = Flask(__name__)

# =========================
# 출력 정리 함수
# =========================
def clean_output(text):
    if not text:
        return ""

    # ANSI escape 제거
    text = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)

    # Windows 안전 처리
    return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")


# =========================
# API
# =========================
@app.route("/run", methods=["POST"])
def run():
    data = request.json.get("message")

    print("받은 요청:", data)

    try:
        # =========================
        # opencode 실행 (기본 모델 사용)
        # =========================
        result = subprocess.run(
            ["opencode", "run", data],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=120,
            shell=True
        )

        output = clean_output(result.stdout)
        error = clean_output(result.stderr)

        return jsonify({
            "input": data,
            "output": output,
            "error": error
        })

    except Exception as e:
        return jsonify({
            "input": data,
            "output": "",
            "error": str(e)
        })


# =========================
# 서버 실행
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)