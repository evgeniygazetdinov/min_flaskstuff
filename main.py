from flask import Flask,jsonify
import random
from flask_sqlalchemy import SQLAlchemy  # 1

app = Flask(__name__)
app.config['SECRET_KEY'] = "xxxxxxxx"    # 2

db = SQLAlchemy(app)

# our database uri
username = "my_super_user"
password = "12345"
dbname = "my_test_data_base"
"postgres://YourUserName:YourPassword@YourHostname:5432/YourDatabaseName"
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{username}:{password}@localhost:5432/{dbname}"


def generate_name():
    first_names=('John','Andy','Joe','Don','Sam')
    last_names=('Johnson','Smith','Williams','Soer','Jons') 
    return "{} {}".format(random.choice(first_names), random.choice(last_names)) 

def generate_email_by_name(name):
    places = ['@gmail.com','@yahoo.com','@mail.ru','@yandex.ru']
    return '{}{}'.format(name,random.choice(places))

def generate_password():
    return '1234567'

def generate_data():
    name = generate_name()
    return {'name': name, 'password':generate_password(), 'email': generate_email_by_name(name)}

def fill_one_row(data):
    db.session.execute("""insert into accounts (username,password,email)
         values('{}','{}','{}');""".format(data['name'], data['password'], data['email']))


def fill_table():
    for _ in range(5):
        data = generate_data()
        fill_one_row(data)
     
def create_table_with_cred():
    db.session.execute('''CREATE TABLE if not exists accounts (
    user_id serial PRIMARY KEY,
    username VARCHAR ( 50 ) NOT NULL,
    password VARCHAR ( 50 ) NOT NULL,
    email VARCHAR ( 255 )  NOT NULL);''')    

@app.route('/')
def main_result():
    create_table_with_cred()
    fill_table()
    result = db.session.execute('SELECT * FROM accounts limit {};'.format(5))
    res_data = result.cursor.fetchall()
    data = [{'id':r[0],'name': r[1],'email': r[-1]} for r in res_data]
    return jsonify({'res':data})

if __name__ == "__main__":
    app.run()
