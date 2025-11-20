from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from reportlab.lib.utils import ImageReader
from datetime import date
import qrcode
import io

def generate_qr_code(data: str):
    """Generate a QR code and return it as an in-memory image."""
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    byte_stream = io.BytesIO()
    img.save(byte_stream, format='PNG')
    byte_stream.seek(0)
    return ImageReader(byte_stream)

def generate_invoice(invoice_number, customer_name, items, output="invoice.pdf"):
    c = canvas.Canvas(output, pagesize=LETTER)
    width, height = LETTER

    # -------------------------
    # Header
    # -------------------------
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Invoice #: {invoice_number}")
    c.drawString(50, height - 100, f"Date: {date.today().isoformat()}")
    c.drawString(50, height - 120, f"Bill To: {customer_name}")

    # -------------------------
    # Table
    # -------------------------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 170, "Description")
    c.drawString(300, height - 170, "Qty")
    c.drawString(350, height - 170, "Price")
    c.drawString(420, height - 170, "Total")

    y = height - 190
    c.setFont("Helvetica", 12)

    grand_total = 0

    for item in items:
        total = item["qty"] * item["price"]
        grand_total += total

        c.drawString(50, y, item["desc"])
        c.drawString(300, y, str(item["qty"]))
        c.drawString(350, y, f"${item['price']:.2f}")
        c.drawString(420, y, f"${total:.2f}")

        y -= 20

    # -------------------------
    # Total
    # -------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y - 20, f"Grand Total: ${grand_total:.2f}")

    # -------------------------
    # Payment Instructions Block
    # -------------------------
    pay_y = y - 80
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, pay_y, "Payment Instructions:")

    c.setFont("Helvetica", 12)
    pay_y -= 20

    payment_lines = [
        "Zelle: william@email.com",
        "Cash App: $WillyP",
        "PayPal: https://paypal.me/Willy",
        "Venmo: @WillyP",
        "Stripe: https://buy.stripe.com/randomlink",
        "Bank (ACH): Chase Bank, Routing: 123456789, Account: ****1234",
        "Bitcoin (BTC): bc1qxyz123abc456",
    ]

    for line in payment_lines:
        c.drawString(50, pay_y, line)
        pay_y -= 16

    # -------------------------
    # QR Code (BTC in this example)
    # -------------------------
    qr_data = "bc1qxyz123abc456"  # mocked-up BTC address
    qr_img = generate_qr_code(qr_data)
    c.drawImage(qr_img, 400, pay_y, width=120, height=120)

    c.setFont("Helvetica", 10)
    c.drawString(400, pay_y - 12, "Scan to Pay (BTC)")

    # -------------------------
    # Save PDF
    # -------------------------
    c.save()
    print(f"Saved invoice to {output}")


# -------------------------------------------------------
# Example Usage (you replace details later)
# -------------------------------------------------------
if __name__ == "__main__":
    items = [
        {"desc": "Logo Design", "qty": 1, "price": 300},
        {"desc": "Business Cards", "qty": 500, "price": 0.15},
    ]

    generate_invoice(
        invoice_number="INV-1001",
        customer_name="John Doe",
        items=items,
        output="invoice-1001.pdf"
    )
