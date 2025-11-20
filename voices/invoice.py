import tkinter as tk
from tkinter import messagebox
from fpdf import FPDF
from datetime import datetime

# --- Invoice PDF generator ---
def generate_invoice():
    recipient = recipient_entry.get()
    item = item_entry.get()
    amount = amount_entry.get()
    currency = currency_var.get()
    
    if not recipient or not item or not amount:
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.cell(200, 10, txt="Invoice", ln=True, align="C")
    pdf.ln(10)
    
    # Recipient
    pdf.cell(200, 10, txt=f"Recipient: {recipient}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.today().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(10)
    
    # Item
    pdf.cell(200, 10, txt="Item Description", ln=True)
    pdf.cell(200, 10, txt=f"{item} - {amount} {currency}", ln=True)
    
    # Save file
    filename = f"Invoice_{recipient.replace(' ', '_')}.pdf"
    pdf.output(filename)
    messagebox.showinfo("Success", f"Invoice saved as {filename}")

# --- Tkinter GUI ---
root = tk.Tk()
root.title("Invoice Generator")

tk.Label(root, text="Recipient Name").grid(row=0, column=0, padx=5, pady=5)
recipient_entry = tk.Entry(root, width=30)
recipient_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Item Description").grid(row=1, column=0, padx=5, pady=5)
item_entry = tk.Entry(root, width=30)
item_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Amount").grid(row=2, column=0, padx=5, pady=5)
amount_entry = tk.Entry(root, width=30)
amount_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Currency").grid(row=3, column=0, padx=5, pady=5)
currency_var = tk.StringVar(value="USD")
tk.OptionMenu(root, currency_var, "USD", "EUR", "BTC").grid(row=3, column=1, padx=5, pady=5)

tk.Button(root, text="Generate Invoice", command=generate_invoice).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
