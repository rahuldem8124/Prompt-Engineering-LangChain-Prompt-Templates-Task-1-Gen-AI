from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 80, "AcmeCorp Retail - Customer Support Knowledge Base")
    
    # Sections
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "1. Return Policy")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 140, "Items can be returned within 30 days of purchase with a valid receipt.")
    c.drawString(70, height - 160, "Electronic items have a 14-day return window. Opened software cannot be returned.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 200, "2. Shipping Times")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 220, "Standard shipping takes 3-5 business days. Expedited shipping takes 1-2 business days.")
    c.drawString(70, height - 240, "International shipping can take up to 3 weeks depending on the destination.")
    
    c.save()
    print(f"Created {filename} successfully.")

if __name__ == "__main__":
    create_pdf("knowledge_base.pdf")
