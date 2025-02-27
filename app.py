import random
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage (Replace with a database in the future)
tournaments = {}
latest_tournament_id = None

@app.route('/admin_create_tournament', methods=['POST'])
def admin_create_tournament():
    """Admin creates a tournament with a random 4-digit ID."""
    global latest_tournament_id
    data = request.json
    
    # Generate a unique 4-digit tournament ID
    while True:
        tournament_id = str(random.randint(1000, 9999))  # Random 4-digit number
        if tournament_id not in tournaments:  # Ensure it’s unique
            break

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
