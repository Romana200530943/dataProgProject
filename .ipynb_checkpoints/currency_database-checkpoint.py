from pymongo import MongoClient
from bson import ObjectId

class CurrencyDatabase:
    def __init__(self, uri, db_name, collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
    
    def get_data_by_date(self, date):
        query = {"date": date}
        data = self.collection.find_one(query)
        if data:
            data["_id"] = str(data["_id"])  # Convert ObjectId to string
        return data
        
    def get_all_data(self, limit=None):
        query_result = self.collection.find().limit(limit) if limit else self.collection.find()

        formatted_data = []
        for data in query_result:
            data["_id"] = str(data["_id"])
            formatted_data.append(data)

        return formatted_data

        
    def get_data_between_dates(self, start_date, end_date):
        query = {"date": {"$gte": start_date, "$lte": end_date}}
        return self.collection.find(query)
        
    def close_connection(self):
        self.client.close()
