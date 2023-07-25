# import flask
from flask import Flask, redirect, url_for, render_template

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

@app.route('/booking', methods=['GET', 'POST'])
def reservation_form():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        party_size = request.form['party_size']
        date = request.form['date']
        time = request.form['time']
        special_requests = request.form['special_requests']

        # You can add further processing here (e.g., save to a database)

        # Prepare the data dictionary
        reservation_data = {
            'Name': name,
            'Email': email,
            'Phone': phone,
            'Party Size': party_size,
            'Date': date,
            'Time': time,
            'Special Requests': special_requests
        }

        # Write data to CSV file
        write_to_csv(reservation_data)

        # Render a confirmation page with the provided information
        return render_template('confirmation.html', reservation_data=reservation_data)

    # Render the reservation form
    return render_template('reservation_form.html')

#run the app
if __name__ == "__main__":
    app.run(debug = True)
