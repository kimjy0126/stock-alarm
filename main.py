
import time
from stock import Stock

#tickers = ["000660", "035420", "001465", "005930", "035720", "036090", "001465"]

def get_alert_condition_from_file(filename):
    stocks = []

    f = open(filename, "r")
    lines = f.readlines()
    for line in lines:
        ticker, conditions = map(lambda x: x.strip(), line.split("/"))
        conditions = conditions.split(" ")
        
        stock = Stock(ticker, conditions)
        
        stocks.append(stock)
    
    return stocks


stocks = get_alert_condition_from_file("condition.txt")

while True:
    for stock in stocks:
        stock.get_stock_info()
        satisfied_condition = stock.check_alert_condition()
        if satisfied_condition:
            stock.alert(satisfied_condition)

    time.sleep(1)