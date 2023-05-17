import os
import random
import datetime

# where is data stored?
data_dir = '../data/'

# intermediates
tribune_file = os.path.join(data_dir, 'tribune.tsv')
sinclair_file = os.path.join(data_dir, 'sinclair.tsv')
nexstar_file = os.path.join(data_dir, 'nexstar.tsv')
meredith_file = os.path.join(data_dir, 'meredith.tsv')
gray_file = os.path.join(data_dir, 'gray.tsv')
hearst_file = os.path.join(data_dir, 'hearst.tsv')
stationindex_file = os.path.join(data_dir, 'station_index.tsv')
usnpl_file = os.path.join(data_dir, 'usnpl.tsv')

# this is where user entries go!
custom_station_file = os.path.join(data_dir, 'custom_additions.json')

# this is the output!
local_news_dataset_file  = os.path.join(data_dir, 'local_news_dataset_2018.csv') 

def generate_request_header():
  '''
  No input
  Generate headers to mimic a browser while randomly cycling between common use agents
  Return a header object to use for requests
  '''
  # Created July 25, 2022
  user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0"
  ]
  this_user_agent = random.choice(user_agent_list)
  headers = {
    "User-Agent": this_user_agent,
    "Accept-Encoding": "gzip, deflate", 
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
    "DNT":"1",
    "Connection":"close", 
    "Upgrade-Insecure-Requests":"1"
  }
  return headers

# variables
today = datetime.datetime.now()
version = 0



# for normalizing station info.
owner_mapping = {
    'Meredith Corporation' : 'Meredith',
    'Sinclair Broadcast Group' : 'Sinclair',
    'Nexstar Media Group' : 'Nexstar',
    'Hearst Television' : 'Hearst'
}

station_index_mapping = {
    'owner' : 'broadcaster'
}

national = [
    'comettv.com',
    'tbn.org',
    'iontelevision.com',
    'tct-net.org',
    'sbgi.net',
    'daystar.com',
]

look_up = {' Honolulu' : 'HI',
 ' Kalamazoo. MI' : 'MI',
' San Antonio' : 'TX'}

col_standard = {
    'station' : 'name',
    'twitter_name' : 'twitter',
    'geography' : 'state',
    'broadcaster' : 'owner'
}

cols_standard_nexstar = {
    'Web Site' : 'website',
    'Station' : 'station',
    'Affiliation' : 'network'
} 

cols_nexstar = ['station', 'website', 'city', 'state', 'broadcaster', 'source']

cols = ['name', 'state', 'website', 'twitter', 'youtube', 'facebook', 'owner', 'medium', 'source', 'collection_date']
cols_final = ['name', 'state', 'website', 'domain', 'twitter', 'youtube', 'facebook', 'owner', 'medium', 'source', 'collection_date']

# to align nexstar websites to station names
nexstar_alignment = {

    'krqe.com' : [
        'KRQE',
        'KBIM',
        'KREZ',
    ],

    'kwbq.com' : [
        'KWBQ',
        'KASY',
        'KRWB'
    ] ,

    'kark.com' : [
        'KARK',
        'KARZ'
    ],

    'fox16.com' : [
        'KLRT'
    ],

    'cwarkansas.com' : [
        'KASN '
    ],

    'woodtv.com' : [
        'WOOD',
    ],

    'wotv4women.com' : [
        'WOTV',
        'WXSP-CD'

    ],
    
    'wkbn.com' : [
        'WKBN'
    ],
    
    'wytv.com' : [
        'WYTV',
        'WYFX-LD'
    ]  
}

# for USNPL
states = '''ak	  al	  ar	  az	  ca	  co	  ct	  dc	  de	  fl	  ga	  hi	  ia	  id	  il	  in	  ks   ky	  la	  ma	  md	  me	  mi	  mn	  mo	  ms	  mt	  nc	  nd	  ne	  nh	  nj	  nm	  nv	  ny	  oh	  ok	  or	  pa	  ri	  sc	  sd	  tn	  tx	  ut	  va	  vt	  wa	  wi	  wv	  wy	'''
states = [s.strip() for s in states.split('  ')]

# for stationindex
city_state = {
    'New York' : 'NY',
    'Los Angeles' : 'CA',
    'Chicago' : 'IL',
    'Philadelphia' : 'PA',
    'Dallas' : 'TX',
    'Washington, D.C.' : 'DC',
    'Houston' : "TX",
    'Seattle' : 'WA',
    'South Florida' : 'FL',
    'Denver' : 'CO',
    'Cleveland': 'OH',
    'Sacramento' : 'CA',
    'San Diego' : 'CA',
    'St. Louis' : 'MO',
    'Portland' : 'OR',
    'Indianapolis' : 'IN',
    'Hartford' :'CT',
    'Kansas City' :'MO',
    'Salt Lake City' : 'UT',
    'Milwaukee' : 'WI',
    'Waterbury' : 'CT',
    'Grand Rapids' : 'MI',
    'Oklahoma City': 'OK',
    'Harrisburg' : 'VA',
    'Norfolk' : 'VA',
    'Greensboro/High Point/Winston-Salem' : 'NC',
    'Memphis' : 'TN',
    'New Orleans' : 'LA',
    'Wilkes-Barre/Scranton' : 'PA',
    'Richmond' : 'VA',
    'Des Moines' : 'IL',
    'Huntsville' : 'AL',
    'Moline, IL / Davenport, IA' : "IL/IA",
    'Fort Smith' : "AK",
    'America' : 'National'
}

not_actually_local = [
    'variety.com', 'investors.com', 'hollywoodreporter.com', 'bizjournals.com'
]