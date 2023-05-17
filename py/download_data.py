import re
import requests
import time

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import pandas as pd
from tqdm import tqdm as tqdm
from bs4 import BeautifulSoup

from config import *

'''
This is a forked version of the original script.

The original script was written by Leon Yin and can be found at NYU's CSMaP.

Updated By Will Dinneen
On 2023-05-16

---
This script contains scrapers for tribune, sinclair, nexstar, hearst, stationindex, and usnpl.

Metadata about the stations in each of the stations is saved as tsvs.

Note that these scrapers are super similar codebases!

Written By Leon Yin
On 2018-05-31
Updated 2018-08-02
'''


def download_tribune():
    '''Scrapes ther Tribune homepage.'''
    def parse_channel_html(channel_html, website=None):
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
        if website == None:
            website = channel_html.find('a').get('href')
        station = channel_html.find('div', class_='q_team_title_holder').find("h3").text
        city = channel_html.find('div', class_='q_team_title_holder').find('span').text
        social = channel_html.find('div', class_='q_team_social_holder')
        network = None
        
        row = dict(
            network = network,
            city = city,
            website = website,
            station = station,
        )

        if social:
            for s in social.find_all('span', class_='q_social_icon_holder normal_social'):
                link = s.find('a').get('href')
                if 'facebook' in link:
                    row['facebook'] = link
                elif 'twitter' in link:
                    row['twitter'] = link
                elif 'youtube' in link:
                    row['youtube'] = link
        return row
    
    print("Downloading Tribune")
    url = 'http://www.tribunemedia.com/our-brands/'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    tables = soup.find_all('div', class_='vc_row wpb_row section vc_row-fluid ')
    channels = soup.find_all('div', class_='wpb_wrapper')

    metadata = []
    for i, channel in tqdm(enumerate(channels)):
        try:
            channel_meta = parse_channel_html(channel)
            metadata.append(channel_meta)
        except:
            try:
                website = channels[i-8].find('a').get('href')
                channel_meta = parse_channel_html(channel, website)
                metadata.append(channel_meta)
            except:
                print(i)

    df = pd.DataFrame(metadata)
    df['broadcaster'] = 'Tribune'
    df['source'] = 'tribunemedia.com'
    df['state'] = df['city'].replace(city_state)
    df['collection_date'] = today
    update = 1
    
    if os.path.exists(tribune_file):
        # appending to old
        df_ = pd.read_csv(tribune_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df)
   
    df.to_csv(tribune_file, index=False, sep='\t')


def download_sinclair():
    '''Scrapes ther Sinclair homepage.'''
    def camel_split(text):
        geo_split = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', text)
        state = geo_split[-1]
        city = ' '.join(geo_split[:-1])
        return city, state

    def parse_channel_html(channel_html):
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
        network = channel_html.get('class')[2]
        city, state = camel_split(channel_html.get('class')[-2])
        website = channel_html.find('a', class_='work-image').get('href')
        if website == 'http://sbgi.net':
            website = None
        station = channel_html.find('span', class_='callLetters').text
        geo = channel_html.find('span', class_='cityState').text.replace(' - ', '')

        row = dict(
            network = network,
            city = city,
            state = state,
            website = website,
            station = station,
            geo = geo
        )

        return row
    
    print("Downloading Sinclair")
    url = 'http://sbgi.net/tv-channels/'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    port = soup.find('div', class_='portfolio')
    channels = port.find_all('div', class_=re.compile('^item five*'))
    metadata = []
    for channel in tqdm(channels):
        try:
            channel_meta = parse_channel_html(channel)
            metadata.append(channel_meta)
        except:
            print(channel)

    df = pd.DataFrame(metadata)
    df['broadcaster'] = 'Sinclair'
    df['source'] = 'sbgi.net'
    df['collection_date'] = today
    
    if os.path.exists(sinclair_file):
        # appending to old
        df_ = pd.read_csv(sinclair_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df) 
        
    df.to_csv(sinclair_file, index=False, sep='\t')


def download_nexstar():
    '''Scrapes ther Nexstar homepage.'''
    def get_geo(row):
        row = row.replace('  (3)', '')
        state = row.split(',')[-1]
        city = row.replace(',' + state, '')

        state = state.strip()
        return city, state
    
    def fix_up_mismatched_stations(row):
        '''
        The table that the Nexstar dataset is scraped from is no aligned.
        This is a way to automate alignment
        '''
        stations = row['station'].split()
        websites = row['website'].split()

        if len(stations) > 1:
            if len(websites) == 1:
                # if there is one website it applies to all the stations
                for station in stations:
                    row_ = row.copy()
                    row_['station'] = station
                    yield row_

            elif len(stations) == len(websites):
                # if the number of websites is equal to that of the stations,
                # we can just align them like this
                for s, w in zip(stations, websites):
                    row_ = row.copy()
                    row_['station'] = s
                    row_['website'] = w
                    yield row_

            else:
                # These are the hardest to align, we make a make a manual mapping
                # and map the correct station to the website
                for w in websites:
                    custom_mapping = nexstar_alignment.get(w)
                    if custom_mapping:
                        for s in custom_mapping:
                            row_ = row.copy()
                            row_['station'] = s
                            row_['website'] = w
                            yield row_
                    else:
                        print(f"{w} is an edge case that needs to be updated on `nexstar_mapping`")
        else:
            yield row
    
    print("Downloading Nexstar")
    url = 'https://www.nexstar.tv/stations/'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    table = soup.find('table', class_='tablepress tablepress-id-1 dataTable no-footer tablepress--responsive')
    df = pd.read_html(str(table))[0]
    df['city'], df['state'] = zip(*df['Market'].apply(get_geo))
    df.columns = [cols_standard_nexstar.get(c, c) for c in df.columns]
    df['broadcaster'] = 'Nexstar'
    df['source'] = 'nexstar.tv'
    df = df[cols_nexstar]
    df['collection_date'] = today
    
    # align stations and websites! many to one relationship per row...
    data = []
    for i, row in df.iterrows():
        for _ in fix_up_mismatched_stations(row):
            data.append(_)
    df = pd.DataFrame(data)
    
    if os.path.exists(nexstar_file):
        # appending to old
        df_ = pd.read_csv(nexstar_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df) 
        
    df.to_csv(nexstar_file, sep='\t', index=False)
    

def download_meredith():
    '''Scrapes ther Meredith homepage.'''
    def parse_channel_html(channel_html):
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
        station = channel_html.get('data-station-name')
        geo = channel_html.find('div', class_='city').text
        city, state = geo.split(', ')
        website = channel_html.find('div', class_='links').find('a').get('href')
        try:
            facebook = channel_html.find('a', class_='icon-FACEBOOK icon').get('href')
        except:
            facebook = None
        try:
            google = channel_html.find('a', class_='icon-GOOGLE icon').get('href')
        except:
            google = None
        try:
            twitter = channel_html.find('a', class_='icon-TWITTER icon').get('href')
        except:
            twitter = None 

        data = dict(
            station = station,
            city = city,
            state = state,
            website = website,
            network = None,
            facebook = facebook,
            twitter = twitter,
            google = google
        )

        return data
    
    print("Downloading Meredith")
    url = 'http://www.meredith.com/local-media/broadcast-and-digital'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    channels = soup.find_all('li', class_=re.compile('^dot station-id-*'))
    metadata = []
    for i, channel in tqdm(enumerate(channels)):
        channel_meta = parse_channel_html(channel)
        metadata.append(channel_meta)
    df = pd.DataFrame(metadata)
    df['broadcaster'] = 'Meredith'
    df['source'] = 'meridith.com'
    df['collection_date'] = today
    
    if os.path.exists(meredith_file):
        # appending to old
        df_ = pd.read_csv(meredith_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df) 
        
    df.to_csv(meredith_file, index=False, sep='\t')


def download_hearst():
    '''
    Downloads metadata about Hearst newspapers and broadcasting channels.

    The final DataFrame includes details such as website, name, address, phone, Twitter, Facebook, LinkedIn, 
    Instagram, station name (for broadcasting channels), broadcaster (set as "Hearst"), source (set as 
    "https://www.hearst.com/"), and collection date.

    Note: The function requires the requests, BeautifulSoup, and pandas libraries.

    Parameters:
    None

    Returns:
    None
    '''
    
    # Parse the broadcasting channels
    def parse_channel_html(channel_html):
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
        website_tag = channel_html.find('a')

        # Sometime there are brand-cards that don't have any metadata attached
        if website_tag is not None:
            website = website_tag.get('href')
        else:
            return None
        
        # Extract station name from alt-text
        img_container = soup.find('div', class_='brand-logo-caption-with-text')
        image_element = img_container.find('img')
        station = alt_text = image_element['alt']

        context = dict(
            website = website,
            station = station,
            name = station,
            phone = "",
            address = "",
            twitter = "",
            facebook = "",
            linkedin = "",
            instagram = ""
        )

        return context
    
    
    # Parse the newspaper pages
    def parse_newspaper_html(newspaper_html):        
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
        
        href = newspaper_html.find('a').get('href')
        sub_r = requests.get(f'https://www.hearst.com{href}', headers=headers)
        sub_soup = BeautifulSoup(sub_r.content, 'lxml')
        
        # Extract newspaper information
        data_section = sub_soup.find('section', id='content')
        name = data_section.find("h1").text.strip()
        
        main_column = data_section.find('div', id='layout-column_column-1')
        column_divs = main_column.find_all('div', recursive=False)

        contact_info = column_divs[2].find('div', class_="brand-contact-info")
        website = contact_info.find('p', class_="brand-address").find('a').get('href')
        
        address_info = column_divs[2].find('div', class_='address-container')
        address_list = [p.text.strip() for p in address_info.find_all('p')]
        phone = address_list[-1]
        address = ' '.join(address_list[:-1])
            
        social_info = column_divs[2].find('ul', class_="brand-icons")
        twitter = ''
        facebook = ''
        linkedin = ''
        instagram = ''
        for link in social_info.find_all('a'):
            img_alt = link.find('img')['alt']
            href = link['href']
            if 'twitter' in img_alt.lower():
                twitter = href
            elif 'facebook' in img_alt.lower():
                facebook = href
            elif 'linkedin' in img_alt.lower():
                linkedin = href
            elif 'instagram' in img_alt.lower():
                instagram = href
        
        column_divs[2]

        context = dict(
            website = website,
            name = name,
            address = address,
            phone = phone,
            twitter = twitter,
            facebook = facebook,
            linkedin = linkedin,
            instagram = instagram,
            station = ""
        )

        return context
    
    # -- -- -- -- -- -- -- -- -- -- -- -- --
    
    print("Downloading Hearst")
    broadcasting_url = "https://www.hearst.com/broadcasting"
    newspaper_url = "https://www.hearst.com/newspapers"
    
    # Get broadcasting data
    r = requests.get(broadcasting_url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    parent_div = soup.find('div', class_='brand-card')
    channels = parent_div.find_all('div', recursive=False)
    channel_metadata = []
    for channel in channels:
        channel_meta = parse_channel_html(channel)
        if channel_meta is not None:
            channel_metadata.append(channel_meta)
    
    # get newspaper data
    r = requests.get(newspaper_url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    parent_div = soup.find('div', class_='brand-card')
    newspapers = parent_div.find_all('div', recursive=False)
    newspaper_metadata = []
    for newspaper in newspapers:
        newspaper_meta = parse_newspaper_html(newspaper)
        newspaper_metadata.append(newspaper_meta)  
    
    broadcast_df = pd.DataFrame(channel_metadata)
    newspaper_df = pd.DataFrame(newspaper_metadata)
    
    df = pd.concat([broadcast_df, newspaper_df])
    
    df['broadcaster'] = 'Hearst'
    df['source'] = 'https://www.hearst.com/'
    df['collection_date'] = today
    
    if os.path.exists(hearst_file):
        # appending to old
        df_ = pd.read_csv(hearst_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df) 
    
    df.to_csv(hearst_file, index=False, sep='\t')

    
def download_stationindex():
    '''
    stationindex has metadata about many tv stations in different states.
    '''
    def parse_station(row):
        '''Parses bs4 html to create a dictionary (row in the dataset)'''
                
        station_name = row.find_all('td')[1].find('a').text
        spans = row.find('td', attrs={'width':'100%'}).find_all('span', attrs={"class":'text-bold'}) 
        row = {'station' : station_name}
        for span in spans:
            # each span becomes a different column:
            col_name = span.text.rstrip(':').strip(' ').replace(' ', '_').lower().replace('web_site', 'website')
            val = span.next_sibling
            if col_name == 'website':
                # this needs to be validateed, 
                # there are some incorrect strings being passed as URLs
                val = val.next_sibling.text
            if col_name == 'city':
                state = val.split(', ')[-1]
                val = val.split(', ')[0]
                row['state'] = state
            row[col_name] = val

        return row
    
    print("Downloading StationIndex")
    tv_markets = [
        'http://www.stationindex.com/tv/tv-markets',
        'http://www.stationindex.com/tv/tv-markets-100'
    ]

    market_urls = []
    for url in tv_markets:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')
        table = soup.find('table', attrs={'class' : 'table table-striped table-condensed'})
        urls = ['http://www.stationindex.com' + _.get('href') for _ in table.find_all('a')]
        market_urls.extend(urls)

    data = []
    for url in tqdm(market_urls):
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')
        rows = soup.find_all('tr')
        data.extend([parse_station(row) for row in rows])     

    df = pd.DataFrame(data)
    df['source'] = 'stationindex'
    df['collection_date'] = today

    if os.path.exists(stationindex_file):
        # appending to old
        df_ = pd.read_csv(stationindex_file, sep='\t')
        df = df[~df['station'].isin(df_['station'])]
        df = df_.append(df) 
        
    df.to_csv(stationindex_file, index=False, sep='\t')

    
def download_usnpl():
    '''
    Retrieves metadata about newspapers in different states from the usnpl.com website
    and saves the information in a CSV file.

    Parses the HTML response to extract newspaper information when available (state, city, name,
    website, Twitter, Facebook, Instagram, YouTube, address, editor, and phone number.

    Note: The function requires the `requests`, `BeautifulSoup`, and `pandas` libraries.

    Parameters:
        None

    Returns:
        None
    '''

    sites = []
    
#    for state in states:
    for state in states:
        url = f'https://www.usnpl.com/search/state?state={state}'
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')
        
        main_table = soup.find('table', class_='table table-sm')
        
        if main_table:
            rows = main_table.find_all('tr')
            # Remove non-data rows
            rows = [row for row in rows if 'table-dark' not in row.get('class', [])]
            current_city = ""
            for row in rows:
                city_element = row.find('h4', class_='result_city')
                if city_element:
                    current_city = city_element.text.strip()
                    continue
                # Extract data From the row
                data_points = row.find_all('td')
                if len(data_points) >= 6:
                    newspaper_name = data_points[0].find('a').text.strip() if data_points[0].find('a') else ''
                    usnpl_page = data_points[0].find('a')['href'] if data_points[0].find('a') else ''
                    website = data_points[1].find('a')['href'] if data_points[1].find('a') else ''
                    twitter = data_points[2].find('a')['href'] if data_points[2].find('a') else ''
                    facebook = data_points[3].find('a')['href'] if data_points[3].find('a') else ''
                    instagram = data_points[4].find('a')['href'] if data_points[4].find('a') else ''
                    youtube = data_points[5].find('a')['href'] if data_points[5].find('a') else ''
                else:
                    continue

                # Extract Data From the Newspaper Page
                sub_url = f"https://www.usnpl.com/search/{usnpl_page}"
                r = requests.get(sub_url, headers=headers)
                sub_soup = BeautifulSoup(r.content, 'lxml')
                sub_table = sub_soup.find_all('tr')
                address_element = sub_table[1]
                address_parts = [part.strip() for part in address_element.stripped_strings]
                address = ' '.join(address_parts)
                editor = sub_soup.find('strong', text='Editor:').find_next_sibling(text=True).strip()
                phone = sub_soup.find('strong', text='Phone:').find_next_sibling(text=True).strip()

                # Parsed Object
                parsed_object = {
                    "State": state,
                    "City": current_city,
                    "Name": newspaper_name,
                    "Website": website,
                    "Twitter": twitter,
                    "Facebook": facebook,
                    "Instagram": instagram,
                    "Youtube": youtube,
                    "Address": address,
                    "Editor": editor,
                    "Phone": phone
                }
                
                # Add to the list
                sites.append(parsed_object)

    df = pd.DataFrame(sites)
    df['Website'] = df['Website'].str.rstrip('/')
    df['source'] = 'usnpl.com'
    df['collection_date'] = today
    
    if os.path.exists(usnpl_file):
        # appending to old
        df_ = pd.read_csv(usnpl_file, sep='\t')
        df = df[~df['Name'].isin(df_['Name'])]
        df = df_.append(df) 
    
    df.to_csv(usnpl_file, index=False, sep='\t')

    print(df)
    
    
def download_all_datasets():
    '''
    Downloads datasets from the 7 sources.
    '''
    download_hearst()
    download_meredith()
    download_nexstar()
    download_sinclair()
    download_tribune()
    download_stationindex()
    download_usnpl()
    
if __name__ == "__main__":
    download_all_datasets()
    