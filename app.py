from matplotlib.style import use
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import  SQLAlchemy
from flask_mail import Mail, Message
import json

LOCAL_SERVER = True


with open("config.json", 'r') as c:
    params = json.load(c)['params']

GREATER = 'Greater Than (>)'
SMALLER = 'Less Than (<)'
EQUAL = 'Equal To (=)'
DATA = [{'name':'Greater Than (>)'}, {'name':'Less Than (<)'}, {'name':'Equal To (=)'}]

app = Flask(__name__, template_folder="templates")
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params["gmail-user"]
app.config['MAIL_PASSWORD'] = params["gmail-password"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

if LOCAL_SERVER:  # If the server is Local Server which is true for this case
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]  # imported from config.json

db = SQLAlchemy(app)

class Stocks(db.Model):
    Email = db.Column(db.String(40), nullable=False)
    ReferencePrice = db.Column(db.String(12), nullable=False)
    UserChoice = db.Column(db.String(20), nullable=False)
    S_no = db.Column(db.Integer, primary_key=True)
    Ticker = db.Column(db.String(15), nullable=False)


def getStockPrice(url):
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}

    response = requests.get(url=url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    data_array = soup.find(id="responseDiv").getText().strip().split(":")

    for item in data_array:
        if 'lastPrice' in item:
            index = data_array.index(item)+1
            # print(index)s

    stock_price_raw = data_array[index]

    price = stock_price_raw.split('"')[1]

    # stock_price = ""
    # for i in price:
    #     if i == ",":
    #         continue
    #     else:
    #         stock_price += i
    # stock_price = float(stock_price)

    stock_price = float(price.replace(","  , ""))

    return stock_price

def sendMail(email_id, stock_ticker, stock_price, user_choice, reference_price):
    msg = Message(
                subject = "Mr Speculator Alert",
                sender = params["gmail-user"],
                recipients=[email_id]
            )
    data = f"{stock_ticker} price: ₹{stock_price} is {user_choice} given price: ₹{reference_price}"
    msg.body = data
    mail.send(msg)

def speculate(stock_list, stock_price):
    if stock_price > float(stock_list.ReferencePrice) and stock_list.UserChoice==GREATER:
        print("Pass")
        sendMail(stock_list.Email, stock_list.Ticker, stock_price, stock_list.UserChoice, stock_list.ReferencePrice)

    elif stock_price < float(stock_list.ReferencePrice) and stock_list.UserChoice==SMALLER: 
        print("Pass")
        sendMail(stock_list.Email, stock_list.Ticker, stock_price, stock_list.UserChoice, stock_list.ReferencePrice)
                        
    
    elif stock_price == float(stock_list.ReferencePrice) and stock_list.UserChoice==EQUAL:
        print("Pass")
        sendMail(stock_list.Email, stock_list.Ticker, stock_price, stock_list.UserChoice, stock_list.ReferencePrice)
            

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        stock_ticker = request.form['symbol'].upper()
        reference_price = request.form['reference-price']
        email_id = request.form['email']
        user_choice = request.form.get('user-choice')
        print(stock_ticker)
        print(reference_price)
        print(user_choice)

        url = f"https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={stock_ticker}"

        stock_price = getStockPrice(url)

        entry = Stocks(Email=email_id, ReferencePrice=reference_price, UserChoice=user_choice, Ticker=stock_ticker,)

        db.session.add(entry)
        db.session.commit()        

        
        stock_list = Stocks.query.all()   
        
        speculate(stock_list, stock_price)

        return render_template("index.html", data=DATA, stock_list=stock_list)

    stock_list = Stocks.query.all()
    return render_template("index.html", data=DATA, stock_list = stock_list)


@app.route("/delete/<string:S_no>")
def delete(S_no):
    stock_data = Stocks.query.filter_by(S_no=S_no).first()
    db.session.delete(stock_data)
    db.session.commit()
    return redirect("/")

app.run(debug=True)

# stock_ticker = "TATAMOTORS"
# url = f"https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={stock_ticker}"

# print(getStockPrice(url))
