from scryfaller import *
import tkinter as tk
from PIL import ImageTk, Image
from tkinter import filedialog, ttk
import pyperclip
import tempfile
import os, platform

ctrlkey = 'Command' if platform.system() == 'Darwin' else 'Control'

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
        pos = widget.index(tk.INSERT)
        widget.insert(pos, pyperclip.paste())

    return 'break'

def askdeckdir(txtvar):
    """Initiates a folder selection dialogue and updates the str var 'txtvar'."""
    initdir = os.path.abspath('./')
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

def nextcard(frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Checks for the next card in the text field and initiates the card previews (if more than one card)."""
    scale = scalew.get()/100

    deletecards(imagelist_o, imagelist, imagetklist, imagelabellist)
    cardname = getfirstname(readtxt(textfield))
    if cardname[1] == '':
        return

    if len(cardjson) > 0:
        cardjson.pop()
    cardjson.append(cardreq(cardname[1]))

    df = 'card_faces' in cardjson[-1]['data'][0].keys()

    # if only one card, download immediately
    if cardjson[-1]['total_cards'] == 1:
        dlselectcard(0, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist)
    else:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmppics(cardjson[-1], tmpdirname)
            drawcards(frame, tmpdirname, cardjson[-1]['total_cards'], df, scale,
                      imagelist_o, imagelist, imagetklist, imagelabellist)

        for i in range(0, len(imagelabellist)):
            imagelabellist[i].bind("<ButtonRelease-1>", lambda e : selectcard(
                e, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist))
        return

def selectcard(event, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Triggered when selecting a card image. Passes 'id' to the download function."""
    id = int(event.widget['text'])
    return dlselectcard(id, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist)

def dlselectcard(id, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    """Downloads the selected card using a fire and forget thread and comments out the corresponding
    entry in the text box."""
    datacard = cardjson[-1]['data'][id]
    df = 'card_faces' in datacard.keys()
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

    nextcard(frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist)
    return

# ROOT window
root = tk.Tk()
root.title("Scryfall Image Grabber")
root.geometry("1024x700")

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
## TOP Stuff
# path to deck folder
tk.Label(fr_top, text="Deck folder:").grid(row=0, column=0, padx=2)

deckdir = tk.StringVar(root)
deckdir.set(os.path.abspath('./'))

deckdir_entry = tk.Entry(fr_top, textvariable=deckdir)
deckdir_entry.grid(row=0, column=1, sticky="ew", padx=1)
deckdir_entry.bind('<'+ctrlkey+'-a>', lambda e : e.widget.select_range(0,tk.END))
deckdir_entry.bind('<'+ctrlkey+'-A>', lambda e : e.widget.select_range(0,tk.END))
deckdir_entry.bind('<'+ctrlkey+'-c>', lambda e : pyperclip.copy(deckdir.get()))
deckdir_entry.bind('<'+ctrlkey+'-C>', lambda e : pyperclip.copy(deckdir.get()))
deckdir_entry.bind('<'+ctrlkey+'-v>', lambda e : deckdir.set(pyperclip.paste()))
deckdir_entry.bind('<'+ctrlkey+'-V>', lambda e : deckdir.set(pyperclip.paste()))
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
imgscale.set(36)
imgscale.grid(row=0, column=1, stick="ew", padx=0, pady=1)

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

quitbutton = tk.Button(fr_botle_but, width=10, text='Quit', command=root.quit)
quitbutton.pack(side=tk.LEFT, padx=1, pady=1)

startbutton = tk.Button(fr_botle_but, width=10, text='Start', command=lambda : nextcard(
    wr_botri, decktext, cardjson, imgscale, imagelist_o, imagelist, imagetklist, imagelabellist))
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
