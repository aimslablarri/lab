from scholarly import scholarly
import re
from bs4 import BeautifulSoup
import time

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

def main():
    try:
        publications = get_publications()
        update_html(publications)
        print("Successfully updated publications")
    except Exception as e:
        print(f"Error updating publications: {str(e)}")

if __name__ == '__main__':
    main() 