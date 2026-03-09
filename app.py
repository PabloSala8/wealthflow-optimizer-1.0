import os
import uuid
import json
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
import config
from logic.parser import load_and_normalize
from logic.fees import load_broker_specs, generate_full_comparison
from logic.health_score import compute_health_score
from utils.ai_advisor import generate_executive_summary, chat_with_advisor

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

specs = load_broker_specs(config.BROKER_SPECS_PATH)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


@app.route("/")
def index():
    brokers = [{"id": b["id"], "name": b["name"]} for b in specs.values()]
    return render_template("index.html", brokers=brokers)


@app.route("/audit", methods=["POST"])
def audit():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    broker_id = request.form.get("broker_id", "").lower()

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file. Please upload a CSV."}), 400
    if broker_id not in specs:
        return jsonify({"error": f"Unknown broker: {broker_id}"}), 400

    session_id = str(uuid.uuid4())
    filename = secure_filename(f"{session_id}.csv")
    filepath = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        portfolio = load_and_normalize(filepath)
    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 422
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    portfolio_dict = {
        "total_cash": portfolio.total_cash,
        "total_options_contracts": portfolio.total_options_contracts,
        "holdings": portfolio.holdings,
    }

    comparison = generate_full_comparison(portfolio_dict, broker_id, specs)
    mutual_fund_flags = comparison[list(comparison.keys())[0]]["mutual_fund_flags"]

    health = compute_health_score(
        total_cash=portfolio.total_cash,
        current_broker_id=broker_id,
        specs=specs,
        comparison=comparison,
        mutual_fund_flags=mutual_fund_flags,
    )

    alternatives = {bid: v for bid, v in comparison.items() if bid != broker_id}
    best_id = max(alternatives, key=lambda b: alternatives[b]["total_annual_savings_usd"])
    best = comparison[best_id]

    aum = portfolio.total_market_value + portfolio.total_cash
    executive_summary = generate_executive_summary(
        aum=aum,
        health_score=health["score"],
        health_band=health["band"],
        sweep_loss_annual=best["sweep"]["annual_loss_usd"],
        sweep_bps=best["sweep"]["basis_point_delta"],
        best_broker_name=best["broker_name"],
        annual_savings=best["total_annual_savings_usd"],
        acats_breakeven_months=best["breakeven_months"],
        current_broker_name=specs[broker_id]["name"],
    )

    result = {
        "session_id": session_id,
        "current_broker_id": broker_id,
        "current_broker_name": specs[broker_id]["name"],
        "portfolio": {
            "total_market_value": portfolio.total_market_value,
            "total_cash": portfolio.total_cash,
            "total_options_contracts": portfolio.total_options_contracts,
            "aum": round(aum, 2),
            "holdings_count": len(portfolio.holdings),
        },
        "health": health,
        "comparison": comparison,
        "best_broker_id": best_id,
        "executive_summary": executive_summary,
        "mutual_fund_flags": mutual_fund_flags,
    }

    for bid, v in result["comparison"].items():
        if v["breakeven_months"] == float("inf"):
            v["breakeven_months"] = None

    return jsonify(result)


@app.route("/report")
def report():
    return render_template("report.html")


@app.route("/brokers")
def brokers():
    return jsonify({"brokers": list(specs.values())})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or session.get("session_id", "anonymous")
    context = data.get("context", {})

    if not message:
        return jsonify({"error": "Empty message"}), 400

    reply = chat_with_advisor(message, session_id, context)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG, host="0.0.0.0", port=5000)
