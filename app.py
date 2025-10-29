from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Mini Expense Tracker by Het</title>
  <style>
    body { font-family: Inter, system-ui, -apple-system, Arial; max-width: 720px; margin: 36px auto; padding: 0 16px; color:#111; }
    h1 { margin-bottom: 6px; }
    form { display:flex; gap:8px; margin-bottom:18px; align-items:center; }
    input[type="text"], input[type="number"] { padding:8px 10px; font-size:16px; border:1px solid #ddd; border-radius:6px; }
    button { padding:9px 12px; border-radius:6px; border:none; background:#0b74ff; color:white; font-weight:600; cursor:pointer; }
    button.delete { background:#e74c3c; }
    button.clear { background:#555; margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:14px; }
    th, td { text-align:left; padding:8px; border-bottom:1px solid #eee; }
    tfoot td { font-weight:700; }
    .muted { color:#666; font-size:13px; }
    .error { color: #b00020; }
  </style>
</head>
<body>
  <h1>Mini Expense Tracker by Het</h1>
  <p class="muted">Add, delete, or clear all expenses. Data is stored locally in SQLite.</p>

  <form id="expense-form">
    <input id="name" type="text" placeholder="Expense name (e.g., Coffee)" required />
    <input id="amount" type="number" step="0.01" placeholder="Amount" required />
    <button type="submit">Add</button>
  </form>

  <div id="message" class="muted"></div>

  <table id="expenses-table" aria-live="polite">
    <thead>
      <tr><th>Item</th><th>Amount</th><th></th></tr>
    </thead>
    <tbody id="expenses-body"></tbody>
    <tfoot>
      <tr><td>Total</td><td id="total-amount">$0.00</td><td></td></tr>
    </tfoot>
  </table>

  <button class="clear" id="clear-all">Clear All</button>

<script>
async function fetchExpenses() {
  try {
    const res = await fetch('/expenses');
    const data = await res.json();
    const tbody = document.getElementById('expenses-body');
    tbody.innerHTML = '';
    data.expenses.forEach(e => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${e.name}</td>
        <td>$${Number(e.amount).toFixed(2)}</td>
        <td><button class="delete" data-id="${e.id}">Delete</button></td>
      `;
      tbody.appendChild(tr);
    });

    // delete buttons
    document.querySelectorAll('.delete').forEach(btn => {
      btn.onclick = async () => {
        await fetch('/expenses/' + btn.dataset.id, { method: 'DELETE' });
        fetchExpenses();
      };
    });

    document.getElementById('total-amount').textContent = '$' + Number(data.total).toFixed(2);
  } catch (err) {
    document.getElementById('message').textContent = 'Failed to load expenses.';
    document.getElementById('message').classList.add('error');
  }
}

document.getElementById('expense-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name').value.trim();
  const amount = document.getElementById('amount').value;
  if (!name || amount === '') return;

  const res = await fetch('/expenses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, amount: Number(amount) })
  });

  if (res.ok) {
    document.getElementById('name').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('message').textContent = 'Added ✓';
    setTimeout(() => { document.getElementById('message').textContent = ''; }, 1800);
    fetchExpenses();
  }
});

document.getElementById('clear-all').addEventListener('click', async () => {
  await fetch('/expenses', { method: 'DELETE' });
  fetchExpenses();
});

// Initial load
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

@app.route("/expenses", methods=["GET", "POST", "DELETE"])
def expenses():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid amount"}), 400
        if not name:
            return jsonify({"message": "Name required"}), 400
        cur.execute("INSERT INTO expenses (name, amount) VALUES (?, ?)", (name, amount))
        conn.commit()
        return jsonify({"message": "Added"}), 201

    if request.method == "DELETE":
        cur.execute("DELETE FROM expenses")
        conn.commit()
        return jsonify({"message": "All cleared"}), 200

    # GET
    cur.execute("SELECT id, name, amount FROM expenses ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    total = sum(float(r["amount"]) for r in rows)
    return jsonify({"expenses": rows, "total": total})

@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return jsonify({"message": "Deleted"}), 200

if __name__ == "__main__":
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
    app.run(debug=True, host="0.0.0.0", port=5000)
