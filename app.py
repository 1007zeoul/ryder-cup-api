import json
import random
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

TOURNAMENTS_FILE = "tournaments.json"

def load_tournaments():
    try:
        with open(TOURNAMENTS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_tournaments():
    with open(TOURNAMENTS_FILE, "w") as file:
        json.dump(tournaments, file, indent=4)

tournaments = load_tournaments()
latest_tournament_id = None if not tournaments else max(tournaments.keys())

@app.route('/admin_create_tournament', methods=['POST'])
def admin_create_tournament():
    global latest_tournament_id
    data = request.json

    while True:
        tournament_id = str(random.randint(1000, 9999))
        if tournament_id not in tournaments:
            break

    tournaments[tournament_id] = {
        "name": data.get("name", f"Tournament {tournament_id}"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "format": data.get("format", "Ryder Cup"),
        "total_rounds": int(data.get("total_rounds", 1)),
        "current_round": 1,
        "teams": {},
        "pairings": [],
        "scores": {},
        "novelty_holes": {"closest_to_pin": [], "longest_drive": []},
        "status": "inactive"
    }
    latest_tournament_id = tournament_id
    save_tournaments()

    return jsonify({
        "message": f"Tournament '{tournaments[tournament_id]['name']}' created.",
        "tournament_id": tournament_id
    })

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
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
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    if tournaments[tournament_id]["current_round"] >= tournaments[tournament_id]["total_rounds"]:
        tournaments[tournament_id]["status"] = "closed"
        save_tournaments()
        return jsonify({"message": f"Tournament '{tournaments[tournament_id]['name']}' has ended."})

    tournaments[tournament_id]["current_round"] += 1
    save_tournaments()

    return jsonify({"message": f"Round {tournaments[tournament_id]['current_round']} started."})

@app.route('/submit_score', methods=['POST'])
def submit_score():
    global latest_tournament_id
    data = request.json
    print("Incoming score submission:", data)  # Log incoming data

    tournament_id = data.get("tournament_id", latest_tournament_id)
    hole = str(data.get("hole"))
    player1 = data.get("player1")
    score1 = data.get("score1")
    player2 = data.get("player2")
    score2 = data.get("score2")

    if not all([tournament_id, hole, player1, player2]) or score1 is None or score2 is None:
        return jsonify({"error": "Missing required fields"}), 400

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    if tournaments[tournament_id]["status"] != "active":
        return jsonify({"error": "Tournament is not active"}), 400

    if "match_scores" not in tournaments[tournament_id]:
        tournaments[tournament_id]["match_scores"] = {}

    tournaments[tournament_id]["match_scores"][hole] = {
        player1: score1,
        player2: score2
    }

    if score1 < score2:
        winner = player1
    elif score2 < score1:
        winner = player2
    else:
        winner = "Halved"

    match_status = calculate_match_status(tournament_id, player1, player2)
    save_tournaments()

    return jsonify({
        "message": f"Hole {hole} recorded: {player1} {score1}, {player2} {score2}",
        "winner": winner,
        "match_status": match_status
    })

def calculate_match_status(tournament_id, player1, player2):
    scores = tournaments[tournament_id].get("match_scores", {})
    player1_wins = sum(1 for _, result in scores.items() if player1 in result and player2 in result and result[player1] < result[player2])
    player2_wins = sum(1 for _, result in scores.items() if player1 in result and player2 in result and result[player2] < result[player1])

    if player1_wins > player2_wins:
        return f"{player1} {player1_wins - player2_wins} Up"
    elif player2_wins > player1_wins:
        return f"{player2} {player2_wins - player1_wins} Up"
    else:
        return "All Square"

@app.route('/recall_tournament', methods=['GET'])
def recall_tournament():
    global latest_tournament_id
    tournament_id = request.args.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    return jsonify(tournaments[tournament_id])

@app.route('/end_tournament', methods=['POST'])
def end_tournament():
    global latest_tournament_id
    data = request.json
    tournament_id = data.get("tournament_id", latest_tournament_id)

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    tournaments[tournament_id]["status"] = "closed"
    save_tournaments()

    return jsonify({"message": "Tournament has ended. Final scores are locked."})

@app.route('/scoreboard/<tournament_id>', methods=['GET'])
def get_scoreboard(tournament_id):
    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 404

    tournament = tournaments[tournament_id]
    scores = tournament.get("match_scores", {})
    players = set()
    detailed_scores = []

    for hole, result in sorted(scores.items(), key=lambda x: int(x[0])):
        if not isinstance(result, dict) or len(result) < 2:
            continue  # Skip invalid or incomplete scores

        names = list(result.keys())
        p1, p2 = names[0], names[1]
        s1, s2 = result[p1], result[p2]
        players.update([p1, p2])

        if s1 < s2:
            hole_winner = p1
        elif s2 < s1:
            hole_winner = p2
        else:
            hole_winner = "Halved"

        detailed_scores.append({
            "hole": int(hole),
            "scores": {p1: s1, p2: s2},
            "winner": hole_winner
        })

    if len(players) == 2:
        player1, player2 = sorted(list(players))
        match_status = calculate_match_status(tournament_id, player1, player2)
    else:
        match_status = "Not enough data"

    return jsonify({
        "tournament_id": tournament_id,
        "tournament_name": tournament.get("name"),
        "status": tournament.get("status"),
        "current_round": tournament.get("current_round"),
        "total_holes_played": len(detailed_scores),
        "match_status": match_status,
        "scoreboard": detailed_scores
    })

@app.route('/debug_tournament/<tournament_id>', methods=['GET'])
def debug_tournament(tournament_id):
    """Inspect raw tournament data for debugging."""
    return jsonify(tournaments.get(tournament_id, {"error": "Not found"}))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
