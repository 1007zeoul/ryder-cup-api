import json
import random
from flask import Flask, request, jsonify

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
    """Admin creates a tournament with format and rounds."""
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
        "format": data.get("format", "Ryder Cup"),  # Default to Ryder Cup
        "total_rounds": int(data.get("total_rounds", 1)),  # Default 1 round
        "current_round": 1,  # Start at round 1
        "teams": {},
        "pairings": [],
        "scores": {},
        "novelty_holes": {"closest_to_pin": [], "longest_drive": []},
        "status": "inactive"
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
    save_tournaments()

    return jsonify({"message": f"Tournament '{tournaments[tournament_id]['name']}' is now active."})

@app.route('/start_new_round', methods=['POST'])
def start_new_round():
    """Starts a new round. Ends tournament if it's the last round."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    # Check if tournament is already finished
    if tournaments[tournament_id]["current_round"] >= tournaments[tournament_id]["total_rounds"]:
        tournaments[tournament_id]["status"] = "closed"
        save_tournaments()
        return jsonify({"message": f"Tournament '{tournaments[tournament_id]['name']}' has ended. No more rounds can be started."})

    # Increase the round number
    tournaments[tournament_id]["current_round"] += 1
    save_tournaments()

    return jsonify({"message": f"Round {tournaments[tournament_id]['current_round']} started."})

@app.route('/submit_score', methods=['POST'])
def submit_score():
    """Records a score for a match and tracks the status."""
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)
    hole = data.get("hole")
    player1 = data.get("player1")
    score1 = data.get("score1")
    player2 = data.get("player2")
    score2 = data.get("score2")

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    if tournaments[tournament_id]["status"] != "active":
        return jsonify({"error": "Tournament is not active"}), 400

    # Initialize scores if they don't exist
    if "match_scores" not in tournaments[tournament_id]:
        tournaments[tournament_id]["match_scores"] = {}

    # Record hole scores
    tournaments[tournament_id]["match_scores"][hole] = {
        player1: score1,
        player2: score2
    }

    # Determine hole winner
    if score1 < score2:
        winner = player1
    elif score2 < score1:
        winner = player2
    else:
        winner = "Halved"

    # Update match status
    match_status = calculate_match_status(tournament_id, player1, player2)

    save_tournaments()

    return jsonify({
        "message": f"Hole {hole} recorded: {player1} {score1}, {player2} {score2}",
        "winner": winner,
        "match_status": match_status
    })

def calculate_match_status(tournament_id, player1, player2):
    """Calculates match play status based on recorded scores."""
    scores = tournaments[tournament_id].get("match_scores", {})

    player1_wins = sum(1 for hole, result in scores.items() if result.get(player1) < result.get(player2))
    player2_wins = sum(1 for hole, result in scores.items() if result.get(player2) < result.get(player1))

    if player1_wins > player2_wins:
        return f"{player1} {player1_wins - player2_wins} Up"
    elif player2_wins > player1_wins:
        return f"{player2} {player2_wins - player1_wins} Up"
    else:
        return "All Square"

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
    save_tournaments()

    return jsonify({"message": "Tournament has ended. Final scores are locked."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
