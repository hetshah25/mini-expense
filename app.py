from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        data = request.get_json()
        cur.execute("INSERT INTO expenses (name, amount) VALUES (?, ?)", 
                    (data["name"], data["amount"]))
        conn.commit()
        return jsonify({"message": "Added the item"}), 201
    else:
        cur.execute("SELECT * FROM expenses")
        rows = [dict(row) for row in cur.fetchall()]
        total = sum(r["amount"] for r in rows)
        return jsonify({"expenses": rows, "total": total})

if __name__ == "__main__":
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, name TEXT, amount REAL)")
    conn.close()
    app.run(debug=True)
