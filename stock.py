import requests
from bs4 import BeautifulSoup
import time
from requests.models import Response
from win10toast import ToastNotifier

class Stock:
    toaster = ToastNotifier()

    def __init__(self, ticker, conditions):
        self.ticker = ticker

        self.get_stock_info_init()
        self.set_alert_condition(conditions)

        self.exday_pricechange_rate = 0.0
        self.current_price = 0
        self.get_stock_info()
        self.prev_exday_pricechange_rate = self.exday_pricechange_rate
        self.prev_price = self.current_price

    def __get_html(self):
        url = "https://finance.naver.com/item/main.nhn?code=" + self.ticker
        response = requests.get(url)

        if response.status_code != 200:
            print("Failed to get html page")
            exit(-1)
        
        return response.text

    def get_stock_info_init(self):
        html = self.__get_html()
        soup = BeautifulSoup(html, "html.parser")

        self.name = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").get_text().strip()
        self.exday_price = int(soup.select_one("#chart_area > div.rate_info > table > tr:nth-child(3) > td.first > em > span.blind").get_text().replace(",", "").strip())

        self.condition_percent = []
        self.condition_price = []

    def get_stock_info(self):
        self.prev_exday_pricechange_rate = self.exday_pricechange_rate
        self.prev_price = self.current_price

        html = self.__get_html()
        soup = BeautifulSoup(html, "html.parser")

        self.current_price = int(soup.select_one("#chart_area > div.rate_info > div > p.no_today > em > span.blind").get_text().replace(",", "").strip())
        self.exday_pricechange = int(soup.select_one("#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2) > span.blind").get_text().replace(",", "").strip())
        self.exday_direction = soup.select_one("#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2) > span:nth-child(1)").get_text().strip()
        if self.exday_direction == "상승" or self.exday_direction == "상한가":
            self.exday_pricechange *= 1
        elif self.exday_direction == "하락" or self.exday_direction == "하한가":
            self.exday_pricechange *= -1

        self.exday_pricechange_rate = float(soup.select_one("#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4) > span:nth-child(1)").get_text().strip()\
                                    + soup.select_one("#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4) > span:nth-child(2)").get_text().strip())

    def set_alert_condition(self, conditions):
        for condition in conditions:
            if "%" in condition:
                self.condition_percent.append(float(condition.replace("%", "")))
            else:
                self.condition_price.append(int(condition))
        
        self.condition_percent_content = ["전일대비 {:+}%".format(self.condition_percent[i]) for i in range(len(self.condition_percent))]
        self.condition = list(zip(list(map(lambda p: self.exday_price * (100 + p) / 100, self.condition_percent)), self.condition_percent_content))

        self.condition_price_content = ["{:,}원".format(self.condition_price[i]) for i in range(len(self.condition_price))]
        self.condition += list(zip(self.condition_price, self.condition_price_content))

        self.condition.sort()

        print(self.name, self.condition)

    def check_alert_condition(self):
        satisfied_condition = []

        for condition in self.condition:
            if self.prev_price <= condition[0] and\
                condition[0] < self.current_price:
                satisfied_condition.append("{} 상향돌파".format(condition[1]))
        
        for condition in reversed(self.condition):
            if self.prev_price >= condition[0] and\
                condition[0] > self.current_price:
                satisfied_condition.append("{} 하향돌파".format(condition[1]))

        return satisfied_condition

    def alert(self, satisfied_condition):
        Stock.toaster.show_toast("📈" + self.name + " [" + self.ticker + "]",
                            "{:,} ({:+,}, {:+.2f}%)\n{}".format(self.current_price, self.exday_pricechange, self.exday_pricechange_rate, "\n".join(satisfied_condition)),
                            icon_path=None,
                            duration=4,
                            threaded=True)
        while Stock.toaster.notification_active():
            time.sleep(0.1)