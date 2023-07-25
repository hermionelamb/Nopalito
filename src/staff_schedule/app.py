# pip intall flask
# pip install psycopg2
# pip install flask flask_sqlalchemy flask_login flask_bcrypt flask_wtf wtforms email_validator

from flask import Flask, render_template, redirect, url_for, request, session
import psycopg2
from datetime import date, timedelta
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
#bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'thisisasecretkey'


DB_HOST = 'localhost'
DB_NAME = 'Staff_Schedule'
DB_USER = 'postgres'
# PUT PASSWORD IN
DB_PASSWORD = ''

# Establish the connection to the PostgreSQL database
connection = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

def add_timedelta(date, days):
    return date + timedelta(days=days)

app.jinja_env.filters['add_timedelta'] = add_timedelta


@app.route('/')
def homepage():
    return render_template('homepage.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        password = request.form['password']

        # Check if the provided credentials exist in the database
        cursor = connection.cursor()

        query = "SELECT staff_id, first_name, surname FROM \"Staff_Schedule\".\"Login Details\" WHERE uname = %s AND password = %s;"
        cursor.execute(query, (uname, password))
        user = cursor.fetchone()

        cursor.close()

        if user:
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            session['surname'] = user[2]

            if uname == 'admin' and password == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('dashboard'))

        else:
            return render_template('login.html', error='Invalid username or password.')

    return render_template('login.html', error=None)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        # Retrieve user data from the session
        staff_id = session['user_id']
        first_name = session['first_name']
        surname = session['surname']

        return render_template('dashboard.html', first_name=first_name, surname=surname)
    else:
        return redirect(url_for('login'))


@app.route('/request_t_o', methods=['GET', 'POST'])
def request_t_o():
    if 'user_id' in session:
        staff_id = session['user_id']
        first_name = session['first_name']
        surname = session['surname']

        if request.method == 'POST':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            reason = request.form['reason']

            cursor = connection.cursor()

            insert_query = "INSERT INTO \"Staff_Schedule\".\"Time Off\" (staff_id, start_date, end_date, reason) VALUES (%s, %s, %s, %s);"
            cursor.execute(insert_query, (staff_id, start_date, end_date, reason))
            connection.commit()

            cursor.close()

            return redirect(url_for('dashboard'))

        # If the request method is GET, render the template with the form
        return render_template('request_t_o.html', first_name=first_name, surname=surname, staff_id=staff_id)

    return redirect(url_for('login'))


@app.route('/admin_page')
def admin_page():
    if 'user_id' in session:
        return render_template('admin_page.html')
    else:
        return redirect(url_for('login'))



@app.route('/requests')
def requests():
    if 'user_id' in session:
        # Fetch all unresolved time-off requests (where 'approved' is null)
        cursor = connection.cursor()

        select_query = "SELECT staff_id, start_date, end_date, reason, request_id FROM \"Staff_Schedule\".\"Time Off\" WHERE approved IS NULL;"
        cursor.execute(select_query)
        unresolved_requests = cursor.fetchall()

        # Fetch all resolved time-off requests (where 'approved' is not null)
        resolved_query = "SELECT staff_id, start_date, end_date, reason, approved, request_id FROM \"Staff_Schedule\".\"Time Off\" WHERE approved IS NOT NULL;"
        cursor.execute(resolved_query)
        resolved_requests = cursor.fetchall()

        cursor.close()

        return render_template('requests.html', unresolved_requests=unresolved_requests, resolved_requests=resolved_requests)

    return redirect(url_for('login'))


@app.route('/process_request/<int:request_id>/<status>', methods=['POST'])
def process_request(request_id, status):
    if 'user_id' in session:

        cursor = connection.cursor()

        if status == 'approve':
            update_query = "UPDATE \"Staff_Schedule\".\"Time Off\" SET approved = TRUE WHERE request_id = %s;"
        else:
            update_query = "UPDATE \"Staff_Schedule\".\"Time Off\" SET approved = FALSE WHERE request_id = %s;"

        cursor.execute(update_query, (request_id,))
        connection.commit()

        cursor.close()

        return redirect(url_for('requests'))

    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        surname = request.form['surname']
        uname = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        cursor = connection.cursor()

        query = "SELECT staff_id FROM \"Staff_Schedule\".\"Login Details\" WHERE uname = %s;"
        cursor.execute(query, (uname,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            return render_template('register.html', error='Username already exists.')

        # If the username is unique, add the new user to the database
        insert_query = "INSERT INTO \"Staff_Schedule\".\"Login Details\" (first_name, surname, uname, password) VALUES (%s, %s, %s, %s);"
        cursor.execute(insert_query, (first_name, surname, uname, password))
        connection.commit()

        cursor.close()

        # Redirect the user to the login page after successful registration.
        return redirect(url_for('login'))

    return render_template('register.html', error=None)



@app.route('/timetable')
def timetable():
    cursor = connection.cursor()
    cursor.execute('SELECT staff_id, first_name, surname, upper(first_name || \' \' || surname) AS NAME, ' \
                    'job, start_date, end_date, wage ' \
                    'FROM "Staff_Schedule"."Staff" ' \
                    'WHERE end_date IS NULL')
    staff_data = cursor.fetchall()

    # Retrieve data from the Shifts table
    cursor.execute('SELECT * FROM "Staff_Schedule"."Shifts"')
    shifts_data = cursor.fetchall()

    cursor.close()

    # Create a timetable data structure to store shift information
    timetable_data = {}
    for shift_data in shifts_data:
        start_time_day, end_time_day, staff_id, job = shift_data
        if staff_id not in timetable_data:
            timetable_data[staff_id] = []
        timetable_data[staff_id].append({
            'start_time_day': start_time_day,
            'end_time_day': end_time_day
        })

    # Sort shifts for each staff by start_time_day
    for staff_id in timetable_data:
        timetable_data[staff_id].sort(key=lambda x: x['start_time_day'])

    # Get the dates of the first day of the week for each column
    # and convert them to datetime.date objects
    column_dates = [date(2023, 7, 24) + timedelta(days=i) for i in range(7)]

    return render_template('timetable.html', staff_data=staff_data, timetable_data=timetable_data, column_dates=column_dates)

if __name__ == '__main__':
    app.run(debug=True)
