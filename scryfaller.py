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
    # First, look for additional infos in front
    cname, set, cnum = stripinfos(card_name)

    # Paper printing flag
    game_str = ''
    if game != False:
        game_str = '+game=' + game

    # Set flag
    set_str = ''
    if set != '':
        set_str = '+set=' + set

    # Collector number flag
    cnum_str = ''
    if cnum != -1:
        cnum_str = '+cn=' + str(cnum)

    # Uniqueness flag
    unique_str = ''
    if unique != False:
        unique_str = '&unique=' + unique

    # Order flag
    order_str = ''
    if order != False:
        order_str = '&order=' + order

    out = 'https://api.scryfall.com/cards/search?q=!"'
    out += urllib.parse.quote(str(cname)) + '"'
    out += game_str + set_str + cnum_str + order_str + unique_str
    return out

def getjson(url):
    r = req.get(url)
    if r.status_code != 200:
        print("Error code " + str(r.status_code))
        return None
    if 'warnings' in r.json().keys():
        print(r.json()['warnings'])
    return r.json()

# Generates json from requested card name (with possible additional infos)
# key 'total_cards' is the length of the data array of individual cards
# key 'data' holds an array with length 'total_cards' of cards
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
        name = stripall(txt)
    return line, name

def stripall(text):
    # dfc is not stripped here due to the bad implementation
    txt = stripnumber(text)
    txt = stripcommander(txt)
    txt = stripfoil(txt)
    return txt

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

    # Deckstats format
    if txt.find('#!Commander') != -1:
        txt = txt[:txt.find('#!Commander')].strip()

    # Archidekt format
    if txt.find('[Commander') != -1:
        txt = txt[:txt.find('[Commander')].strip()

    return txt

def stripdfc(text):
    txt = text.strip()
    txtar = txt.split('//')
    return txtar[0].strip()

def stripfoil(text):
    txt = text.strip()

    # Deckstats format
    if txt.find('#!Foil') != -1:
        txt = txt[:txt.find('#!Foil')].strip()

    # Archidekt format
    if txt.find('*F*') != -1:
        txt = txt[:txt.find('*F*')].strip()

    return txt

# Typical inputs can be '[PZNR] Turntimber Symbiosis' or '[AKH#247] Scattered Groves'
def stripinfos(text):
    txt = text.strip()
    name = txt
    set = ''
    cnum = -1
    # check if additional infos are given

    # Deckstats format
    if txt[0] == '[':
        cpos = txt.find(']')
        hpos = txt.find('#')
        # if hashtag is provided, collector num is set
        if hpos != -1:
            i = hpos + 1
            while txt[hpos+1:i+1].isnumeric():
                i += 1
            cnum = int(txt[hpos+1:i])
        else:
            hpos = cpos
        # check if set is actually set or rather collector number
        if txt[1:hpos].isnumeric() and cnum == -1:
            cnum = int(txt[1:hpos])
        else:
            set = txt[1:hpos]
        name = txt[cpos+1:].strip()

    # Archidekt format
    if txt[-1] == ')':
        ipos = len(txt) - txt[::-1].find('(')
        set = txt[ipos:-1]
        name = txt[:ipos-1].strip()
    name = stripdfc(name)
    return name, set, cnum

def lineskipcheck(text):
    return text[0] == '#' or text[0:2] == '//' or len(text) < 3