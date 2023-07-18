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


#run the app
if __name__ == "__main__":
    app.run(debug = True)