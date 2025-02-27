from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage (resets when restarted)
tournaments = {}

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
    """Start a new tournament and return its ID."""
    tournament_id = str(len(tournaments) + 1)
    tournaments[tournament_id] = {"players": {}, "scores": {}}
    return jsonify({"tournament_id": tournament_id})

@app.route('/add_player', methods=['POST'])
def add_player():
    """Add a player to the tournament."""
    data = request.json
    tournament_id = data.get('tournament_id')
    player_name = data.get('player_name')

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    player_id = str(len(tournaments[tournament_id]["players"]) + 1)
    tournaments[tournament_id]["players"][player_id] = player_name
    tournaments[tournament_id]["scores"][player_id] = []
    
    return jsonify({"player_id": player_id})

@app.route('/submit_score', methods=['POST'])
def submit_score():
    """Submit a score for a player."""
    data = request.json
    tournament_id = data.get('tournament_id')
    player_id = data.get('player_id')
    hole_number = data.get('hole_number')
    score = data.get('score')

    if tournament_id not in tournaments or player_id not in tournaments[tournament_id]["players"]:
        return jsonify({"error": "Invalid tournament or player ID"}), 400

    tournaments[tournament_id]["scores"][player_id].append({"hole": hole_number, "score": score})
    
    return jsonify({"message": "Score submitted successfully"})

@app.route('/get_standings', methods=['GET'])
def get_standings():
    """Get the current tournament standings."""
    tournament_id = request.args.get('tournament_id')

    if tournament_id not in tournaments:
        return jsonify({"error": "Invalid tournament ID"}), 400

    standings = [
        {
            "player_name": tournaments[tournament_id]["players"][player_id],
            "total_score": sum(score["score"] for score in tournaments[tournament_id]["scores"][player_id])
        }
        for player_id in tournaments[tournament_id]["players"]
    ]
    
    standings.sort(key=lambda x: x["total_score"])  # Sort by lowest score (golf)
    
    return jsonify({"standings": standings})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
