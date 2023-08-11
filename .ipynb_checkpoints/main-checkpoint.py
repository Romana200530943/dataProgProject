from flask import Flask, render_template, request, jsonify
from currency_database import CurrencyDatabase
from pymongo import MongoClient
import requests
import schedule
import time
from datetime import datetime, timedelta
import threading

app = Flask(__name__)


# Define the URL from which you want to load data
BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1"
DATA_URL = f"{BASE_URL}/latest/currencies/cad.json"
# MongoDB connection settings
MONGO_URI = "mongodb+srv://200530943:c57VPOOpTo7aWE6v@cluster0.tmbqcxg.mongodb.net/"
DB_NAME = "project_currencies"
COLLECTION_NAME = "currencies"


@app.route('/')
def index():
    db = CurrencyDatabase(MONGO_URI, DB_NAME, COLLECTION_NAME)
    try:
        specific_date_1 = "2023-08-07"
        specific_date_2 = "2023-07-07"
        currency_code = "cad"

        specific_data_1 = db.get_data_by_date(specific_date_1)
        specific_data_2 = db.get_data_by_date(specific_date_2)

        print("Specific Data 1:", specific_data_1)
        print("Specific Data 2:", specific_data_2)

        if specific_data_1 and currency_code in specific_data_1:
            currency_data_1 = specific_data_1[currency_code]
        else:
            currency_data_1 = {}

        if specific_data_2 and currency_code in specific_data_2:
            currency_data_2 = specific_data_2[currency_code]
        else:
            currency_data_2 = {}

        rate_differences = {}
        for currency, rate_1 in currency_data_1.items():
            if currency in currency_data_2:
                rate_2 = currency_data_2[currency]
                difference = abs(rate_1 - rate_2)
                rate_differences[currency] = difference

        top_currencies = sorted(rate_differences.items(), key=lambda x: x[1], reverse=True)[:10]
        top_currency_data_1 = {currency: currency_data_1[currency] for currency, _ in top_currencies}
        top_currency_data_2 = {currency: currency_data_2[currency] for currency, _ in top_currencies}

        zipped_data_top = zip(
            top_currency_data_1.keys(),
            top_currency_data_1.values(),
            top_currency_data_2.values()
        )

        zipped_data_unsorted = zip(
            currency_data_1.keys(),
            currency_data_1.values(),
            currency_data_2.values()
        )

    finally:
        db.close_connection()

    return render_template('index.html', zipped_data_top=zipped_data_top, zipped_data_unsorted=zipped_data_unsorted,
                           specific_date_1=specific_date_1, specific_date_2=specific_date_2) 


    
@app.route('/getAll')
def get_all_data():
    try:
        db = CurrencyDatabase(MONGO_URI, DB_NAME, COLLECTION_NAME)
        all_data = db.get_all_data(limit=10)

        # Convert the ObjectId to string for each document
        formatted_data = []
        for data in all_data:
            data["_id"] = str(data["_id"])
            formatted_data.append(data)
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({"error": str(e)})
        

@app.route('/getForDate')
def get_data_for_date():
    try:
        db = CurrencyDatabase(MONGO_URI, DB_NAME, COLLECTION_NAME)
        date = request.args.get("date")

        data = db.get_data_by_date(date)

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/getRange')
def get_data_range():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        db = CurrencyDatabase(MONGO_URI, DB_NAME, COLLECTION_NAME)

        if not start_date or not end_date:
            return jsonify({"error": "Both start_date and end_date parameters are required."})

        cursor = db.get_data_between_dates(start_date, end_date)
        data = list(cursor)  # Convert the cursor to a list

        # Convert ObjectId to string for each document
        formatted_data = []
        for item in data:
            item["_id"] = str(item["_id"])
            formatted_data.append(item)

        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({"error": str(e)})
    

def scheduler_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)


def load_data(url):
    try:       
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            timestamp = datetime.now()

            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            
            collection.insert_one(json_data)
            print("Data loaded and saved to MongoDB for date:", timestamp)

            client.close()  # Close MongoDB connection
        else:
            print("Failed to load data. Status code:", response.status_code)
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
     # Load data immediately (for the first run)
    today = datetime.now().date()
    load_data(DATA_URL)

    # Schedule data loading every day
    schedule.every().day.at("00:00").do(lambda: load_data(DATA_URL))

    # Fetch data for every day over the past 2 months
    for i in range(60):  # Fetch data for 30 days
        date_n_days_ago = today - timedelta(days=i)
        formatted_date = date_n_days_ago.strftime("%Y-%m-%d")
        past_data_url = f"{BASE_URL}/{formatted_date}/currencies/cad.json"
        load_data(past_data_url)
        print(f"Loaded data for {formatted_date}")

    scheduler_thread = threading.Thread(target=scheduler_thread)
    scheduler_thread.start()

    app.run()  # Start the Flask app






