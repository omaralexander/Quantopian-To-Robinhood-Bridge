#########################################
# This is fo running the robinhood algo #
#########################################

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime
from datetime import date
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from Robinhood import Robinhood
from Robinhood.exceptions import InvalidTickerSymbol
import numpy as pd
import math

def clear_all_positions():
	for open_positions in range(0,len(my_trader.order_history()["results"])):
			if str(my_trader.order_history()["results"][open_positions]["side"]) == "buy":
				try:
					my_trader.cancel_order(str(my_trader.order_history()["results"][open_positions]["id"]))
					pass
				except ValueError as e:
					break

def exit_current_positions():
	# we can add more logic to this later by using the bid size to gauge interest
	# in the stock and make a further prediction on if it will continue to go up or not

	for i in my_trader.securities_owned()['results']:

		symbol         = my_trader.get_url(i['instrument'])['symbol']
		purchase_price = float(i['average_buy_price'])
		price 		   = my_trader.last_trade_price(symbol)[0][0]
		price 		   = float(price) - 0.03

		my_trader.place_limit_sell_order(instrument_URL=None, symbol=str(symbol), time_in_force='GTC', price=price, quantity=float(i['quantity']))

				
# We depreciated this in favor of bid price
#def get_sell_price(stock, purchase_price):

#	current_price = float(my_trader.quote_data(stock)['last_trade_price'])
#	sell_price    = 0

#	if current_price > purchase_price:
		#we send over the purchase_price;DONT GET GREEDY,WE CAN INCREASE IT LATER USING THE DELTA BETWEEN THE PRICE AND PURCHASE PRICE
#		sell_price = float(make_div_by_05(1.01 * purchase_price, buy=False))

#	else:
		#we send over the current price since we're at a loss
#		sell_price = float(make_div_by_05(.98 * current_price, buy=False))

#	return sell_price

def get_buy_price(stock):
	placeholder = []

	for i in my_trader.get_historical_quotes(stock, interval='day', span='year')['historicals'][::-1][:20]:
		placeholder.append(float(i['close_price']))
	
	average_price = pd.mean(placeholder)
	current_price = float(my_trader.quote_data(stock)['last_trade_price'])

	if current_price > float(1.25 * average_price):
		buy_price = float(current_price)
	else:
		buy_price = float(current_price * .99)

	buy_price = float(make_div_by_05(buy_price, buy=True))

	return buy_price

def make_div_by_05(s, buy=False):
    s *= 20.00
    s = math.floor(s) if buy else math.ceil(s)
    s /= 20.00
    return s

def check_if_present(browser,text, max_attempts=3):
	attempt = 1
	while True:
		try:
			return browser.is_text_present(text)
		except StaleElementReferenceException:
			if attempt == max_attempts:
				raise
			attempt += 1

quantopian_email 	= email
quantopian_password = password
robinhood_password  = password
robinhood_email 	= email

my_trader = Robinhood()
my_trader.login(username=robinhood_email,password = robinhood_password)

clear_all_positions()

#we want to sell at the start of the day. To avoid selling out of positions we want to keep i.e we need to restart algo, we can only sell before 10 am


if datetime.datetime.now().hour == 9:
	exit_current_positions()


browser = webdriver.Chrome(".../chromedriver")

browser.get("https://www.quantopian.com/signin")

username = browser.find_element_by_id("user_email")
password = browser.find_element_by_id("user_password")

username.send_keys(quantopian_email) 
password.send_keys(quantopian_password)

signin = browser.find_element_by_id("login-button")
signin.click()

time.sleep(3)

already_entered = []

times_ran = 0
numbers   = ["0","1","2","3","4","5","6","7","8","9"]
today 	  = str(date.today())

run = [6,16,26,36,46,56]

while times_ran != 39:

	print("Ran this many times already ",times_ran)

	minute = 0
	time.sleep(30)
	while minute not in run:
		time.sleep(30)
		minute = datetime.datetime.now().minute
		print(minute)

	browser.get("https://www.quantopian.com/live_algorithms/5c362baaa9c533004b92fb82")
	#browser.get("https://www.quantopian.com/live_algorithms/5c4b7636c7aeb164b25c3cb4")
	time.sleep(3)

	clear_all_positions()

	stop = False

	while stop == False:

		i = 0
		action = ActionChains(browser)
		clicked = False

		while clicked == False:
			time.sleep(9)
		
			positions_count = browser.find_element_by_id("positions_count")
			positions_count = str(positions_count.text).replace("(","")
			positions_count = positions_count.replace(")","")
			positions_count = int(positions_count)

			open_orders = browser.find_elements_by_xpath("//div[@class='slick-cell l6 r6 order-status-cell']")
			stock 		= browser.find_elements_by_xpath("//div[@class = 'slick-cell l1 r1']")
			date 		= browser.find_elements_by_xpath("//div[@class = 'slick-cell l0 r0']")
			shares 		= browser.find_elements_by_xpath("//div[@class = 'slick-cell l3 r3']")

			print(len(open_orders),len(stock),len(date),len(shares))

			for i in range(0,len(open_orders)):

				trade_date = date[i + positions_count].text
				ordered_time = time.strptime(trade_date[:-9],"%Y-%m-%d") #staleelementhere
				todays_date  = time.strptime(today,"%Y-%m-%d")

				if ordered_time != todays_date:
					clicked = True
					stop 	= True
					break

				if open_orders[i].text == "Open":

					if trade_date != "" and trade_date[0] in numbers and stock[i + positions_count].text not in already_entered:

						current_stock  = stock[i + positions_count].text
						current_shares = shares[i + positions_count].text

						if int(current_shares) > 0:

							buy_price = get_buy_price(str(current_stock))

							my_trader.place_limit_buy_order(instrument_URL=None, symbol=str(current_stock), time_in_force='GTC', price=buy_price, quantity=current_shares)
							print(current_stock,buy_price,current_shares)
							already_entered.append(current_stock)
					
			action.move_to_element(open_orders[-1]).perform()
			
			i += 1

			load_more = browser.find_elements_by_xpath("//a[@class='load-older-orders-link']")

			if i > 30:
				clicked = True
				stop = True

			if len(load_more) > 0:
				load_more[0].click()
    			clicked = True
    			
	times_ran += 1		

browser.close()

print("we have finished,hopefuly we made some bucks")
