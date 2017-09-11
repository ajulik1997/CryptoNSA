############################################################
#
#	Author: Alexander Liptak
#	Date: 09 September 2017
#	E-Mail: Alexander.Liptak.2015@live.rhul.ac.uk
#	Phone: +44 7901 595107
#
#	Sentiment check dictionary obtained from:
#	https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html
#
############################################################
#
#	Scrapes a live news forex website for articles about
#		cryptocurrencies and performs a basic sentiment check
#
############################################################
#						IMPORTS
############################################################

import requests
from bs4 import BeautifulSoup
import time
import re

############################################################
# 			LIST OF CRYPTOCURRENCIES TO CHECK FOR
############################################################

active_coins = [['BTC','Bitcoin'],
				['ETH','Ethereum'],
				['LTC','Litecoin'],
				['XRP','Ripple'],
				['BCH','Bitcoin Cash']]

############################################################
#				LOAD SENTIMENT CHECK DICTIONARY
############################################################

positive = []
with open('positive-words.txt') as file:
	for line in file:
		if line[0] != ';' and line[0] != '\n':
			positive.append(line.strip())

negative = []
with open('negative-words.txt') as file:
	for line in file:
		if line[0] != ';' and line[0] != '\n':
			negative.append(line.strip())

############################################################
#			PERFORM INITIAL ARTICLE COLLECTION
############################################################

articles = [[],[],[],[],[]]	# LINK, DATETIME, CRYPTOCURRENCY, SENTIMENT, CONFIDENCE
previous_articles = [] # used to check to see if any changes have been made

urls = ["http://www.forexlive.com"]	# main URL
urls.extend(list("http://www.forexlive.com/Headlines/"+str(i) for i in range(1,41)))	# rest of articles

for url in urls:
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	for rawlink in soup.find_all('a'):					# for every <a> tag
		if "www.forexlive.com/news/" in str(rawlink):	# if it is a NEWS link
			link = rawlink.get('href')					# fetch link from tag
			link = 'http://'+link[link.find('www'):]	# turn into usable link
			if link not in articles[0]:					# if link not in list, append
				print("FOUND NEW:", link)
				articles[0].append(link)
				articles[2].append('UNTESTED')

############################################################
#				MAIN LOOP, REPEATS EVERY MINUTE
############################################################

while True:
	response = requests.get(urls[0])
	soup = BeautifulSoup(response.text, 'html.parser')
	for rawlink in soup.find_all('a'):					# for every <a> tag
		if "www.forexlive.com/news/" in str(rawlink):	# if it is a NEWS link
			link = rawlink.get('href')					# fetch link from tag
			link = 'http://'+link[link.find('www'):]	# turn into usable link
			if link not in articles[0]:					# if link not in list, append
				print("FOUND NEW:", link)
				articles[0].append(link)
				articles[2].append('UNTESTED')
	
	if previous_articles != articles:					# only do everything if there has been a change
	
		print("==================================================")	
		
		for index, item in enumerate(articles[0]):			# for every link
			if articles[2][index] == 'UNTESTED':			# only do something if it is untested yet
				if any(name.lower() in item.lower() for name in [entry for coin in active_coins for entry in coin]): # if link contains any cryptocurrency name or tag
					for coin in active_coins:				# for every active cryptocurrency
						if any(name.lower() in item.lower() for name in coin): # if the name or tag of a cryptocurrency appears in title
							print(coin[0], item)			# label link with cryptocurrency tag
							articles[2][index] = coin[0]
				else:										# if link does not contain name or tag of any cryptocurrency
					print("N/A", item)						# mark it as irrelevant
					articles[2][index] = "N/A"

		print("==================================================")
		
		for i in range(len(articles[1]), len(articles[0])):
			positive_index, negative_index = 0, 0
			
			articlesoup = BeautifulSoup(requests.get(articles[0][i]).text, 'html.parser') # get soup from link
			articletext = articlesoup.article.find_all('div','artbody')[0].get_text(' ', strip=True).lower() # extract article text from link
			words = len(re.sub('[^a-z\ \']+', ' ',  articletext).split()) # split text into words, obeying grammar
			
			articles[1].append(articlesoup.article.find_all('time')[1].get_text()) # fill in timestamp for article
			
			if articles[2][i] != 'N/A':
				for word in positive:						# count all positive sentiment words
					positive_index=positive_index+articletext.lower().count(word)
				for word in negative:						# count all negative sentiment words
					negative_index=negative_index+articletext.lower().count(word)
				
				if positive_index > negative_index:			# If more + than - words, article is + with score (+)/(total) 
					opinion = 'POSITIVE'
					score = '{:.1%}'.format(positive_index/(positive_index+negative_index))
				if negative_index > positive_index:			# If more - than + words, article is - with score (-)/(total) 
					opinion = 'NEGATIVE'
					score = '{:.1%}'.format(negative_index/(positive_index+negative_index))
				if positive_index == negative_index:		# If there is same number of + and - words, article is neutral with score 50%
					opinion = 'NEUTRAL'
					score = '50%'
				confidence = '{:.1%}'.format((positive_index+negative_index)/words)	# calculated as (sentiment words)/(total words analysed)
				
				articles[3].append([opinion, score])		# update article sentiment score
				articles[4].append(['Confidence:',confidence]) # update article sentiment condfidence
				
				print(articles[2][i], articles[3][i], articles[4][i], articles[0][i])

			else: 											# fill irrelevant article information
				articles[3].append('N/A')
				articles[4].append('N/A')
				
		print("==================================================")	
		
		previous_articles = articles[:]						# to check if any changes have been made next loop
	
	time.sleep(60)	## poll website every minute