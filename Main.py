
from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, LoginManager, login_required, current_user, logout_user, login_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, RadioField, HiddenField, StringField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, Regexp, NumberRange
from datetime import date
import sqlite3

import os

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'TRYt0Br3akTh1saaaMLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)

# the name of the database; add path if necessary
db_name = 'database.db'

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

#Unsure if necessary
# app.register_blueprint(views, url_prefix='/')
# app.register_blueprint(auth, url_prefix='/')

login_manager = LoginManager()
login_manager.login_view = 'app.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class SPost(db.Model):
	# Defines the Table for sales postings
	__tablename__ = 'SPost'

	# Makes four columns into the table title, email, price, description
	_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), nullable=False)
	price = db.Column(db.Float, nullable=False)
	description = db.Column(db.String(1000), nullable=False)
	updated = db.Column(db.String)


	# A constructor function where we will pass the input information to a db
	def __init__(self, title, email, price, description, updated):
		self.title = title
		self.email = email
		self.price = price
		self.description = description
		self.updated = updated

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(25))


class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    title = StringField('Listing name', [ InputRequired(),
        Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid title name"),
        Length(min=3, max=35, message="Invalid title length")
        ])
    description = StringField('Description', [ InputRequired(),
        Regexp(r'^[a-zA-Z0-9_.,!\(\)\' ]+$', message="Invalid description"),
        Length(min=3, max=1000, message="Invalid description length")
        ])
    price = FloatField('Price', [ InputRequired(),
        NumberRange(min=0.01, max=9999.99, message="Invalid price range")
        ])
    email = StringField('Email address', [ InputRequired(),
        Regexp(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', message="Invalid email"),
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

'''
@app.route('/',  methods=['GET', 'POST'])
@login_required
def home():
    return render_template("MPHome.html", user=current_user)
'''
@app.route('/MPHome')
@login_required
def MPHome():
    # get a list of unique values in the style column
    titles = SPost.query.with_entities(SPost.title).distinct()
    return render_template('MPHome.html', titles=titles, user=current_user)

@app.route('/', methods=['GET', 'POST'])
def defaultHome():
    return render_template("defaultHome.html", user=current_user)



@app.route('/inventory/<title>')
@login_required
def inventory(title):
    cards = SPost.query.filter_by(title=title).order_by(SPost.title).all()
    return render_template('list.html', cards=cards, title=title)

#Add a new entry to the DB    
@app.route('/MPHome/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        title = request.form['title']
        email = request.form['email']
        price = request.form['price']
        description = request.form['description']
        
        #Capitalize first letter of each word for sorting later
        strList = title.split()
        newString = ''
        for val in strList:
            newString += val.capitalize()+ ' '
        title = newString
            
        # get today's date from function, above all the routes
        updated = stringdate()
        # the data to be inserted into card model - the table, card
        record = SPost(title, email, price, description, updated)
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        # create a message to send to the template
        message = f"The data for {title} has been submitted."
        return render_template('add_record.html', message=message, user=current_user)
    else:
        # show validaton errors
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('add_record.html', form1=form1, user=current_user)

# select a record to edit or delete
@app.route('/select_record/<letters>')
@login_required
def select_record(letters):
    # alphabetical lists by card name, chunked by letters between _ and _
    # .between() evaluates first letter of a string
    a, b = list(letters)
    cards = SPost.query.filter(SPost.title.between(a, b)).order_by(SPost.title).all()
    return render_template('select_record.html', cards=cards, user=current_user)
    
# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
@login_required
def edit_or_delete():
    _id = request.form['id']
    choice = request.form['choice']
    card = SPost.query.filter(SPost._id == _id).first()
    # two forms in this template
    form1 = AddRecord()
    form2 = DeleteForm()
    return render_template('edit_or_delete.html', card=card, form1=form1, form2=form2, choice=choice, user=current_user)

# result of delete - this function deletes the record
@app.route('/delete_result', methods=['POST'])
@login_required
def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']
    card = SPost.query.filter(SPost._id == id).first()
    if purpose == 'delete':
        db.session.delete(card)
        db.session.commit()
        message = f"The card {card.title} has been deleted from the database."
        return render_template('result.html', message=message, user=current_user)
    else:
        # this calls an error handler
        abort(405)
        
# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
@login_required
def edit_result():
    _id = request.form['id_field']
    # call up the record from the database
    card = SPost.query.filter(SPost._id == _id).first()
    # update all values
    card.title = request.form['title']
    card.email = request.form['email']
    card.description = request.form['description']
    card.price = request.form['price']
    # get today's date from function, above all the routes
    card.updated = stringdate()
    
    #Capitalize first letter of each word for sorting later
    strList = card.title.split()
    newString = ''
    for val in strList:
        newString += val.capitalize()+ ' '
    card.title = newString

    form1 = AddRecord()
    if form1.validate_on_submit():
        # update database record
        db.session.commit()
        # create a message to send to the template
        message = f"The data for card {card.title} has been updated."
        return render_template('result.html', message=message, user=current_user)
    else:
         # show validaton errors
        card._id = _id
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('edit_or_delete.html', form1=form1, card=card, choice='edit', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        

        user = User.query.filter_by(email=email).first()
        

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('MPHome'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
	first_nameCheck = User.query.filter_by(first_name=first_name).first()

        if user:
            flash('Email already exists.', category='error')
	elif first_nameCheck:
            flash('Username already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('MPHome'))

    return render_template("sign_up.html", user=current_user)

@app.route('/changePassword', methods=['GET', 'POST'])
@login_required
def changePassword():  
    if request.method == 'POST':
        user = current_user      
        oldPassword = user.password
        newPassword1 = request.form.get('password2')
        newPassword2 = request.form.get('password3')
        
        if newPassword1 == oldPassword:
            flash('Your new password must be different from your old password.', category='error')
        elif newPassword1 != newPassword2:
            flash('Passwords don\'t match.', category='error')
        elif len(newPassword1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            user.password = generate_password_hash(newPassword1, method='sha256')
            db.session.add(user)
            db.session.commit()
            flash('Password Updated!', category='success')
            return redirect(url_for('MPHome'))
    return render_template("changePW.html", user=current_user)
            

@app.route('/accountManagement', methods=['GET', 'POST'])
@login_required
def accountManagement(): 
        return render_template("accountM.html", user=current_user)
    
@app.route('/changeUsername', methods=['GET', 'POST'])
@login_required
def changeUsername():  
    if request.method == 'POST':
        user = current_user 
        oldUsername = user.first_name
        newUsername = request.form.get('firstName')
        newUsername1 = request.form.get('firstName1')
	newUsernameCheck = User.query.filter_by(first_name=newUsername).first()
	
        if newUsername == oldUsername:
            flash('Your new username must be different from your old username.', category='error')
        elif len(newUsername) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif newUsernameCheck:
            flash('Username already exists.', category='error')
        elif newUsername != newUsername1:
            flash('Usernames don\'t match.', category='error')
        else: 
            user.first_name = newUsername
            db.session.add(user)
            db.session.commit()
            flash('Username Updated!', category='success')
            return redirect(url_for('accountManagement'))
    return render_template("changeUsername.html", user=current_user)
        
@app.route('/deleteAccount', methods=['GET', 'POST'])
@login_required
def deleteAccount():
    if request.method == 'POST':
        user = current_user
        password = request.form.get('password1')
        
        if check_password_hash(user.password, password) == False:
            flash('Your password is incorrect.', category='error')
        else:
            flash('Account Deleted', category='success')
            db.session.delete(user) 
            db.session.commit()
            return redirect(url_for('logout'))
    return render_template("deleteAccount.html", user=current_user)

@app.route('/managerPage', methods=['GET', 'POST'])
@login_required
def managerPage():
    connection = sqlite3.connect("database.db")
    crsr = connection.cursor()
    cardCrsr = connection.cursor()
    crsr.execute("SELECT email, first_name FROM user")
    cardCrsr.execute("SELECT * FROM SPost")
    ans = crsr.fetchall()
    cardAns = cardCrsr.fetchall()
    length = len(ans)
    cardLength = len(cardAns)
    connection.close()
    return render_template("managerPage.html", user=current_user, ans=ans, length = length, cardAns=cardAns, cardLength=cardLength)
   
    
    
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
    db.create_all()
    app.run(debug=True)
