from flask import Flask, render_template, request, redirect, url_for, Response
import json
import os

from scraper import get_item_value_sold_new

app = Flask(__name__)

# This is the file where where items are saved to and loaded from
DATA_FILE = "items.json"

# This list stores all our items while web app is running
items = []

# This function deals with loading items from the items.json file into the web app
def load_items():
    global items

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    items = data
                else:
                    items = []
        except (json.JSONDecodeError, OSError):
            items = []
    else:
        items = []

# This function deals with saving items to the items.json file from the web app
def save_items():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(items, f, indent=2)
    except OSError:
        pass

# Function for when someone goes to the home page
@app.route("/")
def home():
    return render_template("index.html", items=items)

# Function for when someone adds a new item
@app.route("/add", methods=["POST"])
def add_item():
    name = request.form.get("name", "").strip()
    quantity = request.form.get("quantity", "").strip()
    category = request.form.get("category", "").strip()
    condition = request.form.get("condition", "").strip()
    purchase_price = request.form.get("purchase_price", "").strip()
    
    # This is where the web scraping gets used
    scrape_result = get_item_value_sold_new(name)

    if scrape_result["error"] is None and scrape_result["count"] > 0:
        current_price = scrape_result["average_price"]
    else:
        current_price = 0.0

    print(f"[DEBUG] Estimated average price for '{name}': {current_price}")

    if name == "":
        return redirect(url_for("home"))
    
    # The following code converts entered values into their respective types
    try:
        qty_value = int(quantity)
    except ValueError:
        qty_value = 1

    try:
        purchase_value = float(purchase_price)
    except ValueError:
        purchase_value = 0.0

    try:
        current_value = float(current_price)
    except ValueError:
        current_value = 0.0

    profit_loss_total = qty_value * (current_value - purchase_value)

    # This stores the entered info into a dictionary (key-value pairs)
    item = {
        "name": name,
        "quantity": qty_value,
        "category": category,
        "condition": condition,
        "purchase_price": purchase_value,
        "current_price": current_value,
        "profit_loss_total": profit_loss_total,
    }

    # This adds the item to the list
    items.append(item)

    # This saves added item to json file
    save_items()

    return redirect(url_for("home"))

# Function for when someone clicks the delete button
@app.route("/delete/<int:item_index>", methods=["POST"])
def delete_item(item_index):
    if 0 <= item_index < len(items):
        del items[item_index]
        save_items()

    return redirect(url_for("home"))

# Function for when someone clicks the edit button
@app.route("/edit/<int:item_index>", methods=["GET", "POST"])
def edit_item(item_index):
    if not (0 <= item_index < len(items)):
        return redirect(url_for("home"))

    item = items[item_index]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()
        condition = request.form.get("condition", "").strip()
        purchase_price = request.form.get("purchase_price", "").strip()

        if name == "":
            return redirect(url_for("home"))

        try:
            qty_value = int(quantity)
        except ValueError:
            qty_value = 1

        try:
            purchase_value = float(purchase_price)
        except ValueError:
            purchase_value = 0.0

        scrape_result = get_item_value_sold_new(name)
        if scrape_result["error"] is None and scrape_result["count"] > 0:
            current_price = scrape_result["average_price"]
        else:
            current_price = 0.0

        try:
            current_value = float(current_price)
        except ValueError:
            current_value = 0.0

        profit_loss_total = qty_value * (current_value - purchase_value)

        item["name"] = name
        item["quantity"] = qty_value
        item["category"] = category
        item["condition"] = condition
        item["purchase_price"] = purchase_value
        item["current_price"] = current_value
        item["profit_loss_total"] = profit_loss_total

        save_items()

        return redirect(url_for("home"))

    # This shows the edit form when the edit button is clicked
    return render_template("edit.html", item=item, index=item_index)

# Function for when someone clicks the export button
@app.route("/export")
# This function exports all the inventory items into a CSV file
def export_csv():
    header = [
        "Item Name",
        "Quantity",
        "Category",
        "Condition",
        "Purchase Price (per item)",
        "Estimated Current Price (per item)",
        "Estimated Profit/Loss (TOTAL)",
    ]

    lines = [",".join(header)]

    for item in items:
        row = [
            str(item.get("name", "")),
            str(item.get("quantity", "")),
            str(item.get("category", "")),
            str(item.get("condition", "")),
            f"{item.get('purchase_price', 0.0):.2f}",
            f"{item.get('current_price', 0.0):.2f}",
            f"{item.get('profit_loss_total', 0.0):.2f}",
        ]
        lines.append(",".join(row))

    csv_data = "\n".join(lines)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"},
    )

# This loads items from json file before launching the server
if __name__ == "__main__":
    load_items()
    app.run(debug=True)