import json
import random
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

TOURNAMENTS_FILE = "tournaments.json"

# Load tournaments from file (if exists)
def load_tournaments():
    try:
        with open(TOURNAMENTS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save tournaments to file
def save_tournaments():
    with open(TOURNAMENTS_FILE, "w") as file:
        json.dump(tournaments, file, indent=4)

# Load tournaments into memory on startup
tournaments = load_tournaments()
latest_tournament_id = None if not tournaments else max(tournaments.keys())

@app.route('/admin_create_tournament', methods=['POST'])
def admin_create_tournament():
    """Admin creates a tournament with a random 4-digit ID and saves it to a file."""
    global latest_tournament_id
    data = request.json

    # Generate a unique 4-digit tournament ID
    while True:
        tournament_id = str(random.randint(1000, 9999))
        if tournament_id not in tournaments:
            break

    tournaments[tournament_id] = {
        "name": data.get("name", f"Tournament {tournament_id}"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "teams": {},
        "pairings": [],
        "scores": {},
        "novelty_holes": {"closest_to_pin": [], "longest_drive": []},
        "status": "inactive",
        "round": 1
    }
    latest_tournament_id = tournament_id

    save_tournaments()  # Save to file

    return jsonify({
        "message": f"Tournament '{tournaments[tournament_id]['name']}' created.",
        "tournament_id": tournament_id
    })

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
    """Organizer starts the tournament."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "active"
    save_tournaments()  # Save changes

    return jsonify({"message": f"Tournament '{tournaments[tournament_id]['name']}' is now active."})

@app.route('/recall_tournament', methods=['GET'])
def recall_tournament():
    """Retrieves stored tournament details."""
    global latest_tournament_id
    tournament_id = request.args.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    return jsonify(tournaments[tournament_id])

@app.route('/end_tournament', methods=['POST'])
def end_tournament():
    """Locks the tournament and stops accepting scores."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "closed"
    save_tournaments()  # Save changes

    return jsonify({"message": "Tournament has ended. Final scores are locked."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
