import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL, sslmode="require")


@app.route("/admin_create_tournament", methods=["POST"])
def create_tournament():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO tournaments (name, start_date, end_date, format, total_rounds)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data["name"],
            data["start_date"],
            data["end_date"],
            data["format"],
            data["total_rounds"]
        ))
        tournament_id = cur.fetchone()[0]
        conn.commit()
    return jsonify({"message": "Tournament created.", "tournament_id": tournament_id})


@app.route("/register_players", methods=["POST"])
def register_players():
    data = request.json
    tournament_id = data["tournament_id"]
    players = data["players"]

    with conn.cursor() as cur:
        for player in players:
            cur.execute("""
                INSERT INTO players (name, tournament_id)
                VALUES (%s, %s)
            """, (player, tournament_id))
        conn.commit()

    return jsonify({"message": f"{len(players)} players registered."})


@app.route("/create_match", methods=["POST"])
def create_match():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO matches (tournament_id, player1, player2)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            data["tournament_id"],
            data["player1"],
            data["player2"]
        ))
        match_id = cur.fetchone()[0]
        conn.commit()
    return jsonify({"message": "Match created.", "match_id": match_id})


@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO scores (match_id, hole, player1_score, player2_score)
            VALUES (%s, %s, %s, %s)
        """, (
            data["match_id"],
            data["hole"],
            data["score1"],
            data["score2"]
        ))
        conn.commit()
    return jsonify({"message": f"Hole {data['hole']} score submitted."})


@app.route("/scoreboard/<int:tournament_id>", methods=["GET"])
def get_scoreboard(tournament_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.id, m.player1, m.player2
            FROM matches m
            WHERE m.tournament_id = %s
        """, (tournament_id,))
        matches = cur.fetchall()

        match_list = []
        for match_id, p1, p2 in matches:
            cur.execute("""
                SELECT hole, player1_score, player2_score
                FROM scores
                WHERE match_id = %s
                ORDER BY hole ASC
            """, (match_id,))
            scores = cur.fetchall()

            p1_wins = p2_wins = 0
            holes_played = []
            for hole, s1, s2 in scores:
                if s1 < s2:
                    p1_wins += 1
                    winner = p1
                elif s2 < s1:
                    p2_wins += 1
                    winner = p2
                else:
                    winner = "Halved"
                holes_played.append({
                    "hole": hole,
                    "scores": {p1: s1, p2: s2},
                    "winner": winner
                })

            if p1_wins > p2_wins:
                status = f"{p1} {p1_wins - p2_wins} Up"
            elif p2_wins > p1_wins:
                status = f"{p2} {p2_wins - p1_wins} Up"
            else:
                status = "All Square"

            match_list.append({
                "match_id": match_id,
                "players": [p1, p2],
                "match_status": status,
                "holes_played": holes_played
            })

    return jsonify({
        "tournament_id": tournament_id,
        "matches": match_list
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

