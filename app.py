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
    form { display:flex; gap:8px; margin-bottom:18px; align-items:center; flex-wrap: wrap; }
    .filters { display:flex; gap:8px; margin-bottom:18px; align-items:center; }
    input[type="text"], input[type="number"], select { padding:8px 10px; font-size:16px; border:1px solid #ddd; border-radius:6px; }
    select { background-color: white; min-width: 140px; }
    button { padding:9px 12px; border-radius:6px; border:none; background:#0b74ff; color:white; font-weight:600; cursor:pointer; }
    button.edit { background:#f39c12; }
    button.delete { background:#e74c3c; }
    button.clear { background:#555; margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:14px; }
    th, td { text-align:left; padding:8px; border-bottom:1px solid #eee; }
    tfoot td { font-weight:700; }
    .muted { color:#666; font-size:13px; }
    .error { color: #b00020; }
    .category-badge { background: #f0f0f0; padding: 2px 6px; border-radius: 12px; font-size: 12px; }
  </style>
</head>
<body>
  <h1>Mini Expense Tracker by Het</h1>
  <p class="muted">Add, edit, delete, or clear all expenses. Data is stored locally in SQLite.</p>

  <form id="expense-form">
    <input id="name" type="text" placeholder="Expense name (e.g., Coffee)" required />
    <input id="amount" type="number" step="0.01" placeholder="Amount" required />
    <select id="category" required>
      <option value="">Select Category</option>
      <option value="Food">🍔 Food</option>
      <option value="Transportation">🚗 Transportation</option>
      <option value="Entertainment">🎬 Entertainment</option>
      <option value="Shopping">🛒 Shopping</option>
      <option value="Bills">💸 Bills</option>
      <option value="Healthcare">🏥 Healthcare</option>
      <option value="Education">📚 Education</option>
      <option value="Travel">✈️ Travel</option>
      <option value="Groceries">🛍️ Groceries</option>
      <option value="Other">📦 Other</option>
    </select>
    <button type="submit">Add</button>
  </form>

  <div class="filters">
    <select id="category-filter">
      <option value="">All Categories</option>
      <option value="Food">🍔 Food</option>
      <option value="Transportation">🚗 Transportation</option>
      <option value="Entertainment">🎬 Entertainment</option>
      <option value="Shopping">🛒 Shopping</option>
      <option value="Bills">💸 Bills</option>
      <option value="Healthcare">🏥 Healthcare</option>
      <option value="Education">📚 Education</option>
      <option value="Travel">✈️ Travel</option>
      <option value="Groceries">🛍️ Groceries</option>
      <option value="Other">📦 Other</option>
    </select>
    <button id="clear-filter">Clear Filter</button>
  </div>

  <div id="message" class="muted"></div>

  <table id="expenses-table" aria-live="polite">
    <thead>
      <tr><th>Item</th><th>Category</th><th>Amount</th><th>Actions</th></tr>
    </thead>
    <tbody id="expenses-body"></tbody>
    <tfoot>
      <tr><td colspan="2">Total</td><td id="total-amount">$0.00</td><td></td></tr>
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

    if (data.expenses.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="muted">No expenses yet.</td></tr>';
    }

    data.expenses.forEach(e => {
      const tr = document.createElement('tr');
      const categoryIcon = getCategoryIcon(e.category);
      tr.innerHTML = `
        <td>${e.name}</td>
        <td><span class="category-badge">${categoryIcon} ${e.category || 'Other'}</span></td>
        <td>$${Number(e.amount).toFixed(2)}</td>
        <td>
          <button class="edit" data-id="${e.id}" data-name="${e.name}" data-amount="${e.amount}" data-category="${e.category || 'Other'}">Edit</button>
          <button class="delete" data-id="${e.id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('total-amount').textContent = '$' + Number(data.total).toFixed(2);
  } catch (err) {
    console.error('Error fetching expenses:', err);
  }
}

function getCategoryIcon(category) {
  const icons = {
    'Food': '🍔',
    'Transportation': '🚗',
    'Entertainment': '🎬',
    'Shopping': '🛒',
    'Bills': '💸',
    'Healthcare': '🏥',
    'Education': '📚',
    'Travel': '✈️',
    'Groceries': '🛍️',
    'Other': '📦'
  };
  return icons[category] || '📦';
}

// Handle add/update
document.getElementById('expense-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  const nameInput = document.getElementById('name');
  const amountInput = document.getElementById('amount');
  const categoryInput = document.getElementById('category');
  const submitButton = e.target.querySelector('button[type="submit"]');

  const name = nameInput.value.trim();
  const amount = parseFloat(amountInput.value);
  const category = categoryInput.value;
  if (!name || isNaN(amount) || !category) return;

  if (submitButton.dataset.editing) {
    const id = submitButton.dataset.editing;
    await fetch('/expenses/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, amount, category }),
    });
    submitButton.textContent = 'Add';
    delete submitButton.dataset.editing;
  } else {
    await fetch('/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, amount, category }),
    });
  }

  nameInput.value = '';
  amountInput.value = '';
  categoryInput.value = '';
  fetchExpenses();
});

// Handle edit & delete buttons
document.getElementById('expenses-body').addEventListener('click', async function (e) {
  if (e.target.classList.contains('edit')) {
    const id = e.target.dataset.id;
    const name = e.target.dataset.name;
    const amount = e.target.dataset.amount;
    const category = e.target.dataset.category;

    document.getElementById('name').value = name;
    document.getElementById('amount').value = amount;
    document.getElementById('category').value = category;

    const submitButton = document.querySelector('#expense-form button[type="submit"]');
    submitButton.textContent = 'Update';
    submitButton.dataset.editing = id;
  } else if (e.target.classList.contains('delete')) {
    const id = e.target.dataset.id;
    await fetch('/expenses/' + id, { method: 'DELETE' });
    fetchExpenses();
  }
});

// Clear all
document.getElementById('clear-all').addEventListener('click', async () => {
  await fetch('/expenses', { method: 'DELETE' });
  fetchExpenses();
});

// Category filtering
document.getElementById('category-filter').addEventListener('change', function(e) {
  const selectedCategory = e.target.value;
  filterExpensesByCategory(selectedCategory);
});

document.getElementById('clear-filter').addEventListener('click', function() {
  document.getElementById('category-filter').value = '';
  filterExpensesByCategory('');
});

function filterExpensesByCategory(category) {
  const rows = document.querySelectorAll('#expenses-body tr');
  let visibleTotal = 0;
  
  rows.forEach(row => {
    if (row.children.length === 1) return; // Skip "No expenses" row
    
    const categoryCell = row.children[1];
    const amountCell = row.children[2];
    const categoryText = categoryCell.textContent.trim();
    
    if (!category || categoryText.includes(category)) {
      row.style.display = '';
      const amount = parseFloat(amountCell.textContent.replace('$', ''));
      visibleTotal += amount;
    } else {
      row.style.display = 'none';
    }
  });
  
  document.getElementById('total-amount').textContent = '$' + visibleTotal.toFixed(2);
}

// Initial load
fetchExpenses();
</script>
</body>
</html>
"""

# Database helper
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
        category = (data.get("category") or "Other").strip()
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid amount"}), 400
        if not name:
            return jsonify({"message": "Name required"}), 400
        cur.execute("INSERT INTO expenses (name, amount, category) VALUES (?, ?, ?)", (name, amount, category))
        conn.commit()
        return jsonify({"message": "Added"}), 201

    if request.method == "DELETE":
        cur.execute("DELETE FROM expenses")
        conn.commit()
        return jsonify({"message": "All cleared"}), 200

    # GET
    cur.execute("SELECT id, name, amount, category FROM expenses ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    total = sum(float(r["amount"]) for r in rows)
    return jsonify({"expenses": rows, "total": total})

@app.route("/expenses/<int:expense_id>", methods=["DELETE", "PUT"])
def modify_expense(expense_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "DELETE":
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({"message": "Deleted"}), 200

    if request.method == "PUT":
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        category = (data.get("category") or "Other").strip()
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid amount"}), 400
        if not name:
            return jsonify({"message": "Name required"}), 400
        cur.execute("UPDATE expenses SET name = ?, amount = ?, category = ? WHERE id = ?", (name, amount, category, expense_id))
        conn.commit()
        return jsonify({"message": "Updated"}), 200

if __name__ == "__main__":
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT DEFAULT 'Other',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Add category column to existing table if it doesn't exist
    try:
        conn.execute("ALTER TABLE expenses ADD COLUMN category TEXT DEFAULT 'Other'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()
    app.run(debug=True, host="0.0.0.0", port=5000)
