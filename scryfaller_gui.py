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
from scryfaller import *
from scryconfig import *
import tkinter as tk
from PIL import ImageTk, Image
from tkinter import filedialog, ttk, messagebox
import pyperclip
import tempfile
import os, platform

__version__ = "1.002b"

ctrlkey = 'Command' if platform.system() == 'Darwin' else 'Control'

# Configuration file
conf = scryConf()

# Some global variables
cardjson = []
imagelist_o = []
imagelist = []
imagetklist = []
imagelabellist = []

def select_all(event):
    """Selects the entire text in the clicked text field."""
    widget = event.widget
    widget.tag_add(tk.SEL, '1.0', 'end-1c')
    widget.mark_set(tk.INSERT, 'end-1c')
    widget.see(tk.INSERT)
    return 'break'

def copy_text(event, cut=False):
    """Copies text from the selected text field to the system clipboard."""
    widget = event.widget
    if widget.selection_get():
        pyperclip.copy(widget.selection_get())
        if cut:
            widget.delete('sel.first', 'sel.last')

    return 'break'

def paste_text(event):
    """Pastes text from the system clipboard to the selected text field."""
    widget = event.widget
    if widget.index(tk.INSERT):
        try:
            widget.delete("sel.first", "sel.last")
        except:
            pass
        widget.insert(tk.INSERT, pyperclip.paste())

    return 'break'

def askdeckdir(txtvar):
    """Initiates a folder selection dialogue and updates the str var 'txtvar'."""
    initdir = os.getcwd()
    if os.path.exists(txtvar.get()):
        initdir = txtvar.get()

    dir = filedialog.askdirectory(initialdir=initdir)
    if dir != '':
        txtvar.set(dir)
    return

def readtxt(textfield):
    """Reads text field content as \n separated array"""
    return str(textfield.get(1.0, tk.END)).strip().split("\n")

def writetxt(textfield, txt):
    """Writes 'txt' into text field, where txt is an string array (w.o. \n)."""
    textfield.delete('1.0', tk.END)
    textfield.insert(tk.END, '\n'.join(txt))
    return textfield

def drawcards(frame, dir, cardnum, df, scale, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Draws card previews with a given scale and stores everything in the appropriate lists."""
    num = 2 * cardnum if df else cardnum
    for i in range(0, num):
        if dir[-1] == os.sep:
            abspath = dir
        else:
            abspath = dir + os.sep

        # for double faced, also load backside
        id = i // 2 if df else i
        name = str(id)
        if df and i % 2 == 1:
            name += 'b'

        imagelist_o.append(Image.open(abspath + name + '.jpg'))
        imgw, imgh = imagelist_o[i].size
        imgw = int(imgw * scale)
        imgh = int(imgh * scale)

        imagelist.append(imagelist_o[i].resize((imgw, imgh), Image.ANTIALIAS))

        imagetklist.append(ImageTk.PhotoImage(imagelist[i]))

        imagelabellist.append(tk.Label(frame, text=str(id), image=imagetklist[i]))
        frame.window_create(tk.END, window=imagelabellist[i])

    return True

def redrawcards(scale, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Redraws contents of the given lists with a given scale."""
    for i in range(0, len(imagelist_o)):
        imgw, imgh = imagelist_o[i].size
        imgw = int(imgw * scale)
        imgh = int(imgh * scale)

        imagelist[i] = imagelist_o[i].resize((imgw, imgh), Image.ANTIALIAS)

        imagetklist[i] = (ImageTk.PhotoImage(imagelist[i]))

        imagelabellist[i]['image'] = imagetklist[i]

    return True

def deletecards(imagelist_o, imagelist, imagetklist, imagelabellist):
    """Removes shown images in the lists and empties them."""
    while len(imagelist_o) > 0:
        imagelist_o.pop()
        imagelist.pop()
        imagetklist.pop()
        imagelabellist.pop().destroy()

    return True

def nextcard(frame, textfield, cardjson, scryconf, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Checks for the next card in the text field and initiates the card previews (if more than one card)."""
    scale = scalew.get()/100

    deletecards(imagelist_o, imagelist, imagetklist, imagelabellist)
    cardname = getfirstname(readtxt(textfield))
    if cardname[1] == '':
        return

    if len(cardjson) > 0:
        cardjson.pop()

    req = cardreq(cardname[1], scryconf)
    if req is None:
        print("Card name not found, will retry with non-strict search")
        req = cardreq(cardname[1], scryconf, strict=False)

    cardjson.append(req)

    df = isdf(cardjson[-1])

    # if only one card, download immediately
    if cardjson[-1]['total_cards'] == 1:
        dlselectcard(0, frame, textfield, cardjson, scryconf, scalew,
                     imagelist_o, imagelist, imagetklist, imagelabellist)
    else:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmppics(cardjson[-1], tmpdirname)
            drawcards(frame, tmpdirname, cardjson[-1]['total_cards'], df, scale,
                      imagelist_o, imagelist, imagetklist, imagelabellist)

        for i in range(0, len(imagelabellist)):
            imagelabellist[i].bind("<ButtonRelease-1>", lambda e : selectcard(
                e, frame, textfield, cardjson, scryconf, scalew, imagelist_o, imagelist, imagetklist, imagelabellist))
        return

def selectcard(event, frame, textfield, cardjson, scryconf, scalew,
               imagelist_o, imagelist, imagetklist, imagelabellist):
    """Triggered when selecting a card image. Passes 'id' to the download function."""
    id = int(event.widget['text'])
    return dlselectcard(id, frame, textfield, cardjson, scryconf, scalew,
                        imagelist_o, imagelist, imagetklist, imagelabellist)

def dlselectcard(id, frame, textfield, cardjson, scryconf, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Downloads the selected card using a fire and forget thread and comments out the corresponding
    entry in the text box."""
    datacard = cardjson[-1]['data'][id]
    df = isdf(cardjson[-1])
    global deckdir
    dir = deckdir.get()
    # pepare path to target folder
    if dir[-1] == os.sep:
        pathsep = dir
    else:
        pathsep = dir + os.sep
    # prepare card name for storage
    cardname = datacard['name'].replace(' ', '_').replace('//', '-')

    urlpatharr = []
    # set up work array
    if df:
        pathsepf = pathsep + cardname + '.png'
        pathsepb = pathsep + cardname + '_back.png'
        urlpatharr.append([datacard['card_faces'][0]['image_uris']['png'], pathsepf])
        urlpatharr.append([datacard['card_faces'][1]['image_uris']['png'], pathsepb])
    else:
        pathsep += cardname + '.png'
        urlpatharr.append([datacard['image_uris']['png'], pathsep])

    downloader = picLoadThread(0, urlpatharr, loadpicarr)
    downloader.start()

    # comment out entry in textbox
    txt = readtxt(textfield)
    txtline, txtname = getfirstname(txt)
    txt[txtline] = '# ' + txt[txtline]
    writetxt(textfield, txt)

    nextcard(frame, textfield, cardjson, scryconf, scalew, imagelist_o, imagelist, imagetklist, imagelabellist)
    return

def vals_from_geometry(geometry):
    """Extracts integer geometry values from geometry string."""
    # Format is e.g. "100x200+10+20"
    txt = geometry
    h = txt.find('x')
    width = int(txt[:h])
    txt = txt[h+1:]
    h = txt.find('+')
    height = int(txt[:h])
    txt = txt[h+1:]
    h = txt.find('+')
    xoffset = int(txt[:h])
    yoffset = int(txt[h+1:])
    return width, height, xoffset, yoffset

def on_close(window, deckdirvar, scalew, scryconf):
    """Save window dimensions and path entry on close."""
    width, height, xoffset, yoffset = vals_from_geometry(window.geometry())
    scryconf.set_window('width', width)
    scryconf.set_window('height', height)
    scryconf.set_window('xoffset', xoffset)
    scryconf.set_window('yoffset', yoffset)
    if platform.system() == 'Windows':
        scryconf.set_window('zoomed', window.state())
    else:
        scryconf.set_window('zoomed', window.attributes('-fullscreen'))
    scryconf.set_window('deckdir', deckdirvar.get())
    scryconf.set_preview('scale', scalew.get())
    scryconf.save()
    window.destroy()

on_close_lambda = lambda : on_close(root, deckdir, imgscale, conf)

#
########################
# ROOT window
root = tk.Tk()
root.title("Scryfall Image Downloader")
rootwidth = conf.get_window('width')
rootheight = conf.get_window('height')
rootxoffset = conf.get_window('xoffset')
rootxoffset = 0 if rootxoffset < 0 else rootxoffset
rootyoffset = conf.get_window('yoffset')
rootyoffset = 0 if rootyoffset < 0 else rootyoffset
root.geometry("{}x{}+{}+{}".format(rootwidth, rootheight, rootxoffset, rootyoffset))
root.minsize("512", "300")

if not (conf.get_window('zoomed') is None):
    if platform.system() == 'Windows':
        root.state(conf.get_window('zoomed'))
    else:
        root.attributes('-fullscreen', conf.get_window('zoomed'))

root.wm_protocol("WM_DELETE_WINDOW", on_close_lambda)

# TOP Frame
fr_top = tk.Frame(root)
fr_top.grid(row=0, column=0, columnspan=2, sticky='nesw', padx=2, pady=2)

# BOTTOM LEFT Frame
fr_botle = tk.Frame(root)
fr_botle.grid(row=1, column=0, sticky="ns")

# BOTTOM RIGHT Frame
fr_botri = tk.Frame(root, bd=1, relief=tk.SOLID, bg="white")
fr_botri.grid(row=1, column=1, sticky="nesw", padx=2, pady=2)

# ROOT WEIGHTS
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)

root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

##
# Menu
##
menu = tk.Menu(root)
root.config(menu=menu)
filemenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=filemenu)
#filemenu.add_command(label="Open")
#filemenu.add_separator()
filemenu.add_command(label="Exit", command=on_close_lambda)

settingsmenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Settings", menu=settingsmenu)
settingsmenu.add_command(label="Edit", command=lambda : settingsdialogue(conf, root.geometry()))

helpmenu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=helpmenu)
helpmenu.add_command(label="About", command=lambda : showabout(__version__))

def showabout(version):
    txt = "Scryfall Downloader v"+version+"\n"
    txt += "Git: marvinlenk/scryfall_downloader\n"
    txt += "Licensed under\nGNU General Public License v3.0"
    messagebox.showinfo("About", txt)
    return

def settingsdialogue(scryconf, geometry):
    rwidth, rheight, rxoffset, ryoffset = vals_from_geometry(geometry)
    width = 500
    height = 200
    xoffset = rxoffset + rwidth // 2 - width // 2
    yoffset = ryoffset + abs(rheight - height) // 2
    window = tk.Toplevel()
    window.geometry("{}x{}+{}+{}".format(width, height, xoffset, yoffset))
    window.minsize(str(450), str(200))
    window.title("Config editor")
    sframe = tk.Frame(window)
    sframe.grid(row=0, column=0)
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    row = 0
    ## Prevtype
    prevtype = tk.StringVar()
    prevtype.set(scryconf.get_preview('prevtype'))
    prevtype_options = ['small', 'normal', 'large']
    prevtype_label = tk.Label(sframe, text="Preview size: ")
    prevtype_label.grid(row=row, column=0)
    prevtype_buttons = []
    columns = 0
    for i in range(0, len(prevtype_options)):
        opt = prevtype_options[i]
        prevtype_buttons.append(
            tk.Radiobutton(sframe, text=opt, value=opt, variable=prevtype))
        prevtype_buttons[-1].grid(row=row, column=2*i + 1, sticky="w")
        tk.Label(sframe, text="").grid(row=row, column=2*i + 2)
        columns += 2
    row += 1

    ## Unique prints
    unique = tk.StringVar()
    uniqueh = scryconf.get_searchflag('unique')
    unique.set(uniqueh if uniqueh != '' else 'false')
    unique_options = [['Yes', 'prints'], ['No', 'false']]
    unique_label = tk.Label(sframe, text="Individual printing: ")
    unique_label.grid(row=row, column=0)
    unique_buttons = []
    for i in range(0, len(unique_options)):
        lab = unique_options[i][0]
        val = unique_options[i][1]
        unique_buttons.append(
            tk.Radiobutton(sframe, text=lab, value=val, variable=unique))
        unique_buttons[-1].grid(row=row, column=2*i + 1, sticky="w")
        tk.Label(sframe, text="").grid(row=row, column=2*i + 2)
        columns += 2 if 2*i + 2 > columns else 0
    row += 1

    ## Game prints
    game = tk.StringVar()
    gameh = scryconf.get_searchflag('game')
    game.set(gameh if gameh != '' else 'any')
    game_options = [['Paper', 'paper'], ['Arena', 'arena'], ['MTGO', 'mtgo'], ['Any', 'any']]
    game_label = tk.Label(sframe, text="Game: ")
    game_label.grid(row=row, column=0)
    game_buttons = []
    for i in range(0, len(game_options)):
        lab = game_options[i][0]
        val = game_options[i][1]
        game_buttons.append(
            tk.Radiobutton(sframe, text=lab, value=val, variable=game))
        game_buttons[-1].grid(row=row, column=2*i + 1, sticky="w")
        tk.Label(sframe, text="").grid(row=row, column=2*i + 2)
        columns += 2 if 2*i + 2 > columns else 0
    row += 1

    ## Language
    lang = tk.StringVar()
    langh = scryconf.get_searchflag('lang')
    langvar = 'selection'
    if langh == '':
        langvar = 'any'
    elif langh == 'en' or langh == 'de':
        langvar = langh
    lang.set(langvar)
    lang_options = [['en', 'en'], ['de', 'de'], ['Any', 'any'], ['Custom:', 'selection']]
    lang_label = tk.Label(sframe, text="Language: ")
    lang_label.grid(row=row, column=0)
    lang_buttons = []
    for i in range(0, len(lang_options)-1):
        lab = lang_options[i][0]
        val = lang_options[i][1]
        lang_buttons.append(
            tk.Radiobutton(sframe, text=lab, value=val, variable=lang))
        lang_buttons[-1].grid(row=row, column=2*i + 1, sticky="w")
        tk.Label(sframe, text="").grid(row=row, column=2*i + 2)
        columns += 2 if 2*i + 2 > columns else 0
    langentryframe = tk.Frame(sframe)
    langentryframe.grid(row=row, column=2*i + 3, stick="w")
    lang_buttons.append(
        tk.Radiobutton(langentryframe, text=lang_options[-1][0], value=lang_options[-1][1], variable=lang))
    lang_buttons[-1].pack(side=tk.LEFT)
    lang_entryvar = tk.StringVar()
    lang_entry = tk.Entry(langentryframe, textvariable=lang_entryvar, width=6)
    if langvar == "selection":
        lang_entryvar.set(langh)
    lang_entry.pack()
    columns += 1 if 2*i+3 > columns else 0
    row += 1

    ## Promo prints
    promo = tk.StringVar()
    promoh = scryconf.get_searchflag('promo')
    promo.set(promoh if promoh != '' else 'any')
    promo_options = [['Yes', 'True'], ['No', 'False'], ['Any', 'any']]
    promo_label = tk.Label(sframe, text="Promo prints: ")
    promo_label.grid(row=row, column=0)
    promo_buttons = []
    for i in range(0, len(promo_options)):
        lab = promo_options[i][0]
        val = promo_options[i][1]
        promo_buttons.append(
            tk.Radiobutton(sframe, text=lab, value=val, variable=promo))
        promo_buttons[-1].grid(row=row, column=2*i + 1, sticky="w")
        tk.Label(sframe, text="").grid(row=row, column=2*i + 2)
        columns += 2 if 2*i + 2 > columns else 0
    row += 1

    def setdefault():
        # Preview
        prevtype.set(scryconf.get_preview('prevtype', default=True))
        # Unique prints
        uniqued = scryconf.get_searchflag('unique', default=True)
        unique.set(uniqued if uniqued != '' else 'false')
        # Game
        gamed = scryconf.get_searchflag('game', default=True)
        game.set(gamed if gamed != '' else 'any')
        # Language
        langd = scryconf.get_searchflag('lang', default=True)
        if langd == '':
            lang.set('any')
        elif langd == 'en' or langd == 'de':
            lang.set(langd)
        else:
            lang.set('selction')
            lang_entryvar.set('')
        # Promo
        promod = scryconf.get_searchflag('promo', default=True)
        promo.set(promod if promod != '' else 'any')

    def closedialogue():
        # Preview
        scryconf.set_preview('prevtype', prevtype.get())
        # Unique prints
        uniqueh = unique.get() if unique.get() != 'false' else ''
        scryconf.set_searchflag('unique', uniqueh)
        # Game
        gameh = game.get() if game.get() != 'any' else ''
        scryconf.set_searchflag('game', gameh)
        # Language
        langh = lang.get()
        if langh == 'any':
            langh = ''
        elif langh == 'selection':
            langh = lang_entryvar.get().strip()
        scryconf.set_searchflag('lang', langh)
        # Promo
        promoh = promo.get() if promo.get() != 'any' else ''
        scryconf.set_searchflag('promo', promoh)
        # Close window
        window.destroy()

    tk.Label(sframe, text="").grid(row=row, column=0)
    buttonframe = tk.Frame(sframe)
    buttonframe.grid(row=row+1, column=0, columnspan=columns)
    button_close = tk.Button(buttonframe, text="Save", command=closedialogue, width=6)
    button_close.pack(side=tk.LEFT, padx=1, pady=1)
    button_close = tk.Button(buttonframe, text="Default", command=setdefault, width=6)
    button_close.pack(side=tk.LEFT, padx=1, pady=1)
    button_close = tk.Button(buttonframe, text="Discard", command=window.destroy, width=6)
    button_close.pack(side=tk.LEFT, padx=1, pady=1)

##
## TOP Stuff
# path to deck folder
tk.Label(fr_top, text="Deck folder:").grid(row=0, column=0, padx=2)

deckdir = tk.StringVar(root)
deckdir.set(conf.get_window('deckdir'))

deckdir_entry = tk.Entry(fr_top, textvariable=deckdir)
deckdir_entry.grid(row=0, column=1, sticky="ew", padx=1)
deckdir_entry.bind('<'+ctrlkey+'-a>', lambda e : e.widget.select_range(0,tk.END))
deckdir_entry.bind('<'+ctrlkey+'-A>', lambda e : e.widget.select_range(0,tk.END))
deckdir_entry.bind('<'+ctrlkey+'-c>', lambda e : copy_text)
deckdir_entry.bind('<'+ctrlkey+'-C>', lambda e : copy_text)
deckdir_entry.bind('<'+ctrlkey+'-v>', lambda e : paste_text)
deckdir_entry.bind('<'+ctrlkey+'-V>', lambda e : paste_text)
deckdir_entry.unbind('<Button-3>')

openbutton = tk.Button(fr_top, text='Open', command=lambda : askdeckdir(deckdir))
openbutton.grid(row=0, column=2, padx=1)

# WEIGHTS
fr_top.grid_columnconfigure(1, weight=1)

##
## BOTTOM LEFT Stuff
# Image size slider
tk.Label(fr_botle, text="Size:").grid(row=0, column=0, stick="sw", pady=2)
imgscale = tk.Scale(fr_botle, from_=15, to=80, orient=tk.HORIZONTAL, showvalue=0, command=lambda x : redrawcards(
        float(x)/100, imagelist_o, imagelist, imagetklist, imagelabellist))
imgscale.set(conf.get_preview('scale'))
imgscale.grid(row=0, column=1, stick="ew", padx=0, pady=1)
imgscale.bind('<ButtonRelease-2>', lambda e: e.widget.set(conf.get_preview('scale', default=True)))
imgscale.bind('<ButtonRelease-3>', lambda e: e.widget.set(conf.get_preview('scale', default=True)))

# Text box
decktext = tk.Text(fr_botle, bd=1, width=34, relief=tk.SOLID)
decktext.grid(row=1, column=0, columnspan=2, stick="nesw", padx=2, pady=1)
decktext.bind('<'+ctrlkey+'-a>', select_all)
decktext.bind('<'+ctrlkey+'-A>', select_all)
decktext.bind('<'+ctrlkey+'-c>', copy_text)
decktext.bind('<'+ctrlkey+'-C>', copy_text)
decktext.bind('<'+ctrlkey+'-v>', paste_text)
decktext.bind('<'+ctrlkey+'-V>', paste_text)
decktext.bind('<'+ctrlkey+'-x>', lambda e : copy_text(e, True))
decktext.bind('<'+ctrlkey+'-X>', lambda e : copy_text(e, True))
decktext.unbind('<Button-3>')

# Buttons
fr_botle_but = tk.Frame(fr_botle)
fr_botle_but.grid(row=2, column=0, columnspan=2, sticky="we", padx=3, pady=3)

quitbutton = tk.Button(fr_botle_but, width=10, text='Quit', command=on_close_lambda)
quitbutton.pack(side=tk.LEFT, padx=1, pady=1)

startbutton = tk.Button(fr_botle_but, width=10, text='Start', command=lambda : nextcard(
    wr_botri, decktext, cardjson, conf, imgscale, imagelist_o, imagelist, imagetklist, imagelabellist))
startbutton.pack(side=tk.RIGHT, padx=1, pady=1)

# WEIGHTS
fr_botle.grid_rowconfigure(1, weight=1)
fr_botle.grid_columnconfigure(1, weight=1)

##
## BOTTOM RIGHT STUFF

# Widget wrapper
wr_botri = tk.Text(fr_botri, wrap="char", borderwidth=0, highlightthickness=0, state="disabled", cursor="arrow")
scrollbar_botri = ttk.Scrollbar(fr_botri, orient="vertical", command=wr_botri.yview)
wr_botri.configure(yscrollcommand=scrollbar_botri.set)

scrollbar_botri.pack(side="right", fill="y")
wr_botri.pack(side="left", fill="both", expand=True)

root.mainloop()
