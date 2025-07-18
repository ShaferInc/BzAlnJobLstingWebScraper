# src/main.py
import pandas as pd
from scraper.scraper import scrape_all_jobs
from scraper.utils.logger import log

def main():
    """Entry point of the application."""
    log.info("Starting the Booz Allen job scraper.")
    
    try:
        scraped_data = scrape_all_jobs()

        if not scraped_data:
            log.warning("No job data was scraped. Exiting.")
            return

        log.info(f"Scraping complete. Found {len(scraped_data)} jobs.")
        
        # --- Save the data to a CSV file ---
        columns = [
            'Job Title', 'Job Number', 'Location', 'Remote Work', 'URL', 'The Opportunity', 
            'You Have', 'Nice If You Have', 'Clearance', 'Compensation', 'Identity Statement', 'Work Model'
        ]
        
        df = pd.DataFrame(scraped_data)
        df = df.reindex(columns=columns, fill_value='') # Ensure consistent column order

        output_filename = 'booz_allen_jobs.csv'
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        log.info(f"Data successfully saved to {output_filename}")

    except Exception as e:
        log.critical(f"A critical error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()