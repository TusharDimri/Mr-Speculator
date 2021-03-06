from sched import scheduler
import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, redirect
from flask_sqlalchemy import  SQLAlchemy
from flask_mail import Mail, Message
import json
# from flask_apscheduler import APScheduler

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
# scheduler = APScheduler()

class Stocks(db.Model):
    Email = db.Column(db.String(40), nullable=False)
    ReferencePrice = db.Column(db.String(12), nullable=False)
    UserChoice = db.Column(db.String(20), nullable=False)
    S_no = db.Column(db.Integer, primary_key=True)
    Ticker = db.Column(db.String(15), nullable=False)


def getStockPrice(stock_ticker):
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    
    url = f"https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={stock_ticker}"


    response = requests.get(url=url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    data_array = soup.find(id="responseDiv").getText().strip().split(":")

    for item in data_array:
        if 'lastPrice' in item:
            index = data_array.index(item)+1
            # print(index)

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
    data = f"{stock_ticker} price: ???{stock_price} is {user_choice} given price: ???{reference_price}"
    msg.body = data
    mail.send(msg)
    print("Message Sent")

def deleteData(S_no):
    stock_data = Stocks.query.filter_by(S_no=S_no).first()
    db.session.delete(stock_data)
    db.session.commit()

def speculate():
    stock_list = Stocks.query.all()
    for stock in stock_list:
        ticker = stock.Ticker
        stock_price = getStockPrice(ticker)

        if stock_price > float(stock.ReferencePrice) and stock.UserChoice==GREATER:
            print("Pass")
            with app.app_context():
                sendMail(stock.Email, stock.Ticker, stock_price, stock.UserChoice, stock.ReferencePrice)
                deleteData(stock.S_no)



        elif stock_price < float(stock.ReferencePrice) and stock.UserChoice==SMALLER: 
            print("Pass")
            with app.app_context():
                sendMail(stock.Email, stock.Ticker, stock_price, stock.UserChoice, stock.ReferencePrice)
                deleteData(stock.S_no)
            
            
        elif stock_price == float(stock.ReferencePrice) and stock.UserChoice==EQUAL:
            print("Pass")
            with app.app_context():
                sendMail(stock.Email, stock.Ticker, stock_price, stock.UserChoice, stock.ReferencePrice)
                deleteData(stock.S_no)
            
        
            

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

        entry = Stocks(Email=email_id, ReferencePrice=reference_price, UserChoice=user_choice, Ticker=stock_ticker,)
        db.session.add(entry)
        db.session.commit()        
        
        # scheduler.resume() 
        # scheduler.add_job(func=speculate, trigger='interval', id=None, seconds=1)    
        speculate()

        return redirect("/")

    

    # scheduler.resume() 
    # scheduler.add_job(func=speculate, trigger='interval', id=None, seconds=1)   
    
    speculate()
    return render_template("index.html", data=DATA, stock_list =  Stocks.query.all())


@app.route("/delete/<string:S_no>")
def delete(S_no):
    # stock_data = Stocks.query.filter_by(S_no=S_no).first()
    # db.session.delete(stock_data)
    # db.session.commit()
    deleteData(S_no)
    return redirect("/")



# scheduler.start()  
app.run(debug=True)



# stock_ticker = "TATAMOTORS"
# url = f"https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={stock_ticker}"

# print(getStockPrice(url))
