# scripts/update_publications.py

import os
import re
from bs4 import BeautifulSoup
from scholarly import scholarly
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def setup_selenium_driver():
    """Setup Selenium WebDriver with Chrome options for headless browsing"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_scholar_with_selenium(scholar_url):
    """Scrape Google Scholar publications using Selenium"""
    driver = setup_selenium_driver()
    publications = []
    
    try:
        print(f"Accessing Google Scholar: {scholar_url}")
        driver.get(scholar_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gsc_a_tr"))
        )
        
        print("Page loaded, looking for publications...")
        
        # Click "Show more" button until all publications are loaded
        show_more_clicks = 0
        max_clicks = 50  # Safety limit to prevent infinite loops
        
        while show_more_clicks < max_clicks:
            try:
                # Wait a bit before checking for the button
                time.sleep(2)
                
                # Find the "Show more" button
                show_more_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "gsc_bpf_more"))
                )
                
                # Check if button is visible and enabled
                if show_more_btn.is_displayed() and show_more_btn.is_enabled():
                    # Get current publication count before clicking
                    current_pubs = len(driver.find_elements(By.CLASS_NAME, "gsc_a_tr"))
                    print(f"Current publications loaded: {current_pubs}")
                    
                    # Scroll to the button and click it
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", show_more_btn)
                    
                    show_more_clicks += 1
                    print(f"Clicked 'Show more' button {show_more_clicks} times")
                    
                    # Wait for new content to load
                    time.sleep(3)
                    
                    # Check if new publications were loaded
                    new_pubs = len(driver.find_elements(By.CLASS_NAME, "gsc_a_tr"))
                    if new_pubs == current_pubs:
                        print("No new publications loaded, assuming all are visible")
                        break
                        
                else:
                    print("Show more button not clickable, all publications likely loaded")
                    break
                    
            except Exception as e:
                print(f"No more 'Show more' button found or error: {e}")
                break
        
        # Final count of publications
        final_pub_count = len(driver.find_elements(By.CLASS_NAME, "gsc_a_tr"))
        print(f"Total publications found: {final_pub_count}")
        
        # Extract publication data
        pub_elements = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
        
        for i, pub_element in enumerate(pub_elements, 1):
            try:
                print(f"Processing publication {i}/{len(pub_elements)}")
                
                # Get title
                title_element = pub_element.find_element(By.CLASS_NAME, "gsc_a_at")
                title = title_element.text.strip()
                
                # Get the full text of the publication row
                pub_text = pub_element.text.strip()
                lines = pub_text.split('\n')
                
                # Parse authors and venue from the lines
                authors = ""
                venue = ""
                year = ""
                
                if len(lines) >= 2:
                    authors = lines[1] if len(lines) > 1 else ""
                    venue = lines[2] if len(lines) > 2 else ""
                
                # Extract year from the rightmost column
                try:
                    year_element = pub_element.find_element(By.CLASS_NAME, "gsc_a_y")
                    year = year_element.text.strip() if year_element.text.strip() else "N/A"
                except:
                    year = "N/A"
                
                # Try to get citation count
                citation_count = ""
                try:
                    citation_element = pub_element.find_element(By.CLASS_NAME, "gsc_a_c")
                    citation_count = citation_element.text.strip()
                except:
                    citation_count = "0"
                
                # For now, we'll skip trying to get individual PDF links to avoid
                # complications with navigation. This can be enhanced later.
                pdf_link = ""
                
                if title:  # Only add if we have a title
                    publications.append({
                        'title': title,
                        'authors': authors,
                        'venue': venue,
                        'year': year,
                        'pdf_link': pdf_link,
                        'citations': citation_count
                    })
                    print(f"Added: {title[:50]}...")
                
            except Exception as e:
                print(f"Error extracting publication {i}: {e}")
                continue
        
        print(f"Successfully extracted {len(publications)} publications")
        
    except Exception as e:
        print(f"Error scraping with Selenium: {e}")
    
    finally:
        driver.quit()
    
    return publications

def scrape_scholar_with_scholarly(author_name):
    """Alternative method using scholarly library"""
    try:
        print(f"Searching for author: {author_name}")
        search_query = scholarly.search_author(author_name)
        author = scholarly.fill(next(search_query))
        
        publications = []
        for pub in author['publications']:
            pub_filled = scholarly.fill(pub)
            
            # Extract publication data
            title = pub_filled.get('title', '')
            authors = ', '.join(pub_filled.get('author', []))
            venue = pub_filled.get('venue', '')
            year = pub_filled.get('year', 'N/A')
            pdf_link = pub_filled.get('eprint_url', '')
            
            publications.append({
                'title': title,
                'authors': authors,
                'venue': venue,
                'year': str(year),
                'pdf_link': pdf_link
            })
        
        return publications
    
    except Exception as e:
        print(f"Error with scholarly: {e}")
        return []

def format_publication_html(pub, index):
    """Format a single publication as HTML list item"""
    title = pub['title']
    authors = pub['authors']
    venue = pub['venue']
    year = pub['year']
    pdf_link = pub['pdf_link']
    
    # Create PDF link HTML
    pdf_html = ""
    if pdf_link:
        pdf_html = f' [<a href="{pdf_link}" target="_blank">pdf</a>]'
    
    html = f'''  <li><span style="color: rgb(204, 0, 0);"><span style="color: rgb(153, 0, 0);">{title}</span></span><span style="color: red; font-family: Times New Roman,Times,serif;"><span style="color: red;"><span style="color: black;">{pdf_html}<br>
    <span style="font-family: Times New Roman;">{authors}</span><span style="font-family: Times New Roman;"></span><br style="font-family: Times New Roman;">
    <span style="font-family: Times New Roman,Times,serif;"><p>{venue} {year}<br></p>
    </span></li>'''
    
    return html

def update_html_file(publications, html_file_path):
    """Update the HTML file with new publications"""
    try:
        # Read the current HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the publications list (ol tag after "Journals & Conference Proceedings")
        h2_tags = soup.find_all('h2')
        journals_h2 = None
        
        for h2 in h2_tags:
            if 'Journals' in h2.get_text() and 'Conference' in h2.get_text():
                journals_h2 = h2
                break
        
        if not journals_h2:
            print("Could not find 'Journals & Conference Proceedings' section")
            return False
        
        # Find the ol tag that follows
        ol_tag = journals_h2.find_next('ol')
        if not ol_tag:
            print("Could not find publications list")
            return False
        
        # Clear existing publications
        ol_tag.clear()
        
        # Add new publications
        for i, pub in enumerate(publications, 1):
            pub_html = format_publication_html(pub, i)
            li_soup = BeautifulSoup(pub_html, 'html.parser')
            ol_tag.append(li_soup.li)
        
        # Write updated HTML back to file
        with open(html_file_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        print(f"Successfully updated {html_file_path} with {len(publications)} publications")
        return True
        
    except Exception as e:
        print(f"Error updating HTML file: {e}")
        return False

def main():
    """Main function to orchestrate the publication update"""
    # Configuration - using the specific scholar profile you provided
    scholar_id = os.getenv('SCHOLAR_ID', 'UY1UAKUAAAAJ')  # Default to the provided ID
    scholar_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
    author_name = "Sabur Baidya"  # Fallback for scholarly library
    html_file_path = "publication.html"
    
    print("Starting publication update process...")
    print(f"Target Scholar URL: {scholar_url}")
    
    # Try Selenium method first
    publications = scrape_scholar_with_selenium(scholar_url)
    
    # If Selenium fails, try scholarly library
    if not publications:
        print("Selenium method failed. Trying scholarly library as fallback...")
        publications = scrape_scholar_with_scholarly(author_name)
    
    if not publications:
        print("No publications found with either method. Exiting.")
        return
    
    # Sort publications by year (newest first), handling non-numeric years
    def get_sort_year(pub):
        try:
            return int(pub['year']) if pub['year'] != 'N/A' else 0
        except (ValueError, TypeError):
            return 0
    
    publications.sort(key=get_sort_year, reverse=True)
    
    print(f"Found {len(publications)} publications")
    
    # Print first few publications for verification
    print("\nFirst 3 publications found:")
    for i, pub in enumerate(publications[:3], 1):
        print(f"{i}. {pub['title'][:60]}... ({pub['year']})")
    
    # Update HTML file
    success = update_html_file(publications, html_file_path)
    
    if success:
        print("Publications updated successfully!")
    else:
        print("Failed to update publications")
        exit(1)

if __name__ == "__main__":
    main()