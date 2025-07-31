# import the necessary modules
import requests
import pandas as pd 
import argparse
from datetime import datetime
import xml.etree.ElementTree as ET 
import time
 
# Function to fetch data from the pubmed API
def fetch_data_from_pubmed(query, max_results=10):
    url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed", # default database
        "term": query, # search term
        "retmax": max_results, # it can also be changed further
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    # print("[esearch] Status Code:", response.status_code)
    # print("[esearch] Response Preview:", response.text[:300])  
    # print(response.text)
    return response.text

# Fetch the papers with pubmed ID as pmid
def fetch_paper_info(pmid):
    url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    # print(f"[efetch] Status Code for PMID {pmid}:", response.status_code)
    # print("[efetch] Response Preview:", response.text[:300])
    return response.text

# parse the paper details from the XML response
def parse_paper_info(xml_data):
    root = ET.fromstring(xml_data)
    paper_info = []

    # iterate through each pubmed article to extract the necessary details
    for article in root.findall(".//PubmedArticle"):
        paper = {}

        # extract the pmid 
        pmid = article.find(".//PMID").text if article.find(".//PMID") is not None else "N/A"
        paper['PubMedID'] = pmid 

        # extract the title
        title = article.find(".//ArticleTitle").text if article.find(".//ArticleTitle") is not None else "N/A" 
        paper['Title'] = title

        # extract the date of publication
        pub_date = article.find(".//PubDate")
        if pub_date is not None:
            pub_year = pub_date.find("Year").text if pub_date.find("Year") is not None else "N/A"
            pub_month = pub_date.find("Month").text if pub_date.find("Month") is not None else "N/A"
            pub_day = pub_date.find("Day").text if pub_date.find("Day") is not None else "N/A"
            paper['Publication Date'] = f"{pub_year}-{pub_month}-{pub_day}"
        else: 
            paper['Publication Date'] = "N/A"
        
        # extract the industry affiliation
        non_academic_authors = []
        company_affiliations = []
        for author in article.findall(".//Author"):
            last_name = author.find("LastName").text if author.find("LastName") is not None else "N/A"
            fore_name = author.find("ForeName").text if author.find("ForeName") is not None else "N/A"
            affiliation = author.find("AffiliationInfo/Affiliation").text if author.find("AffiliationInfo/Affiliation") is not None else "N/A"

            if "pharma" in affiliation.lower() or "biotech" in affiliation.lower():
                company_affiliations.append(affiliation)
            else:
                non_academic_authors.append(f"{fore_name} {last_name}")
        paper["Non-academic Authors"] = ", ".join(non_academic_authors)
        paper["Company Affiliations"] = ", ".join(company_affiliations)

        # extract the corresponding author's email
        corresponding_email = article.find(".//CorrespondingAuthor/Email")
        paper["Corresponding Author Email"] = corresponding_email.text if corresponding_email is not None else "N/A"

        paper_info.append(paper)

    return paper_info

# output the results to CSV format
def output_csv_result(data, filename="papers.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

# command line interface to run the script
def parse_args():
     parser = argparse.ArgumentParser(description="fetch the papers from pubmed")
     parser.add_argument("query", type=str, help="Query to search papers on PubMed")
     parser.add_argument("-f", "--file", type=str, help="Filename to save the results", default="papers.csv")
     parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
     return parser.parse_args()

# main function 
def main():
    args = parse_args()
    if args.debug:
        print(f"Searching for papers with query: {args.query}")
        xml_response = fetch_data_from_pubmed(args.query)

        root = ET.fromstring(xml_response)
        paper_ids = [id_elem.text for id_elem in root.findall(".IdList/Id")]

        papers_data=[]

        for pmid in paper_ids:
            if args.debug:
                print(f"Fetching details for PubMed ID: {pmid}")
            paper_details = fetch_paper_info(pmid)
            parsed_paper = parse_paper_info(paper_details)
            papers_data.extend(parsed_paper)
            time.sleep(1) 
        
        output_csv_result(papers_data, args.file)
        print(f"Results saved to {args.file}")


# running the script
if __name__ == "__main__":
    main()