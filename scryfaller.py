import requests as req
import urllib.parse
import shutil
import tempfile
import threading
import os

class picLoadThread(threading.Thread):
    def __init__(self, threadID, workarr, func):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.workarr = workarr
        self.func = func
    def run(self):
        self.func(self.workarr)

# Generate request url from card name
def searchapi(card_name, unique='prints', game='paper', order='released'):
    # Paper printing flag
    game_str = ''
    if game != False:
        game_str = '+game=' + game
    
    # Uniqueness flag
    unique_str = ''
    if unique != False:
        unique_str = '&unique=' + unique

    # Order flag
    order_str = ''
    if order != False:
        order_str = '&order=' + order 
   
    out = 'https://api.scryfall.com/cards/search?q=!"'
    out += urllib.parse.quote(str(card_name)) + '"'
    out += game_str + order_str + unique_str
    return out

def getjson(url):
    r = req.get(url)
    if r.status_code != 200:
        print("Error code " + str(r.status_code))
        return None
    if 'warnings' in r.json().keys():
        print(r.json()['warnings'])
    return r.json()

# Generates json from requested card name
# key 'total_cards' is the length of the data array of individual cards
# key 'data' holds an array with lengt 'total_cards' of cards
# every entry of the list ist another dictionary
# Pic urls are listed in 'image_uris'
def cardreq(card_name, unique='prints', game='paper', order='released'):
    r = getjson(searchapi(card_name, unique, game, order))

    while r['has_more']:
        rt = getjson(r['next_page'])

        if rt['has_more']:
            r['next_page'] = rt['next_page']
        else:
            del r['next_page']
            r['has_more'] = False

        r['data'].extend(rt['data'])

    return r

# Downloads picture from url to path
def loadpic(url, path):
    rpic = req.get(url, stream=True)
    if rpic.status_code != 200:
        print("Error code " + str(rpic.status_code))
        del rpic
        return False
    
    with open(path, 'wb') as out_file:
        shutil.copyfileobj(rpic.raw, out_file)
        del rpic
    
    return True

# array structure is [[url, path], [url, path], ...]
def loadpicarr(urlpatharr):
    for el in urlpatharr:
        loadpic(el[0], el[1])

    return True

# use with with tempfile.TemporaryDirectory() as tmpdirname:
# tp can be 'small', 'normal', 'large', 'png', 'art_crop', 'border_crop'
def tmppics(apireq, dir, tp='normal'):
    data = apireq['data']
    df = 'card_faces' in data[0].keys()
    if dir[-1] == os.sep:
        pathsep = dir
    else:
        pathsep = dir + os.sep
    ending = '.jpg'

    if tp == 'png':
        ending = '.png'

    ncards = apireq['total_cards']
    # Limit number of threads to 20 (40)
    nthreads = ncards if ncards < 20 else 20
    # Double the number of threads for double faced cards
    nthreads *= 2 if df else 1

    urlpatharr = []

    if df:
        for i in range(0, apireq['total_cards']):
            urlpatharr.append([data[i]['card_faces'][0]['image_uris'][tp], pathsep + str(i) + ending])
            urlpatharr.append([data[i]['card_faces'][1]['image_uris'][tp], pathsep + str(i) + 'b' + ending])
    else:
        for i in range(0, apireq['total_cards']):
            urlpatharr.append([data[i]['image_uris'][tp], pathsep + str(i) + ending])

    threadarr = []
    sllen = len(urlpatharr) // nthreads
    slrest = len(urlpatharr) % nthreads
    sllo = 0
    slhi = sllen
    for i in range(0, nthreads):
        # distribute rest as evenly as possible
        if slrest > 0:
            slhi += 1
            slrest -= 1

        threadarr.append(picLoadThread(i, urlpatharr[sllo:slhi], loadpicarr))
        threadarr[-1].start()
        sllo = slhi
        slhi = sllo + sllen

    for t in threadarr:
        t.join()

    return True

def getfirstname(text):
    name = ''
    line = 0
    while name == '' and line < len(text):
        txt = text[line]
        if lineskipcheck(txt):
            line += 1
            continue
        name = stripnumber(stripcommander(stripdfc(txt)))
    return line, name

def stripnumber(text):
    txt = text.strip()
    i = 1
    check = False
    while i < len(txt):
        if txt[0:i].isnumeric():
            check = True
            i += 1
            continue
        elif check == False:
            return txt
        else:
            # For any reasonable input, expect whitespace or colon after number, so strip this as well
            return txt[i:].strip()
    return ''

def stripcommander(text):
    txt = text.strip()
    if len(txt) > 12:
        if txt[-11] == '#!Commander':
            return txt[:-11].strip()
    return txt

def stripdfc(text):
    txt = text.strip()
    txtar = txt.split('//')
    return txtar[0].strip()

def lineskipcheck(text):
    return text[0] == '#' or text[0:2] == '//' or len(text) < 3