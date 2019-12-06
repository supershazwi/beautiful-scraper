# coding=utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

import csv
import time
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["price-manager"]
productsTable = db["products"]
crawldatesTable = db["crawldates"]

page = 0
lastPage = 999

ff = webdriver.Chrome()

while page < lastPage:

	# open up chrome browser to crawl beautiful.me's profile so as to
	# list all the items that they are selling. these items' prices will be 
	# compared to prices on other platforms via google shopping
	# will go page by page till end of profile

	url = "https://shopee.sg/beautiful.me?page="+str(page)+"&sortBy=pop"
	ff.get(url)

	print('crawling page' + str(page))
	
	final_listing_to_mongo = []
	pricing_to_excel = []

	try:
	    element = WebDriverWait(ff, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "shop-search-result-view__item")))
	finally:
		soup = BeautifulSoup(ff.page_source, 'html.parser')

		listing_array = soup.find_all("div", {"class":["_1NoI8_", "_2gr36I"]})
		pricing_array = soup.find_all("div", {"class":["_1w9jLI _37ge-4 _2XtIUk"]})

		if(lastPage == 999):
			lastPage = float(soup.find("span", {"class": "shopee-mini-page-controller__total"}).text)

		print("lastPage: " + str(lastPage))

		for listing in listing_array:
			final_listing_to_mongo.append((listing.text).encode('utf-8'))

		for pricing in pricing_array:
			span_array = pricing.find_all("span")
			if len(span_array) == 2:
				pricing_to_excel.append((span_array[0].text + span_array[1].text).encode('utf-8'))
			else:
				pricing_to_excel.append((span_array[0].text + span_array[1].text + " - " + span_array[2].text + span_array[3].text).encode('utf-8'))

	page = page + 1

	# once list of items on the current page is crawled, open google
	# shopping to start comparing to other sites 

	for counter_1, listing_from_shopee in enumerate(final_listing_to_mongo):
		url = "https://www.google.com/shopping?hl=en"
		ff.get(url)

		print(counter_1)

		grid_layout = 0

		try:
			element = WebDriverWait(ff, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="lst-ib"]')))
		finally:
			search_element = WebDriverWait(ff, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="lst-ib"]')))
			search_element.send_keys(listing_from_shopee.decode('utf-8'))
			print("Searching: " + listing_from_shopee.decode('utf-8'))
			search_element.send_keys(Keys.RETURN)

			grid_layout = soup.find_all("span", {"class": "Ytbez IYWnmd"})
			
			print("Grid layout: " + str(len(grid_layout)))

			if(len(grid_layout) != 0):
				list_element = WebDriverWait(ff, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="taw"]/div[1]/div/div/a')))
				list_element.click()

			time.sleep(0.5)

			soup = BeautifulSoup(ff.page_source, 'html.parser')

			from_is_present = True

			google_shop_array = soup.find_all("div", {"class": "g27Cj"})

			google_url_array = []

			# sometimes the values are placed in different classes
			# therefore these many cases just to get the SHOP names

			if(len(google_shop_array) == 0):
				from_is_present = False
				google_shop_array = soup.find_all("a", {"class": "shntl hy2WroIfzrX__merchant-name"})
				google_url_array = soup.find_all("a", {"class": "shntl hy2WroIfzrX__merchant-name"})
			
			if(len(google_shop_array) == 0):
				from_is_present = False
				google_shop_array = soup.find_all("div", {"class": "kD8n3"})
			
			if(len(google_shop_array) == 0):
				from_is_present = False
				google_shop_array = soup.find_all("a", {"class": "r29r0b a3H7pd shntl"})

			if(from_is_present):
				for counter_9, shop in enumerate(google_shop_array):
					processed = (shop.text).encode('utf-8')
					index = processed.find("from")
					google_shop_array[counter_9] = processed[index+5:]
			else:
				for counter_9, shop in enumerate(google_shop_array):
					google_shop_array[counter_9] = (shop.text).encode('utf-8')

			# sometimes the values are placed in different classes
			# therefore these many cases just to get the ITEM names
			
			google_listing_array = soup.find_all("a", {"class":"AGVhpb"})
			if(len(google_listing_array) == 0):
				google_listing_array = soup.find_all("a", {"class":"GyDBsd"})
			if(len(google_listing_array) == 0):
				google_listing_array = soup.find_all("a", {"class":"VZTCjd"})
			if(len(google_listing_array) == 0):
				google_listing_array = soup.find_all("a", {"class":"EI11Pd"})
			if(len(google_listing_array) == 0):
				google_listing_array = soup.find_all("a", {"class":"VQN8fd"})
				
			for counter_4, listing in enumerate(google_listing_array):
				google_listing_array[counter_4] = (listing.text).encode('utf-8')

			google_pricing_array = soup.find_all("span", {"class":"Nr22bf"})
			for counter_5, pricing in enumerate(google_pricing_array):
				google_pricing_array[counter_5] = (pricing.text[:-1]).encode('utf-8')

			# sometimes the values are placed in different classes
			# therefore these many cases just to get the URLs

			if(len(google_url_array) == 0):
				google_url_array = soup.find_all("a", {"class":"AGVhpb"})
			if(len(google_url_array) == 0):
				google_url_array = soup.find_all("a", {"class":"GyDBsd"})
			if(len(google_url_array) == 0):
				google_url_array = soup.find_all("a", {"class":"VZTCjd"})
			if(len(google_url_array) == 0):
				google_url_array = soup.find_all("a", {"class":"EI11Pd"})
			if(len(google_url_array) == 0):
				google_url_array = soup.find_all("a", {"class":"VQN8fd"})

			for counter_6, url in enumerate(google_url_array):
				google_url_array[counter_6] = "https://www.google.com" + (url.get('href')).encode('utf-8')

			# click all the links that has 2 or more shops to expose elements

			click_counter = 1

			print("google_shop_array length" + str(len(google_shop_array)))
			print(google_shop_array)

			if(len(google_shop_array) == 0):
				# find if there's a product already in the database
				
				product = productsTable.find_one({"title": final_listing_to_mongo[counter_1]})

				# product does not exist, so we create a new product profile
				# trackers are the comparison item, the shop it came from, url,
				# and price history on a daily basis

				if(product == None):
					product = { 
						"title": final_listing_to_mongo[counter_1], 
						"source": {
							"shop": "Shopee",
							"price": map(float, pricing_to_excel[counter_1].replace("$","").split(" - ")),
						},
						"trackers": [
						]
					}

					print("Creating product")
					print(product)

					productsTable.insert_one(product)

			other_matches = False

			# sometimes the google results appear in a grid layout instead of
			# the typical list, then some of the classes will change 
			# for items that have more than 1 shop in the google result,
			# we have to click the box so that it dynamically loads the classes
			# for us to crawl the other shops, urls, and prices

			if(len(grid_layout) != 0):
				for counter_10, shop in enumerate(google_shop_array):
					if(shop.find("shops") != -1):
						print("Shop: " + shop)
						print("Click counter: " + str(click_counter))
						print("Counter_10: " + str(counter_10))
						
						print("Clicking on: //*[@id='rso']/div/div/div["+str(click_counter)+"]/div/div[2]/div[3]/div/a")
						link_element = WebDriverWait(ff,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rso"]/div/div/div['+str(click_counter)+']/div/div[2]/div[3]/div/a')))
						link_element.click()

						click_counter = click_counter + 1

						time.sleep(0.75)
					else:
						print("Shop: " + shop)
						print("Counter_10: " + str(counter_10))
						click_counter = click_counter + 1
			else:
				temp_google_shop_array = []

				for counter_10, shop in enumerate(google_shop_array):
					if(shop.find("shops") != -1):
						# click link to expose elements
						print("Shop: " + shop)
						print("Click counter: " + str(click_counter))
						print("Counter_10: " + str(counter_10))
						try:
							if(other_matches):
								print("Clicking on: //*[@id='rso']/div[2]/div[2]/div["+str(click_counter)+"]/div/div[2]/div/div[1]/a")
								link_element = WebDriverWait(ff,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rso"]/div[2]/div[2]/div['+str(click_counter)+']/div/div[2]/div/div[1]/a')))
								link_element.click()
								click_counter = click_counter + 2
							else:
								print("Clicking on: //*[@id='rso']/div[1]/div/div["+str(click_counter)+"]/div/div[2]/div/div[1]/a")
								link_element = WebDriverWait(ff,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rso"]/div[1]/div/div['+str(click_counter)+']/div/div[2]/div/div[1]/a')))
								link_element.click()
								click_counter = click_counter + 2
						except:
							print("Timeout!!! Other matches is true")
							print("Take check of which shops are left")
							click_counter = 1
							temp_google_shop_array = google_shop_array[counter_10:]

							break

						time.sleep(0.75)
					else:
						print("Shop: " + shop)
						print("Counter_10: " + str(counter_10))
						click_counter = click_counter + 1

				# time to run through the remaining shops
				if(len(temp_google_shop_array) > 0):
					for counter_11, shop in enumerate(temp_google_shop_array):
						if(shop.find("shops") != -1):
							print("Shop: " + shop)
							print("Click counter: " + str(click_counter))
							print("Counter_10: " + str(counter_11))

							link_element = WebDriverWait(ff,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rso"]/div[2]/div[2]/div['+str(click_counter)+']/div/div[2]/div/div[1]/a')))
							click_counter = click_counter + 2
						else:
							print("Shop: " + shop)
							print("Counter_10: " + str(counter_11))
							click_counter = click_counter + 1

						time.sleep(0.75)

			time.sleep(0.5)

			# this is to find the values of all the prices, regardless of
			# whether the result is only 1 shop or if the result is multiple
			# shops

			soup = BeautifulSoup(ff.page_source, 'html.parser')
			google_first_dollar_listings = soup.findAll('div', attrs={'class': '_-df'}) 
			if(len(google_first_dollar_listings) == 0):
				google_first_dollar_listings = soup.find_all('div', attrs={'class': '_-dh'})
			google_first_shop_listings = soup.findAll('a', attrs={'class': 'shntl internal-link sg-offer__offer-link'})
			if(len(google_first_shop_listings) == 0):
				google_first_shop_listings = soup.findAll('a', attrs={'class': '_-mz sh-os__altol shntl'})
			google_extra_dollar_listings = soup.findAll('td', attrs={'class': '_-d6'})
			google_extra_shop_listings = soup.findAll('a', attrs={'class': 'sh-os__altol shntl'})
			if(len(google_extra_shop_listings) == 0):
				google_extra_shop_listings = soup.findAll('a', attrs={'class': '_-mz sh-os__altol shntl'})

			print("Length of google_first_dollar_listings:" + str(len(google_first_dollar_listings)))
			print("Length of google_first_shop_listings:" + str(len(google_first_shop_listings)))
			print("Length of google_extra_dollar_listings:" + str(len(google_extra_dollar_listings)))
			print("Length of google_extra_shop_listings:" + str(len(google_extra_shop_listings)))

			print("google_listing_array length" + str(len(google_listing_array)))
			print(google_listing_array)
			
			listing_to_excel = []
			price_to_excel = []
			shop_to_excel = []
			url_to_excel = []

			for counter_10, shop in enumerate(google_shop_array):
				if(shop.find("shops") != -1):
					# theres more than 1 shop
					# retrieve digit
					shop_split = shop.split()[0]
					if(shop_split == '5+'):
						digit = 4
					else:
						digit = float(shop.split()[0])
					
					print("!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!")
					print("more than 1 shop")
					print(counter_10)
					print("Listing:" + google_listing_array[counter_10])
					
					print("Original price:" + google_first_dollar_listings[0].text)
					print("Original shop:" + google_first_shop_listings[0].text)
					print("Original url:" + "https://www.google.com" + google_first_shop_listings[0].get('href').encode('utf-8'))

					listing_to_excel.append(google_listing_array[counter_10])
					price_to_excel.append(google_first_dollar_listings[0].text.encode('utf-8'))
					shop_to_excel.append(google_first_shop_listings[0].text.encode('utf-8'))
					url_to_excel.append("https://www.google.com" + google_first_shop_listings[0].get('href').encode('utf-8'))


					google_first_dollar_listings.pop(0)
					google_first_shop_listings.pop(0)

					counterToDigit = 1

					while(counterToDigit < digit):
						print("Extra price:" + google_extra_dollar_listings[0].text)
						print("Extra shop:" + google_extra_shop_listings[0].text)
						print("Extra url:" + "https://www.google.com" + google_extra_shop_listings[0].get('href').encode('utf-8'))

						listing_to_excel.append(google_listing_array[counter_10])
						price_to_excel.append(google_extra_dollar_listings[0].text.encode('utf-8'))
						shop_to_excel.append(google_extra_shop_listings[0].text.encode('utf-8'))
						url_to_excel.append("https://www.google.com" + google_extra_shop_listings[0].get('href').encode('utf-8'))

						google_extra_dollar_listings.pop(0)
						google_extra_shop_listings.pop(0)

						counterToDigit = counterToDigit + 1
					
					print(" ")
					print(" ")
				else:
					print("!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!~!")
					print("1 shop")
					print(counter_10)
					print("Listing:" + google_listing_array[counter_10])

					print("Original price:" + google_pricing_array[counter_10])
					print("Original shop:" + google_shop_array[counter_10])
					print("Original url:" + google_url_array[counter_10])

					listing_to_excel.append(google_listing_array[counter_10])
					price_to_excel.append(google_pricing_array[counter_10].encode('utf-8'))
					shop_to_excel.append(google_shop_array[counter_10].encode('utf-8'))
					url_to_excel.append(google_url_array[counter_10].encode('utf-8'))

					print(" ")
					print(" ")

			# write to mongodb
			for counter_7, data in enumerate(listing_to_excel):
				# insert to mongodb database
				# check if btfl's product is in the database
				# identified by title
				
				product = productsTable.find_one({"title": final_listing_to_mongo[counter_1]})

				index = price_to_excel[counter_7].find(" ")
				if(index != -1):
					price_to_excel[counter_7] = price_to_excel[counter_7][:index]
				index2 = price_to_excel[counter_7].find("(")
				if(index2 != -1):
					price_to_excel[counter_7] = price_to_excel[counter_7][:index2]

				# if not in database, create new product
				if(product == None):
					crawldates_array = crawldatesTable.find()

					arrayForPriceHistory = []
					for crawldate in crawldates_array:
						arrayForPriceHistory.append({
							"price": float(price_to_excel[counter_7].replace("$","")),
							"date": crawldate['date']
						})

					arrayForPriceHistory.append({
						"price": float(price_to_excel[counter_7].replace("$","")),
						"date":  datetime.now()
					})

					ff.get(url_to_excel[counter_7])
					current_url = ff.current_url
					if(current_url.find("?") != -1):
						current_url = current_url[:current_url.find("?")]
					
					product = { 
						"title": final_listing_to_mongo[counter_1], 
						"source": {
							"shop": "Shopee",
							"price": map(float, pricing_to_excel[counter_1].replace("$","").split(" - ")),
						},
						"trackers": [
							{
								"title": listing_to_excel[counter_7],
								"shop": shop_to_excel[counter_7],
								"pricehistory": arrayForPriceHistory,
								"url": current_url
							}
						]
					}

					print("Creating product")
					print(product)

					productsTable.insert_one(product)

				# if in database, check whether the tracker is in the database
				elif(product != None):
					print("Product is not equal none")

					ff.get(url_to_excel[counter_7])
					current_url = ff.current_url
					if(current_url.find("?") != -1):
						current_url = current_url[:current_url.find("?")]

					productrow = productsTable.find_one({"title": final_listing_to_mongo[counter_1], "trackers":{"$elemMatch": {"title": listing_to_excel[counter_7], "url": current_url}}})
					updatedtrackers = ""
					if(productrow == None):
						# if not in database, create new tracker
						arrayForPriceHistory = []
						crawldates_array = crawldatesTable.find()

						for crawldate in crawldates_array:
							arrayForPriceHistory.append({
								"price": float(price_to_excel[counter_7].replace("$","")),
								"date": crawldate['date']
							})

						arrayForPriceHistory.append({
							"price": float(price_to_excel[counter_7].replace("$","")),
							"date":  datetime.now()
						})

						newTracker = {
							"title": listing_to_excel[counter_7],
							"shop": shop_to_excel[counter_7],
							"pricehistory": arrayForPriceHistory,
							"url": current_url
						}

						if(len(product["trackers"]) > 0):
							product["trackers"].append(newTracker)
						else:
							product["trackers"]

						productsTable.update_one({"_id": product["_id"]}, {"$set": {"trackers": product['trackers']}})
					else:
						# add price history to existing tracker
						for counter_12, tracker in enumerate(productrow['trackers']):
							if(tracker['title'] == listing_to_excel[counter_7]):
								tracker['pricehistory'].append({
									"price": float(price_to_excel[counter_7].replace("$","")),
									"date":  datetime.now()
								})
								productrow['trackers'][counter_12] = tracker
								break

						updatedtrackers = productrow['trackers']

						productsTable.update_one({"_id": product["_id"]}, {"$set": {"trackers": updatedtrackers}})

				print(" ")

			# check if there are trackers without current price history
				
			product = productsTable.find_one({"title": final_listing_to_mongo[counter_1]})
			changed = False

			crawldates_array = crawldatesTable.find()

			for counter_13, tracker in enumerate(product['trackers']):
				if(len(product['trackers'][counter_13]['pricehistory']) == crawldates_array.count()):
					product['trackers'][counter_13]['pricehistory'].append({
						"date":  datetime.now(),
						"price": tracker['pricehistory'][-1]['price']
					})
					changed = True

			if(changed):
				productsTable.update_one({"_id": product["_id"]}, {"$set": product})

		time.sleep(1.5)

crawldatesTable.insert_one({ "date":  datetime.now() })

# close chrome browser after crawling all items under beautiful.me

ff.quit()