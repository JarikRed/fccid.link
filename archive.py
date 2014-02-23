#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import string
import sys
import re

fcc_url = "https://apps.fcc.gov"
product_search_url = "/oetcf/eas/reports/GenericSearchResult.cfm?RequestTimeout=500"

s = requests.Session()

# Perform FCC id search
def lookup_fccid(appid, productid):
	payload = {
		"application_status" : "",
		"applicant_name" : "",
		"grant_date_from" : "",
		"grant_date_to" : "",
		"grant_comments_label" : "",
		"application_purpose" : "",
		"application_purpose_description" : "",
		"grant_code_1" : "",
		"grant_code_2" : "",
		"grant_code_3" : "",
		"test_firm" : "",
		"equipment_class" : "",
		"equipment_class_description" : "",
		"lower_frequency" : "",
		"upper_frequency" : "",
		"freq_exact_match" : "checked",
		"bandwidth_from" : "",
		"emission_designator" : "",
		"tolerance_from" : "",
		"tolerance_to" : "",
		"tolerance_exact_match" : "checked",
		"power_output_from" : "",
		"power_output_to" : "",
		"power_exact_match" : "checked",
		"rule_part_1" : "",
		"rule_part_2" : "",
		"rule_part_3" : "",
		"rule_part_exact_match" : "checked",
		"product_description" : "",
		"tcb_code" : "",
		"tcb_code_description" : "",
		"tcb_scope" : "",
		"tcb_scope_description" : "",
		"fetchfrom" : "0",
		"calledFromFrame" : "Y",
		"comments" : "",
		"show_records" : "25",
		"grantee_code" : appid,
		"product_code" : productid
	}
	print(s.cookies)
	r = s.post(fcc_url + product_search_url, data=payload)
	print(r.cookies)
	print("FCC id lookup complete")
	return r.text

# Try to format appid and productid correctly
def parse_fccid(appid=None, productid=None):
	if appid is None:
		return None
	if productid is None:
		productid = ''
	if appid[0] in string.ascii_letters:
		app_len = 3
	elif appid[0] in string.digits:
		app_len = 5
	else:
		return None
	
	if len(appid) > app_len:
		productid = appid[app_len:] + productid
		appid = appid[:app_len]
	return (appid, productid)

# Parsesearch results page to find "Detail" link
def parse_search_results(html):
	soup = BeautifulSoup(html)
	#print(html.prettify())
	
	rs_tables = soup("table", id="rsTable")
	if len(rs_tables) != 1:
		raise Exception("Error, found %d results tables" % len(rs_tables))
	
	links = rs_tables[0].find_all("a", href=re.compile("/oetcf/eas/reports/ViewExhibitReport.cfm\?mode=Exhibits"))
	if len(links) != 1:
		raise Exception("Error, found %d results tables" % len(links))

	print("Detail link found")
	return links[0]['href']

# Request details page
def get_attachment_urls(detail_url):
	print(s.cookies)
	r = s.get(fcc_url + detail_url)
	print(r.cookies)
	soup = BeautifulSoup(r.text)
	
	rs_tables = soup("table", id="rsTable")
	if len(rs_tables) != 1:
		raise Exception("Error, found %d results tables" % len(rs_tables))
	
	links = rs_tables[0].find_all("a", href=re.compile("/eas/GetApplicationAttachment.html"))
	hrefs = [link['href'] for link in links]

	print("Exhibit links found")
	return hrefs

# Fetch files and pack in to archive
def fetch_and_pack(urls, filename):
	with open(filename, 'wb') as handle:
		print(s.cookies)
		r = s.get(fcc_url + urls[0], cookies=s.cookies)
		print(r.cookies)
		for chunk in r.iter_content():
			handle.write(chunk)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		(appid, productid) = parse_fccid(*sys.argv[1:])
	else:
		(appid, productid) = parse_fccid(appid='ZYXSMARTIP1')
	html_doc = lookup_fccid(appid, productid)
	detail_url = parse_search_results(html_doc)
	attachment_urls = get_attachment_urls(detail_url)
	filename = "%s_%s.tar.gz" % (appid, productid)
	# testing
	filename = "test.pdf"
	fetch_and_pack(attachment_urls, filename)
