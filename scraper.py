import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# Base URL for constructing absolute links
BASE_URL = "https://careers.boozallen.com"

# Set a User-Agent to mimic a real browser visit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def parse_job_details(job_url):
    """Scrapes the details from an individual job posting page."""
    print(f"  -> Scraping details from: {job_url}")
    soup = get_soup(job_url)
    if not soup:
        return {}

    job_data = {'URL': job_url}

    # --- Extract Key-Value data from the top article section ---
    top_details = soup.find('article', class_='article--details--top')
    if top_details:
        fields = top_details.find_all('div', class_='article__content__view__field')
        for field in fields:
            label_tag = field.find('div', class_='article__content__view__field__label')
            value_tag = field.find('div', class_='article__content__view__field__value')
            if label_tag and value_tag:
                label = label_tag.text.strip().replace(':', '')
                value = value_tag.text.strip()
                job_data[label] = value

    # --- Extract text block data from the main description section ---
    rich_text_container = soup.find('div', class_='article__content--rich-text')
    if rich_text_container:
        # Find all section headers (e.g., <b><span>The Opportunity:</span></b>)
        section_headers = rich_text_container.find_all('b')
        
        for header in section_headers:
            header_text = header.get_text(strip=True).replace(':', '')
            # List of headers we want to capture
            if header_text in ["The Opportunity", "You Have", "Nice If You Have", "Clearance", "Compensation", "Identity Statement", "Work Model"]:
                content = []
                # Collect all sibling tags until the next <b> tag
                for sibling in header.find_next_siblings():
                    if sibling.name == 'b':
                        break # Stop when we hit the next section header
                    if sibling.name: # Ensure it's a tag
                        content.append(sibling.get_text(separator=' ', strip=True))
                
                job_data[header_text] = ' '.join(content).strip()

    return job_data


def main():
    """Main function to orchestrate the scraping process."""
    start_url = f"{BASE_URL}/jobs/search"
    all_jobs_data = []
    current_page_url = start_url
    page_count = 1

    while current_page_url:
        print(f"Scraping page {page_count}: {current_page_url}")
        soup = get_soup(current_page_url)
        if not soup:
            break

        # Find all job rows in the table body
        job_table = soup.find('tbody')
        if not job_table:
            print("Could not find job table. Exiting.")
            break
            
        job_rows = job_table.find_all('tr')
        if not job_rows:
            print("No more job listings found on this page.")
            break
        
        for row in job_rows:
            title_cell = row.find('td', class_='cell-title')
            if title_cell and title_cell.a:
                job_title = title_cell.a.text.strip()
                job_link = title_cell.a['href']
                
                # Ensure link is absolute
                if not job_link.startswith('http'):
                    job_link = BASE_URL + job_link
                
                # Scrape the details from the job's dedicated page
                job_details = parse_job_details(job_link)
                job_details['Job Title'] = job_title
                all_jobs_data.append(job_details)
                
                # Be a good web citizen, don't spam requests
                time.sleep(1) 
        
        # --- Find the link to the next page ---
        next_link_tag = soup.find('a', class_='paginationNextLink')
        if next_link_tag and next_link_tag.get('href'):
            current_page_url = BASE_URL + next_link_tag['href']
            page_count += 1
        else:
            print("No 'Next' page link found. Reached the last page.")
            current_page_url = None # End the loop
            
        time.sleep(1) # Pause between scraping list pages

    # --- Save the data to a CSV file ---
    if all_jobs_data:
        print(f"\nScraping complete. Found {len(all_jobs_data)} jobs.")
        # Define the desired column order
        columns = [
            'Job Title', 'Job Number', 'Location', 'Remote Work', 'URL', 'The Opportunity', 
            'You Have', 'Nice If You Have', 'Clearance', 'Compensation', 'Identity Statement', 'Work Model'
        ]
        
        df = pd.DataFrame(all_jobs_data)
        
        # Reorder and fill missing columns with empty string
        df = df.reindex(columns=columns, fill_value='')

        output_filename = 'booz_allen_jobs.csv'
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Data successfully saved to {output_filename}")
    else:
        print("No job data was scraped.")


if __name__ == "__main__":
    main()