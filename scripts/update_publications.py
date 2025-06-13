from scholarly import scholarly
import re
from bs4 import BeautifulSoup
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

def get_publications():
    # Search for Sabur Baidya's profile
    search_query = scholarly.search_author('Sabur Baidya')
    author = next(search_query)
    
    # Get all publications
    publications = []
    for pub in scholarly.search_pubs('author:"Sabur Baidya"'):
        publications.append({
            'title': pub.bib.get('title', ''),
            'authors': pub.bib.get('author', ''),
            'year': pub.bib.get('year', ''),
            'journal': pub.bib.get('journal', ''),
            'url': pub.bib.get('url', ''),
            'abstract': pub.bib.get('abstract', '')
        })
        time.sleep(2)  # Be nice to Google Scholar
    
    return publications

def update_html(publications):
    with open('aimslab.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find the publications section
    pub_section = soup.find('h2', string=re.compile('Publications'))
    if not pub_section:
        return
    
    # Create new publications list
    pub_list = soup.new_tag('ul')
    for pub in publications:
        li = soup.new_tag('li')
        
        # Create publication entry
        title = soup.new_tag('span', style='color: rgb(153, 0, 0);')
        title.string = pub['title']
        li.append(title)
        
        # Add links
        links = soup.new_tag('span', style='color: black;')
        links.append(' [')
        pdf_link = soup.new_tag('a', href=pub['url'], target='_blank')
        pdf_link.string = 'pdf'
        links.append(pdf_link)
        links.append(']')
        li.append(links)
        
        # Add authors
        authors = soup.new_tag('br')
        authors.string = pub['authors']
        li.append(authors)
        
        # Add venue and year
        venue = soup.new_tag('p')
        venue.string = f"{pub['journal']} {pub['year']}"
        li.append(venue)
        
        pub_list.append(li)
    
    # Replace old publications list with new one
    old_list = pub_section.find_next('ul')
    if old_list:
        old_list.replace_with(pub_list)
    else:
        pub_section.insert_after(pub_list)
    
    # Write updated HTML
    with open('aimslab.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

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
        
        # Click "Show more" button until all publications are loaded
        while True:
            try:
                show_more = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "gsc_bpf_more"))
                )
                if show_more.is_enabled():
                    show_more.click()
                    time.sleep(2)  # Wait for new publications to load
                else:
                    break
            except:
                break
        
        # Extract publication data
        pub_elements = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
        
        for pub_element in pub_elements:
            try:
                # Get title
                title_element = pub_element.find_element(By.CLASS_NAME, "gsc_a_at")
                title = title_element.text.strip()
                
                # Get the full text of the publication row
                pub_text = pub_element.text.strip()
                lines = pub_text.split('\n')
                
                # Parse authors and venue from the lines
                authors = lines[1] if len(lines) > 1 else ""
                venue = lines[2] if len(lines) > 2 else ""
                
                # Extract year
                try:
                    year_element = pub_element.find_element(By.CLASS_NAME, "gsc_a_y")
                    year = year_element.text.strip() if year_element.text.strip() else "N/A"
                except:
                    year = "N/A"
                
                # Get URL if available
                url = ""
                try:
                    url = title_element.get_attribute("href")
                except:
                    pass
                
                publications.append({
                    'title': title,
                    'authors': authors,
                    'venue': venue,
                    'year': year,
                    'url': url
                })
                
            except Exception as e:
                print(f"Error processing publication: {e}")
                continue
                
    except Exception as e:
        print(f"Error in Selenium scraping: {e}")
    finally:
        driver.quit()
        
    return publications

def scrape_scholar_with_scholarly(author_name):
    """Scrape Google Scholar publications using scholarly library"""
    publications = []
    try:
        # Search for the author
        search_query = scholarly.search_author(author_name)
        author = next(search_query)
        
        # Get their publications
        pubs = scholarly.search_pubs(author_name)
        
        for pub in pubs:
            try:
                publications.append({
                    'title': pub.get('bib', {}).get('title', ''),
                    'authors': pub.get('bib', {}).get('author', ''),
                    'venue': pub.get('bib', {}).get('venue', ''),
                    'year': pub.get('bib', {}).get('pub_year', 'N/A')
                })
            except Exception as e:
                print(f"Error processing publication: {e}")
                continue
                
    except Exception as e:
        print(f"Error in scholarly scraping: {e}")
        
    return publications

def update_html_file(publications, html_file_path):
    """Update the HTML file with new publications"""
    try:
        # Read the existing HTML file
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        if html_file_path == "publication.html":
            # Find the heading - try different variations
            heading = None
            possible_headings = [
                'Journals & Conference Proceedings',
                'Journals & Conference Proceedings\n',
                'Journals &amp; Conference Proceedings',
                'Journals &amp; Conference Proceedings\n',
                'Journals & Conference Proceedings<br>',
                'Journals &amp; Conference Proceedings<br>'
            ]
            
            print("Searching for heading in HTML file...")
            # First try exact matches
            for h in possible_headings:
                heading = soup.find('h2', string=lambda text: text and text.strip() == h.strip())
                if heading:
                    print(f"Found heading: {heading.text}")
                    break
            
            # If no exact match, try partial matches
            if not heading:
                for h2 in soup.find_all('h2'):
                    h2_text = h2.text.strip()
                    if 'Journals' in h2_text and 'Conference' in h2_text:
                        heading = h2
                        print(f"Found heading with partial match: {h2_text}")
                        break
            
            if not heading:
                print("Could not find 'Journals & Conference Proceedings' heading")
                print("Available h2 headings in file:")
                for h2 in soup.find_all('h2'):
                    print(f"- '{h2.text}'")
                return False
                
            # Find the ordered list after the heading
            pub_list = heading.find_next('ol')
            if not pub_list:
                print("Could not find publications list in HTML")
                return False
                
            print(f"Found publications list with {len(pub_list.find_all('li'))} existing items")
            
            # Clear existing publications
            pub_list.clear()
            
            # Add new publications
            for pub in publications:
                li = soup.new_tag('li')
                
                # Add title with red color
                title_span = soup.new_tag('span', attrs={'style': 'color: rgb(153, 0, 0);'})
                title_span.string = pub['title']
                li.append(title_span)
                
                # Add PDF link
                li.append(' [')
                pdf_link = soup.new_tag('a', href=pub.get('url', '#'), target='_blank')
                pdf_link.string = 'pdf'
                li.append(pdf_link)
                li.append(']')
                li.append(soup.new_tag('br'))
                
                # Add authors
                authors = soup.new_tag('span', attrs={'style': 'font-family: Times New Roman;'})
                authors.string = pub['authors']
                li.append(authors)
                li.append(soup.new_tag('br'))
                
                # Add venue and year
                venue = soup.new_tag('span', attrs={'style': 'font-family: Times New Roman,Times,serif;'})
                venue.string = f"{pub['venue']}, {pub['year']}"
                li.append(venue)
                
                pub_list.append(li)
                pub_list.append(soup.new_tag('br'))
            
            print(f"Added {len(publications)} new publications to the list")
                
        else:  # aimslab.html
            # Find the unordered list in the publications section
            pub_list = soup.find('ul', {'style': 'width: 100%; font-family: Times New Roman,Times,serif;'})
            if not pub_list:
                print("Could not find publications list in HTML")
                return False
                
            # Clear existing publications
            pub_list.clear()
            
            # Add new publications
            for pub in publications:
                li = soup.new_tag('li')
                
                # Add title
                title = soup.new_tag('b')
                title.string = pub['title']
                li.append(title)
                li.append(soup.new_tag('br'))
                
                # Add authors
                authors = soup.new_tag('span', attrs={'style': 'font-family: Times New Roman;'})
                authors.string = pub['authors']
                li.append(authors)
                li.append(soup.new_tag('br'))
                
                # Add venue and year
                venue = soup.new_tag('span', attrs={'style': 'font-family: Times New Roman,Times,serif;'})
                venue.string = f"{pub['venue']}, {pub['year']}"
                li.append(venue)
                
                # Add PDF and GitHub links
                li.append(soup.new_tag('br'))
                pdf_link = soup.new_tag('a', href=pub.get('url', '#'), attrs={'style': 'color:brown;'})
                pdf_link.string = '[PDF]'
                li.append(pdf_link)
                li.append(' | ')
                github_link = soup.new_tag('a', href='#', attrs={'style': 'color:brown;'})
                github_link.string = '[View on GitHub]'
                li.append(github_link)
                
                pub_list.append(li)
                pub_list.append(soup.new_tag('br'))
        
        # Write the updated HTML
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"Successfully updated {html_file_path}")
        return True
        
    except Exception as e:
        print(f"Error updating HTML file: {e}")
        return False

def main():
    """Main function to orchestrate the publication update"""
    # Using a default scholar ID
    scholar_id = 'UY1UAKUAAAAJ'  # Default scholar ID
    scholar_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
    author_name = "Sabur Baidya"  # Fallback for scholarly library
    
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
    
    # Update both HTML files
    success1 = update_html_file(publications, "publication.html")
    success2 = update_html_file(publications[:3], "aimslab.html")  # Only update with 3 most recent publications
    
    if success1 and success2:
        print("Publications updated successfully in both files!")
    else:
        print("Failed to update one or both files")
        exit(1)

if __name__ == '__main__':
    main() 