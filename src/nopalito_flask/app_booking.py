# import flask
from flask import Flask, render_template, url_for, redirect, request
import psycopg2
import time
import traceback

# create instance of web application
app = Flask(__name__)

#define routes for pages on website
#route to home page
@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')

#route to menu page
@app.route("/menu")
def menu():
    return render_template('menu.html')

#route to about page
@app.route("/about")
def about():
    return render_template('about.html')

#route to contact page
@app.route("/contact")
def contact():
    return render_template('contact.html')

def id_maker():
    conn = psycopg2.connect(database="Nopalito_DB_1",
                            user="postgres",
                            password="**n0pAlIt0",
                            host="nopalitodb.c9ezdaye8tbs.eu-north-1.rds.amazonaws.com",
                            port="5432")
        
    cur = conn.cursor()

    cur.execute("""SELECT MAX(BOOKING_ID) FROM nopalito_schema.bookings""")
    if cur.fetchall()[0][0]:
        id_value = cur.fetchall()[0][0] + 1

    else:
        id_value = 1
    cur.close()
    conn.close()
    
    return id_value



#route to booking page, allows for POST REST methods on the page
@app.route('/booking', methods = ["GET", "POST"])
def booking():
    if request.method == "POST":
        try:
            id = id_maker()
            conn = psycopg2.connect(database="Nopalito_DB_1",
                        user="postgres",
                        password="**n0pAlIt0",
                        host="nopalitodb.c9ezdaye8tbs.eu-north-1.rds.amazonaws.com",
                        port="5432")
            
            cur = conn.cursor()

            #Get data from the form
            first_name = request.form.get("fname")
            last_name = request.form.get("lname")
            phone = request.form.get("phone")
            email = request.form.get("email")
            guests = request.form.get("guests")
            booking_time = request.form.get("time")
            date = request.form.get("date")
            requirements = request.form.get("special_requests")

            #Check if there are available bookings for the selected time and date
            conn = psycopg2.connect(database="Nopalito_DB_1",
                        user="postgres",
                        password="**n0pAlIt0",
                        host="nopalitodb.c9ezdaye8tbs.eu-north-1.rds.amazonaws.com",
                        port="5432")
            cur = conn.cursor()

            booking_time = request.form.get("time")
            date = request.form.get("date")

            cur.execute("""SELECT COUNT(*) FROM nopalito_schema.bookings WHERE booking_time = %s AND booking_date = %s""", (booking_time, date))
            count_bookings = cur.fetchone()[0]

            if count_bookings >= 10:
                conn.close()
                return render_template('booking.html', error="Sorry, no bookings available at this time, please try another time.")

            # Find the lowest available table number (from 1 to 10)
            cur.execute("""SELECT table_number FROM nopalito_schema.bookings WHERE booking_time = %s AND booking_date = %s""", (booking_time, date))
            assigned_table_numbers = set(row[0] for row in cur.fetchall())
            available_table_numbers = set(range(1, 11)) - assigned_table_numbers
            table_number = min(available_table_numbers)
            

            cur.execute("""INSERT INTO nopalito_schema.bookings (booking_id, first_name, surname, phone_num, email, num_of_guests, booking_time, booking_date, requests, table_number) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (id, first_name, last_name, phone, email, guests, booking_time, date, requirements, table_number))

            conn.commit()
            return redirect(url_for('confirmation', booking_id = id))
        
        except psycopg2.Error as e:
            traceback.print_exc()
            # Handle psycopg2 database errors
            return render_template('booking.html', error="Database error occurred. Please try again later.")

        except Exception as e:
            traceback.print_exc()
            # Handle other unexpected exceptions
            return render_template('booking.html', error="An unexpected error occurred. Please try again later.")
        
        
    else:
        return render_template('booking.html')

@app.route('/confirmation/<int:booking_id>')
def confirmation(booking_id):
    conn = psycopg2.connect(database="Nopalito_DB_1",
                        user="postgres",
                        password="**n0pAlIt0",
                        host="nopalitodb.c9ezdaye8tbs.eu-north-1.rds.amazonaws.com",
                        port="5432")
    cur = conn.cursor()

    cur.execute("SELECT * FROM nopalito_schema.bookings WHERE booking_id = %s", (booking_id,))
    booking = cur.fetchone()

    if booking:
        # Extract the booking details
        booking_info = {
            "id": booking[0],
            "fname": booking[1],
            "lname": booking[2],
            "phone": booking[3],
            "email": booking[4],
            "guests": booking[7],
            "booking_time": booking[6],
            "date": booking[5],
            "requests": booking[9],
            "table_number": booking[8]
        }

        conn.close()
        return render_template('confirmation.html', booking=booking_info)
    else:
        conn.close()
        return "Booking not found."

#run the app
if __name__ == "__main__":
    app.run(debug = True)