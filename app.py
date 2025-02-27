from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage (Replace this with a database in the future)
tournaments = {}
latest_tournament_id = None

@app.route('/create_tournament', methods=['POST'])
def create_tournament():
    """Admin creates a tournament with a unique ID."""
    global latest_tournament_id
    data = request.json
    tournament_id = str(len(tournaments) + 1)

    tournaments[tournament_id] = {
        "name": data.get("name", f"Tournament {tournament_id}"),
        "date": data.get("date"),  # Expected format: YYYY-MM-DD
        "teams": {},
        "pairings": [],
        "scores": {},
        "novelty_holes": {"closest_to_pin": [], "longest_drive": []},
        "status": "inactive",
        "round": 1
    }
    latest_tournament_id = tournament_id

    return jsonify({"message": f"Tournament {tournament_id} created.", "tournament_id": tournament_id})

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
    """Organizer starts the tournament (activates it)."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "active"
    return jsonify({"message": f"Tournament {tournament_id} is now active."})

@app.route('/set_teams', methods=['POST'])
def set_teams():
    """Organizer sets Red and Blue teams."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["teams"] = {
        "Red": data.get("red_team", []),
        "Blue": data.get("blue_team", [])
    }

    return jsonify({"message": "Teams set successfully."})

@app.route('/set_pairings', methods=['POST'])
def set_pairings():
    """Organizer sets the pairings for the day."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["pairings"] = data.get("pairings", [])

    return jsonify({"message": "Pairings set successfully."})

@app.route('/start_new_round', methods=['POST'])
def start_new_round():
    """Organizer starts a new round, keeping overall team scores but resetting daily match scores."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["round"] += 1  # Increase round number
    tournaments[tournament_id]["pairings"] = data.get("pairings", tournaments[tournament_id]["pairings"])
    tournaments[tournament_id]["scores"] = {}  # Reset daily scores

    return jsonify({"message": f"Round {tournaments[tournament_id]['round']} started. Pairings updated."})

@app.route('/submit_score', methods=['POST'])
def submit_score():
    """Submit match play score updates."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)
    match = data.get("match")  # Example: "Tom & Phil vs. Joey & Bob"
    result = data.get("result")  # Example: "Tom & Phil won hole 1"

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    if match not in tournaments[tournament_id]["scores"]:
        tournaments[tournament_id]["scores"][match] = "All Square"

    if "won hole" in result:
        winning_team = "Red" if any(player in tournaments[tournament_id]["teams"]["Red"] for player in result.split()) else "Blue"
        tournaments[tournament_id]["scores"][match] = f"{winning_team} Up"

    return jsonify({"message": "Score updated successfully."})

@app.route('/set_novelty_holes', methods=['POST'])
def set_novelty_holes():
    """Organizer sets novelty holes like Closest to the Pin or Longest Drive."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["novelty_holes"] = {
        "closest_to_pin": data.get("closest_to_pin", []),
        "longest_drive": data.get("longest_drive", [])
    }

    return jsonify({"message": "Novelty holes set successfully."})

@app.route('/recall_tournament', methods=['GET'])
def recall_tournament():
    """Retrieves all stored tournament details to reload the session."""
    global latest_tournament_id
    tournament_id = request.args.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    return jsonify(tournaments[tournament_id])

@app.route('/end_tournament', methods=['POST'])
def end_tournament():
    """Lock the tournament and stop accepting scores."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "closed"
    return jsonify({"message": "Tournament has ended. Final scores are locked."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
