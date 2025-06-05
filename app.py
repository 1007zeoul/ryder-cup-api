import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

@app.route('/admin_create_tournament', methods=['POST'])
def admin_create_tournament():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO tournaments (name, start_date, end_date, format, total_rounds)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (
            data.get("name"),
            data.get("start_date"),
            data.get("end_date"),
            data.get("format"),
            data.get("total_rounds")
        ))
        tournament_id = cur.fetchone()[0]
        conn.commit()
    return jsonify({"message": "Tournament created.", "tournament_id": tournament_id})

@app.route('/start_tournament', methods=['POST'])
def start_tournament():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("UPDATE tournaments SET status = 'active' WHERE id = %s", (data.get("tournament_id"),))
        conn.commit()
    return jsonify({"message": f"Tournament {data.get('tournament_id')} started."})

@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO scores (tournament_id, hole, player1, score1, player2, score2)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get("tournament_id"),
            data.get("hole"),
            data.get("player1"),
            data.get("score1"),
            data.get("player2"),
            data.get("score2")
        ))
        conn.commit()
    return jsonify({"message": "Score submitted."})

@app.route('/scoreboard/<int:tournament_id>', methods=['GET'])
def get_scoreboard(tournament_id):
    with conn.cursor() as cur:
        cur.execute("SELECT name, current_round, status FROM tournaments WHERE id = %s", (tournament_id,))
        tournament = cur.fetchone()
        if not tournament:
            return jsonify({"error": "Tournament not found"}), 404
        name, current_round, status = tournament

        cur.execute("""
            SELECT hole, player1, score1, player2, score2
            FROM scores
            WHERE tournament_id = %s
            ORDER BY hole ASC
        """, (tournament_id,))
        rows = cur.fetchall()

    scores = []
    for hole, p1, s1, p2, s2 in rows:
        winner = p1 if s1 < s2 else p2 if s2 < s1 else "Halved"
        scores.append({
            "hole": hole,
            "scores": {p1: s1, p2: s2},
            "winner": winner
        })

    return jsonify({
        "tournament_id": tournament_id,
        "tournament_name": name,
        "status": status,
        "current_round": current_round,
        "total_holes_played": len(scores),
        "scoreboard": scores
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

