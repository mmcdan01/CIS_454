
from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, RadioField, HiddenField, StringField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, Regexp, NumberRange
from datetime import date

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'TRYt0Br3akTh1saaaMLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)

# the name of the database; add path if necessary
db_name = 'Marketplace.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

class SPost(db.Model):
	# Defines the Table for sales postings
	__tablename__ = 'SPost'

	# Makes four columns into the table title, email, price, description
	_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), nullable=False)
	price = db.Column(db.Integer, nullable=False)
	description = db.Column(db.String(1000), nullable=False)
	updated = db.Column(db.String)


	# A constructor function where we will pass the input information to a db
	def __init__(self, title, email, price, description, updated):
		self.title = title
		self.email = email
		self.price = price
		self.description = description
		self.updated = updated
        
      
class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    title = StringField('Listing name', [ InputRequired(),
        Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid title name"),
        Length(min=3, max=25, message="Invalid title length")
        ])
    description = StringField('Description', [ InputRequired(),
        Regexp(r'^[A-Za-z\s\-\'\/]+$', message="Invalid description"),
        Length(min=3, max=1000, message="Invalid description length")
        ])
    price = FloatField('Price', [ InputRequired(),
        NumberRange(min=0.99, max=9999.99, message="Invalid price range")
        ])
    email = StringField('Email address', [ InputRequired(),
        Regexp(r'^[A-Za-z\s\-\'\/]+$', message="Invalid email"),
        Length(min=6, max=50, message="Invalid email length")
        ])
    # updated - date - handled in the route function
    updated = HiddenField()
    submit = SubmitField('Add/Update Record')

# small form
class DeleteForm(FlaskForm):
    id_field = HiddenField()
    purpose = HiddenField()
    submit = SubmitField('Delete This Card')

# +++++++++++++++++++++++
# get local date - does not account for time zone
# note: date was imported at top of script
def stringdate():
    today = date.today()
    date_list = str(today).split('-')
    # build string in format 01-01-2000
    date_string = date_list[1] + "-" + date_list[2] + "-" + date_list[0]
    return date_string

# +++++++++++++++++++++++
# routes

@app.route('/')
def index():
    # get a list of unique values in the style column
    titles = SPost.query.with_entities(SPost.title).distinct()
    return render_template('index.html', titles=titles)

@app.route('/inventory/<style>')
def inventory(title):
    cards = SPost.query.filter_by(title=title).order_by(SPost.title).all()
    return render_template('list.html', cards=cards, title=title)

#Add a new entry to the DB    
@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        title = request.form['title']
        email = request.form['email']
        price = request.form['price']
        description = request.form['description']
        # get today's date from function, above all the routes
        updated = stringdate()
        # the data to be inserted into Sock model - the table, socks
        record = SPost(title, email, price, description, updated)
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        # create a message to send to the template
        message = f"The data for {title} has been submitted."
        return render_template('add_record.html', message=message)
    else:
        # show validaton errors
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('add_record.html', form1=form1)

# select a record to edit or delete
@app.route('/select_record/<letters>')
def select_record(letters):
    # alphabetical lists by card name, chunked by letters between _ and _
    # .between() evaluates first letter of a string
    a, b = list(letters)
    cards = SPost.query.filter(SPost.title.between(a, b)).order_by(SPost.title).all()
    return render_template('select_record.html', cards=cards)
    
# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
def edit_or_delete():
    id = request.form['id']
    choice = request.form['choice']
    card = SPost.query.filter(SPost.id == id).first()
    # two forms in this template
    form1 = AddRecord()
    form2 = DeleteForm()
    return render_template('edit_or_delete.html', card=card, form1=form1, form2=form2, choice=choice)

# result of delete - this function deletes the record
@app.route('/delete_result', methods=['POST'])
def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']
    card = SPost.query.filter(SPost.id == id).first()
    if purpose == 'delete':
        db.session.delete(card)
        db.session.commit()
        message = f"The sock {card.title} has been deleted from the database."
        return render_template('result.html', message=message)
    else:
        # this calls an error handler
        abort(405)
        
# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
def edit_result():
    id = request.form['id_field']
    # call up the record from the database
    card = SPost.query.filter(SPost.id == id).first()
    # update all values
    card.title = request.form['title']
    card.email = request.form['email']
    card.description = request.form['description']
    card.price = request.form['price']
    # get today's date from function, above all the routes
    card.updated = stringdate()

    form1 = AddRecord()
    if form1.validate_on_submit():
        # update database record
        db.session.commit()
        # create a message to send to the template
        message = f"The data for card {card.title} has been updated."
        return render_template('result.html', message=message)
    else:
         # show validaton errors
        card.id = id
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('edit_or_delete.html', form1=form1, card=card, choice='edit')
    
# +++++++++++++++++++++++
# error routes

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', pagetitle="404 Error - Page Not Found", pageheading="Page not found (Error 404)", error=e), 404

@app.errorhandler(405)
def form_not_posted(e):
    return render_template('error.html', pagetitle="405 Error - Form Not Submitted", pageheading="The form was not submitted (Error 405)", error=e), 405

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', pagetitle="500 Error - Internal Server Error", pageheading="Internal server error (500)", error=e), 500

# +++++++++++++++++++++++

if __name__ == '__main__':
    app.run(debug=True)