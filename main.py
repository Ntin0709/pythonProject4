from flask import Flask, render_template, request, redirect, url_for,jsonify,send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os
import pdfkit
from flask import Flask, render_template, request, make_response
import sqlite3
from PyPDF2 import PdfWriter, PdfFileReader
from flask import make_response
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from zipfile import *
import datetime

app = Flask(__name__, static_url_path='/static')
items = []
next_sr_no = 1  # Track the next Sr No. to assign
@app.route('/get-partynames', methods=['GET'])
def fetch_party_names():
    try:
        # Establish a connection to the database
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT party_name FROM parties')
        parties = cursor.fetchall()
        print(parties)
        # Convert the result to a list of dictionaries
        party_names = [{'name': party[0]} for party in parties]
        return jsonify(party_names)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Home route
@app.route('/create-bill')
def billing_page():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        party_name = request.form.get('partyName')

        # Generate the next bill number
        cursor.execute('SELECT MAX(id) FROM bills')
        last_id = cursor.fetchone()[0]
        if last_id is not None:
            next_bill_no = str(last_id + 1)
        else:
            next_bill_no = '1'

        # Save the bill details to the database
        cursor.execute('INSERT INTO bills (bill_no, party_name) VALUES (?, ?)', (next_bill_no, party_name))
        conn.commit()

        # Redirect to the billing page or show a success message

    # Retrieve party names from the database
    cursor.execute('SELECT DISTINCT party_name FROM parties')
    parties = cursor.fetchall()
    print(parties)
    return render_template('bill.html', parties=parties)
@app.route('/mark-paid/<bill_no>', methods=['POST'])
def mark_paid(bill_no):
    # Retrieve the bill details from the database
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bills WHERE bill_no = ?", (bill_no,))
    bill = cursor.fetchone()

    if bill:
        # Update the remaining amount to 0
        cursor.execute("UPDATE bills SET remaining_amount = 0 WHERE bill_no = ?", (bill_no,))

        # Update the paid status to 1 (assuming 1 represents "paid")
        cursor.execute("UPDATE bills SET paid_status = 1 WHERE bill_no = ?", (bill_no,))

        # Update the paid date to the current date
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("UPDATE bills SET paid_date = ? WHERE bill_no = ?", (current_date, bill_no))

        conn.commit()

    conn.close()

    # Redirect back to the party bills page
    return redirect('/party-bills/' + bill[1])

    # Redirect back to the party bills page
    return redirect('/party-bills/' + bill['party_name'])
@app.route('/main')
def main_page():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    cursor.execute('''SELECT parties.party_name, SUM(bills.remaining_amount) AS total_amount
                  FROM parties
                  LEFT JOIN bills ON parties.party_name = bills.party_name
                  GROUP BY parties.party_name''')
    parties = cursor.fetchall()

    party_list = []

    for party in parties:
        party_name, total_amount = party
        party_list.append({'party_name': party_name, 'total_amount': total_amount})

    conn.close()

    return render_template('main_page.html', parties=party_list)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Perform authentication logic here
        # Check username and password against your user database

        if username == 'admin' and password == 'password':
            # Authentication successful
            # Set a session cookie or perform any other required actions

            # Redirect to the main page after successful login
            return redirect(url_for('main_page'))
        else:
            # Authentication failed
            return render_template('index.html', error='Invalid username or password')

    return render_template('index.html')


@app.route('/save-bill', methods=['POST'])
def save_bill():
    data = request.get_json()
    conn = sqlite3.connect('your_database.db')
    c = conn.cursor()
    # Validate the received JSON data here if needed

    party_id = data['partyId']
    party_name = data['partyName']
    bill_no = data['billNo']
    items = data['items']
    total_amount=data['total_amount']
    # Insert the party name and bill number into the database
    c.execute("INSERT INTO bills (party_name, bill_no,total_amount,remaining_amount) VALUES (?, ?,?,?)", (party_name, bill_no,total_amount,total_amount))
    conn.commit()

    # Get the inserted row id
    bill_id = c.lastrowid
    # total_amount = 0 

    # Insert the table items into the database with the party_id and bill_id as foreign keys
    for item in items:
        sr_no = item['srNo']
        item_name = item['item']
        description_image = item['descriptionImage']
        description_text = item['descriptionText']
        meters = item['meters']
        rate = item['rate']
        total = item['total']
        # total_amount += float(total)
        c.execute("INSERT INTO items (bill_id, sr_no, item_name, description_image, description_text, meters, rate, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (bill_id, sr_no, item_name, description_image, description_text, meters, rate, total))
        conn.commit()

    # Update the totalamount in the parties table
    # c.execute("UPDATE parties SET totalamount = totalamount + ? WHERE id = ?", (total, party_id))
    # conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

def fetch_party_data():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Example query to fetch party data
    cursor.execute("SELECT party_name FROM parties")
    parties = [{'party_name': row[0]} for row in cursor.fetchall()]

    conn.close()
    return parties


def fetch_total_amount(party_name):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Query to fetch total remaining amount for a party
    cursor.execute("SELECT total_amount FROM parties WHERE party_name=?", (party_name,))
    total_amount = cursor.fetchone()[0]

    conn.close()
    return total_amount
def fetch_bill_data(party_name):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    print(party_name)
    # Example query to fetch bill data for a specific party with total amount, remaining amount, and paid status
    cursor.execute("SELECT * FROM bills WHERE party_name = ?", (party_name,))
    bills = []
    # print(cursor.fetchall())
    for row in cursor.fetchall():
        print("inside")
        print(row)
        bill = {
            'bill_no': row[2],
            'total_amount': row[3],
            'remaining_amount': row[4],
            'paid_status': row[5],
            'paid_date': row[6]
        }
        bills.append(bill)

    conn.close()
    return bills

def fetch_bill_details(bill_id):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Example query to fetch bill details for a specific bill ID
    cursor.execute("SELECT * FROM items WHERE bill_id=?", (bill_id,))
    items = cursor.fetchall()

    bill_details = {'bill_id': bill_id, 'items': []}

    for item in items:
        item_id, _, sr_no, item_name, description_image, description_text, meters, rate, total, _ = item
        bill_details['items'].append({
            'sr_no': sr_no,
            'item_name': item_name,
            'description_image': description_image,
            'description_text': description_text,
            'meters': meters,
            'rate': rate,
            'total': total
        })

    conn.close()
    return bill_details


def fetch_items(bill_id):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Example query to fetch items associated with a specific bill ID
    cursor.execute("SELECT item_name, meters, rate, total FROM items WHERE bill_id=?", (bill_id,))
    items = [{'item_name': row[0], 'meters': row[1], 'rate': row[2], 'total': row[3]} for row in cursor.fetchall()]

    conn.close()
    return items


@app.route('/party-bills/<party_name>')
def party_bills(party_name):
    # Fetch bill data and total remaining amount for the specified party from the database
    # Replace 'fetch_bill_data' and 'fetch_total_amount' with your actual database query functions
    bills = fetch_bill_data(party_name)
    # total_amount = fetch_total_amount(party_name)

    return render_template('party_bills.html', party_name=party_name, bills=bills)
@app.route('/bill-details/<bill_id>')
def bill_details(bill_id):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Fetch the bill details
    cursor.execute("SELECT * FROM bills WHERE id=?", (bill_id,))
    bill = cursor.fetchone()

    # Fetch the items associated with the bill
    cursor.execute("SELECT sr_no, item_name, meters, rate, total FROM items WHERE bill_id=?", (bill_id,))
    items = [{'sr_no': row[0], 'item_name': row[1], 'meters': row[2], 'rate': row[3], 'total': row[4]} for row in cursor.fetchall()]

    conn.close()

    return render_template('bill_details.html', bill=bill, items=items)
@app.route('/add-party', methods=['GET', 'POST'])
def add_party():
    if request.method == 'POST':
        # Get the party name and total amount from the form
        party_name = request.form['party_name']
        # total_amount = float(0)

        # Connect to the SQLite database
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Insert the party into the "parties" table
        cursor.execute("INSERT INTO parties (party_name) VALUES (?)", (party_name,))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return redirect('/main')  # Redirect to the main page after adding the party

    return render_template('add_party.html')
from pdf2image import convert_from_path

def pdf_to_image(pdf_file_path):
    # Convert the PDF into a list of PIL images
    file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
    images = convert_from_path(pdf_file_path)

    # Save each image as a separate file
    image_paths = []
    for i, image in enumerate(images):
        image_path = f'static/bills/{file_name}.png'  # Adjust the destination folder and file format as needed
        image.save(image_path, 'PNG')
        image_paths.append(image_path)

    return image_paths
import os

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json

    print(data)
    tableData = data['items']
    billNumber = data['billNo']
    partyName = data['partyName']
    logoPath = "static/images/logo_1-removebg.png"
    companyName = "Nandanam Fabrics"
    companyAddress = "Ground floor, 18-D, Canopus Mall, Ghoddod Road, Surat - 395007, +918460281282"
    finalTotal = sum(float(row['total']) for row in tableData)

    # Calculate the total width required for the table columns
    table_width = 30 + 40 + 70 + 70 + 30 + 30 + 30  # Adjust the widths as required

    # Set the desired page size based on the table width
    page_width = table_width + 20  # Add some padding
    page_height = 297  # A4 page height (adjust if necessary)

    # Generate PDF using FPDF library with the desired page size
    pdf = FPDF(format=(page_width, page_height))
    pdf.add_page()

    # Load and resize the design images
    for row in tableData:
        designImagePath = os.path.join("static/images/", row['descriptionImage'] + ".jpg")
        if os.path.isfile(designImagePath):
            row['descriptionImage'] = designImagePath
        else:
            row['descriptionImage'] = ""  # Set empty string if image file doesn't exist

    # Set logo and company name/address
    pdf.set_xy(10, 10)
    pdf.image(logoPath, x=pdf.get_x(), y=pdf.get_y(), w=50)
    pdf.set_xy(70, 10)
    pdf.set_font('Arial', 'B', 12)
    pdf.multi_cell(0, 10, companyName)
    pdf.set_xy(70, 17)
    pdf.multi_cell(0, 10, companyAddress)
    pdf.ln(20)

    # Add bill number and party name
    pdf.set_font('Arial', 'B', 12)
    pdf.multi_cell(0, 10, f'Bill Number: {billNumber}')
    pdf.multi_cell(0, 10, f'Party Name: {partyName}')
    pdf.ln(10)

    # Add table header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(30, 30, 'Sr No', 1)
    pdf.cell(40, 30, 'Item', 1)
    pdf.cell(70, 30, 'Description', 1)
    pdf.cell(70, 30, 'Design', 1)  # Adjusted the width to accommodate the image
    pdf.cell(30, 30, 'Meters', 1)
    pdf.cell(30, 30, 'Rate', 1)
    pdf.cell(30, 30, 'Total Amount', 1)
    pdf.ln()

    # Add table data
    pdf.set_font('Arial', '', 12)
    for row in tableData:
        pdf.cell(30, 30, str(row['srNo']), 1)
        pdf.cell(40, 30, str(row['item']), 1)
        pdf.cell(70, 30, row['descriptionText'], 1)
        if row['descriptionImage']:
            pdf.image(row['descriptionImage'], x=pdf.get_x() + 1, y=pdf.get_y() + 1, w=68, h=28)  # Adjusted the image position and dimensions
            pdf.set_xy(pdf.get_x() + 70, pdf.get_y())
        else:
            pdf.cell(70, 30, '', 1)# Add empty cell if image doesn't exist
              # Move the cursor to the right of the image
        pdf.cell(30, 30, row['meters'], 1)
        pdf.cell(30, 30, row['rate'], 1)
        pdf.cell(30, 30, row['total'], 1)
        pdf.ln()

    # Add final total
    pdf.cell(table_width - 30, 10, 'Final Total:', 1, 0, 'R')  # Adjusted the cell width
    pdf.cell(30, 10, str(finalTotal), 1, 0, 'R')
    pdf.ln()

    # Save the PDF file
    pdf_file_path = f'static/bills/{billNumber}.pdf'
    pdf.output(pdf_file_path)
    
    pdf_file_path=pdf_to_image(pdf_file_path)
    print(pdf_file_path)
    return {'imagePaths': pdf_file_path}





if __name__ == '__main__':
    app.run(debug=True)
