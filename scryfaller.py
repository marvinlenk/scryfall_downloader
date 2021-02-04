import requests as req
import urllib.parse
import shutil
import tempfile
import os

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

# Generates json from requested card name
# key 'total_cards' is the length of the data array of individual cards
# key 'data' holds an array with lengt 'total_cards' of cards
# every entry of the list ist another dictionary
# Pic urls are listed in 'image_uris'
def cardreq(card_name, unique='prints', game='paper', order='released'):
    r = req.get(searchapi(card_name, unique, game, order))
    if r.status_code != 200:
        print("Error code " + str(r.status_code))
        return r
    if 'warnings' in r.json().keys():
        print(r.json()['warnings'])
    
    return r.json()

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

    if df:
        for i in range(0, apireq['total_cards']):
            loadpic(data[i]['card_faces'][0]['image_uris'][tp], pathsep + str(i) + ending)
            loadpic(data[i]['card_faces'][1]['image_uris'][tp], pathsep + str(i) + 'b' + ending)
    else:
        for i in range(0, apireq['total_cards']):
            loadpic(data[i]['image_uris'][tp], pathsep + str(i) + ending)

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