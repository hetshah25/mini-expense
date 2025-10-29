# app.py
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import decimal

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Mini Expense Tracker</title>
  <style>
    body { font-family: Inter, system-ui, -apple-system, Arial; max-width: 720px; margin: 36px auto; padding: 0 16px; color:#111; }
    h1 { margin-bottom: 6px; }
    form { display:flex; gap:8px; margin-bottom:18px; align-items:center; }
    input[type="text"], input[type="number"] { padding:8px 10px; font-size:16px; border:1px solid #ddd; border-radius:6px; }
    button { padding:9px 12px; border-radius:8px; border:none; background:#0b74ff; color:white; font-weight:600; cursor:pointer; }
    table { width:100%; border-collapse:collapse; margin-top:14px; }
    th, td { text-align:left; padding:8px; border-bottom:1px solid #eee; }
    tfoot td { font-weight:700; }
    .muted { color:#666; font-size:13px; }
    .error { color: #b00020; }
  </style>
</head>
<body>
  <h1>Mini Expense Tracker</h1>
  <p class="muted">Add an expense (name + amount). Data is stored in a local SQLite database.</p>

  <form id="expense-form">
    <input id="name" type="text" placeholder="Expense name (e.g., Coffee)" required />
    <input id="amount" type="number" step="0.01" placeholder="Amount" required />
    <button type="submit">Add</button>
  </form>

  <div id="message" class="muted"></div>

  <table id="expenses-table" aria-live="polite">
    <thead>
      <tr><th>Item</th><th>Amount</th></tr>
    </thead>
    <tbody id="expenses-body"></tbody>
    <tfoot>
      <tr><td>Total</td><td id="total-amount">$0.00</td></tr>
    </tfoot>
  </table>

<script>
async function fetchExpenses() {
  try {
    const res = await fetch('/expenses');
    const data = await res.json();
    const tbody = document.getElementById('expenses-body');
    tbody.innerHTML = '';
    data.expenses.forEach(e => {
      const tr = document.createElement('tr');
      const nameTd = document.createElement('td');
      nameTd.textContent = e.name;
      const amountTd = document.createElement('td');
      amountTd.textContent = '$' + Number(e.amount).toFixed(2);
      tr.appendChild(nameTd);
      tr.appendChild(amountTd);
      tbody.appendChild(tr);
    });
    document.getElementById('total-amount').textContent = '$' + Number(data.total).toFixed(2);
  } catch (err) {
    document.getElementById('message').textContent = 'Failed to load expenses.';
    document.getElementById('message').classList.add('error');
    console.error(err);
  }
}

document.getElementById('expense-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name').value.trim();
  const amount = document.getElementById('amount').value;
  if (!name || amount === '') return;

  try {
    const res = await fetch('/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, amount: Number(amount) })
    });
    if (!res.ok) {
      const err = await res.json();
      document.getElementById('message').textContent = err.message || 'Failed to add';
      document.getElementById('message').classList.add('error');
      return;
    }
    // clear form
    document.getElementById('name').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('message').textContent = 'Added ✓';
    document.getElementById('message').classList.remove('error');
    setTimeout(() => { document.getElementById('message').textContent = ''; }, 1800);
    await fetchExpenses();
  } catch (err) {
    document.getElementById('message').textContent = 'Network error';
    document.getElementById('message').classList.add('error');
    console.error(err);
  }
});

// initial load
fetchExpenses();
</script>
</body>
</html>
"""

def get_db():
    conn = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        # ensure decimal-handling for money
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid amount"}), 400
        if not name:
            return jsonify({"message": "Name required"}), 400
        cur.execute("INSERT INTO expenses (name, amount) VALUES (?, ?)", (name, amount))
        conn.commit()
        return jsonify({"message": "Added"}), 201

    # GET
    cur.execute("SELECT id, name, amount FROM expenses ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    total = sum(float(r["amount"]) for r in rows)
    return jsonify({"expenses": rows, "total": total})

if __name__ == "__main__":
    # create table if not exists
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

    # Run dev server
    app.run(debug=True, host="0.0.0.0", port=5000)
