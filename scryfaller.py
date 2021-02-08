"""
Copyright (C) 2021  Marvin Lenk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import requests as req
import urllib.parse
import shutil
import tempfile
import threading
import os

class picLoadThread(threading.Thread):
    """Thread for downloading a picture."""
    def __init__(self, threadID, workarr, func):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.workarr = workarr
        self.func = func
    def run(self):
        self.func(self.workarr)

def isdf(apireq):
    """Checks if card is double faced by searching for 'dfc' in the layout."""
    return 'dfc' in apireq['data'][0]['layout']

def searchapi(card_name, scryconf, strict=None):
    """Generate request url from card name (with additional infos)"""
    # First, look for additional infos in front
    cname, set, cnum = stripinfos(card_name)

    # Set flag - from card name
    set_str = ''
    if set != '':
        set_str = '+set=' + set

    # Collector number flag - from card name
    cnum_str = ''
    if cnum != -1:
        cnum_str = '+cn=' + str(cnum)

    # Uniqueness flag
    unique_str = scryconf.get_searchflag('unique')
    if unique_str != '':
        unique_str = '&unique=' + unique_str

    # Paper printing flag
    game_str = scryconf.get_searchflag('game')
    if game_str != '':
        game_str = '+game=' + game_str

    # Order flag
    order_str = scryconf.get_searchflag('order')
    if order_str != '':
        order_str = '&order=' + order_str

    # Strict name
    card_str = urllib.parse.quote(str(cname))
    if strict is None:
        strict = scryconf.get_searchflag('strict')
    if strict:
        card_str = '!"' + card_str + '"'

    # Language flag
    lang_str = scryconf.get_searchflag('lang')
    if lang_str != '':
        lang_str = '+lang=' + lang_str

    # Promo cards - None allows for promos, True forces promos, False disallows
    promo_str = scryconf.get_searchflag('promo')
    if promo_str != '':
        promo_str = '+' if promo_str == 'True' else '+-'
        promo_str += 'is=promo'

    out = 'https://api.scryfall.com/cards/search?q=' + card_str
    out += game_str + set_str + cnum_str + lang_str + promo_str + order_str + unique_str
    print(out)
    return out

def getjson(url):
    """Files 'url' request to the server and returns json (in dict form)."""
    r = req.get(url)
    if r.status_code != 200:
        print("Error code " + str(r.status_code))
        return None
    if 'warnings' in r.json().keys():
        print(r.json()['warnings'])
    return r.json()

def cardreq(card_name, scryconf, strict=None):
    """Generates json (in dict form) from requested card name (with additional infos).
     The flag 'strict' overrides the conf file entry."""

    # key 'total_cards' is the length of the data array of individual cards
    # key 'data' holds an array with length 'total_cards' of cards
    # every entry of the list ist another dictionary
    # Pic urls are listed in 'image_uris'
    r = getjson(searchapi(card_name, scryconf, strict))

    if r is None:
        return None

    # If more than one page, append data until everything is fetched
    while r['has_more']:
        rt = getjson(r['next_page'])

        if rt['has_more']:
            r['next_page'] = rt['next_page']
        else:
            del r['next_page']
            r['has_more'] = False

        r['data'].extend(rt['data'])

    return r

def loadpic(url, path):
    """Download picture form url to path"""
    rpic = req.get(url, stream=True)
    if rpic.status_code != 200:
        print("Error code " + str(rpic.status_code))
        del rpic
        return False
    
    with open(path, 'wb') as out_file:
        shutil.copyfileobj(rpic.raw, out_file)
        del rpic
    
    return True

def loadpicarr(urlpatharr):
    """Downloads all urls to corresponding paths given in an array."""
    # array structure is [[url, path], [url, path], ...]
    for el in urlpatharr:
        loadpic(el[0], el[1])

    return True

def tmppics(apireq, dir, tp='normal'):
    """Downloads card previews of the json 'apireq' to a folder 'dir' in multiple threads.
    Picture types 'tp' can be 'small', 'normal', 'large', 'png', 'art_crop' and 'border_crop'"""
    data = apireq['data']
    df = isdf(apireq)
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
    """Extract first valid card name from array of strings."""
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
    """Strips as many unnecessary infos from a card name as possible."""
    # dfc is not stripped here due to the bad implementation
    txt = stripnumber(text)
    txt = stripcommander(txt)
    txt = stripfoil(txt)
    return txt

def stripnumber(text):
    """Strips a leading number from a string (including the character after the number)."""
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
    """Strips the commander identification from a string."""
    txt = text.strip()

    # Deckstats format
    if txt.find('#!Commander') != -1:
        txt = txt[:txt.find('#!Commander')].strip()

    # Archidekt format
    if txt.find('[Commander') != -1:
        txt = txt[:txt.find('[Commander')].strip()

    return txt

def stripdfc(text):
    """Returns only the first part of a double-faced card name."""
    txt = text.strip()
    txtar = txt.split('//')
    return txtar[0].strip()

def stripfoil(text):
    """Strips the foil identification from a string."""
    txt = text.strip()

    # Deckstats format
    if txt.find('#!Foil') != -1:
        txt = txt[:txt.find('#!Foil')].strip()

    # Archidekt format
    if txt.find('*F*') != -1:
        txt = txt[:txt.find('*F*')].strip()

    return txt

def stripinfos(text):
    """Extracts set and collector number info from a string and returns the stripped name,
     the set and the collector number."""
    txt = text.strip()
    name = txt
    set = ''
    cnum = -1
    # check if additional infos are given

    # Deckstats format
    # Typical inputs will be '[PZNR] Turntimber Symbiosis // ...' or '[AKH#247] Scattered Groves'
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
    # Typical input will be 'Scattered Grove (akh)'
    if txt[-1] == ')':
        ipos = len(txt) - txt[::-1].find('(')
        set = txt[ipos:-1]
        name = txt[:ipos-1].strip()
    name = stripdfc(name)
    return name, set, cnum

def lineskipcheck(text):
    """Checks if the given text is a comment or to short and should be skipped."""
    return text[0] == '#' or text[0:2] == '//' or len(text) < 3