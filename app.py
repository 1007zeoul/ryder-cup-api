from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage (Replace with a database in the future)
tournaments = {}
latest_tournament_id = None

@app.route('/admin_create_tournament', methods=['POST'])
def admin_create_tournament():
    """Admin creates a tournament with a unique ID."""
    global latest_tournament_id
    data = request.json
    tournament_id = str(len(tournaments) + 1)  # Auto-generate a unique ID

    tournaments[tournament_id] = {
        "name": data.get("name", f"Tournament {tournament_id}"),
        "start_date": data.get("start_date"),  # Expected format: YYYY-MM-DD
        "end_date": data.get("end_date"),  # Expected format: YYYY-MM-DD
        "teams": {},
        "pairings": [],
        "scores": {},
        "novelty_holes": {"closest_to_pin": [], "longest_drive": []},
        "status": "inactive",
        "round": 1
    }
    latest_tournament_id = tournament_id  # Store the latest created tournament

    return jsonify({
        "message": f"Tournament '{tournaments[tournament_id]['name']}' created.",
        "tournament_id": tournament_id
    })

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
    """Organizer starts the tournament but cannot create a new one."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "active"
    return jsonify({"message": f"Tournament '{tournaments[tournament_id]['name']}' is now active."})

# Other tournament management endpoints remain the same...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
