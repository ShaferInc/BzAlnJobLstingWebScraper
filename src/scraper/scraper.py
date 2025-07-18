# src/scraper/scraper.py
import requests
from bs4 import BeautifulSoup
import time
import logging

# Use the logger configured in the logger utility
from .utils.logger import log

# Constants
BASE_URL = "https://careers.boozallen.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching URL {url}: {e}")
        return None

def parse_job_details(job_url):
    """Scrapes the details from an individual job posting page."""
    log.info(f"Scraping details from: {job_url}")
    soup = get_soup(job_url)
    if not soup:
        return {}

    job_data = {'URL': job_url}
    
    # Extract Key-Value data from the top article section
    top_details = soup.find('article', class_='article--details--top')
    if top_details:
        for field in top_details.find_all('div', class_='article__content__view__field'):
            label_tag = field.find('div', class_='article__content__view__field__label')
            value_tag = field.find('div', class_='article__content__view__field__value')
            if label_tag and value_tag:
                label = label_tag.text.strip().replace(':', '')
                value = value_tag.text.strip()
                job_data[label] = value

    # Extract text block data from the main description section
    rich_text_container = soup.find('div', class_='article__content--rich-text')
    if rich_text_container:
        for header in rich_text_container.find_all('b'):
            header_text = header.get_text(strip=True).replace(':', '')
            if header_text in ["The Opportunity", "You Have", "Nice If You Have", "Clearance", "Compensation", "Identity Statement", "Work Model"]:
                content = []
                for sibling in header.find_next_siblings():
                    if sibling.name == 'b': break
                    if sibling.name: content.append(sibling.get_text(separator=' ', strip=True))
                job_data[header_text] = ' '.join(content).strip()
                
    return job_data

def scrape_all_jobs():
    """Main function to orchestrate the scraping process and return data."""
    start_url = f"{BASE_URL}/jobs/search"
    all_jobs_data = []
    current_page_url = start_url
    page_count = 1

    while current_page_url:
        log.info(f"Scraping page {page_count}: {current_page_url}")
        soup = get_soup(current_page_url)
        if not soup: break

        job_table = soup.find('tbody')
        if not job_table:
            log.warning("Could not find job table. Exiting.")
            break
        
        job_rows = job_table.find_all('tr')
        if not job_rows:
            log.info("No more job listings found on this page.")
            break
        
        for row in job_rows:
            title_cell = row.find('td', class_='cell-title')
            if title_cell and title_cell.a:
                job_title = title_cell.a.text.strip()
                job_link = BASE_URL + title_cell.a['href']
                
                job_details = parse_job_details(job_link)
                job_details['Job Title'] = job_title
                all_jobs_data.append(job_details)
                time.sleep(1) # Be respectful
        
        next_link_tag = soup.find('a', class_='paginationNextLink')
        if next_link_tag and next_link_tag.get('href'):
            current_page_url = BASE_URL + next_link_tag['href']
            page_count += 1
        else:
            log.info("No 'Next' page link found. Reached the last page.")
            current_page_url = None
        time.sleep(1)
        
    return all_jobs_data