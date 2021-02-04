from scryfaller import *
import tkinter as tk
from PIL import ImageTk, Image
from tkinter import filedialog, ttk
import tempfile
import os

# Some global variables
cardjson = []
imagelist_o = []
imagelist = []
imagetklist = []
imagelabellist = []

def askdeckdir(txtvar):
    initdir = os.path.abspath('./')
    if os.path.exists(txtvar.get()):
        initdir = txtvar.get()

    dir = filedialog.askdirectory(initialdir=initdir)
    if dir != '':
        txtvar.set(dir)
    return

# read textfield as /n separated array
def readtxt(textfield):
    return str(textfield.get(1.0, tk.END)).strip().split("\n")

# write text into text field, where txt is an array separated by lines
def writetxt(textfield, txt):
    textfield.delete('1.0', tk.END)
    textfield.insert(tk.END, '\n'.join(txt))
    return textfield

def nextcard(frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    scale = scalew.get()/100

    deletecards(imagelist_o, imagelist, imagetklist, imagelabellist)
    cardname = getfirstname(readtxt(textfield))
    if cardname[1] == '':
        return

    if len(cardjson) > 0:
        cardjson.pop()
    cardjson.append(cardreq(cardname[1]))

    df = 'card_faces' in cardjson[-1]['data'][0].keys()

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmppics(cardjson[-1], tmpdirname)
        drawcards(frame, tmpdirname, cardjson[-1]['total_cards'], df, scale,
                  imagelist_o, imagelist, imagetklist, imagelabellist)


    for i in range(0, len(imagelabellist)):
        imagelabellist[i].bind("<ButtonRelease-1>", lambda e : selectcard(
            e, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist))
    return

def drawcards(frame, dir, cardnum, df, scale, imagelist_o, imagelist, imagetklist, imagelabellist):
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

        imagelabellist.append(tk.Label(text=str(id), image=imagetklist[i]))
        frame.window_create("end", window=imagelabellist[i])

    return True

def redrawcards(scale, imagelist_o, imagelist, imagetklist, imagelabellist):
    for i in range(0, len(imagelist_o)):
        imgw, imgh = imagelist_o[i].size
        imgw = int(imgw * scale)
        imgh = int(imgh * scale)

        imagelist[i] = imagelist_o[i].resize((imgw, imgh), Image.ANTIALIAS)

        imagetklist[i] = (ImageTk.PhotoImage(imagelist[i]))

        imagelabellist[i]['image'] = imagetklist[i]

    return True

def deletecards(imagelist_o, imagelist, imagetklist, imagelabellist):
    while len(imagelist_o) > 0:
        imagelist_o.pop()
        imagelist.pop()
        imagetklist.pop()
        imagelabellist.pop().destroy()

    return True

def selectcard(event, frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist):
    id = int(event.widget['text'])
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

    # laod picture
    if df:
        urlf = datacard['card_faces'][0]['image_uris']['png']
        urlb = datacard['card_faces'][1]['image_uris']['png']
        pathsepf = pathsep + cardname + '.png'
        pathsepb = pathsep + cardname + '_back.png'
        loadpic(urlf, pathsepf)
        loadpic(urlb, pathsepb)
    else:
        # select correct url
        url = datacard['image_uris']['png']
        pathsep += cardname + '.png'
        loadpic(url, pathsep)

    # comment out entry in textbox
    txt = readtxt(textfield)
    txtline, txtname = getfirstname(txt)
    txt[txtline] = '# ' + txt[txtline]
    writetxt(textfield, txt)

    nextcard(frame, textfield, cardjson, scalew, imagelist_o, imagelist, imagetklist, imagelabellist)
    return

# ROOT window
root = tk.Tk()
root.title("Scryfall image grabber")
root.geometry("1024x700")

bgcolor="grey"

# TOP Frame
fr_top = tk.Frame(root)
fr_top.grid(row=0, column=0, columnspan=2, sticky='nesw')

# BOTTOM LEFT Frame
fr_botle = tk.Frame(root)
fr_botle.grid(row=1, column=0, sticky="ns")

# BOTTOM RIGHT Frame
fr_botri = tk.Frame(root, bd=1, relief=tk.SOLID, bg="white")
fr_botri.grid(row=1, column=1, sticky="nesw")

cv_botri = tk.Canvas(fr_botri)
scrollbar_botri = ttk.Scrollbar(fr_botri, orient="vertical", command=cv_botri.yview)
fr_botri_scr = ttk.Frame(cv_botri)
fr_botri_scr.bind(
    "<Configure>",
    lambda e: cv_botri.configure(
        scrollregion=cv_botri.bbox("all")
    )
)
cv_botri.create_window((0, 0), window=fr_botri_scr, anchor="nw")
cv_botri.configure(yscrollcommand=scrollbar_botri.set)

cv_botri.pack(side="left", fill="both", expand=True)
scrollbar_botri.pack(side="right", fill="y")
fr_botri_scr.pack(fill="both", expand=True)

# ROOT WEIGHTS
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)

root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

##
## TOP Stuff
# path to deck folder
tk.Label(fr_top, text="Deck folder:").grid(row=0, column=0, padx=1)

deckdir = tk.StringVar(root)
deckdir.set(os.path.abspath('./'))

deckdir_entry = tk.Entry(fr_top, textvariable=deckdir)
deckdir_entry.grid(row=0, column=1, sticky="ew", padx=1)

openbutton = tk.Button(fr_top, text='Open', command=lambda : askdeckdir(deckdir))
openbutton.grid(row=0, column=2, padx=1)

# WEIGHTS
fr_top.grid_columnconfigure(1, weight=1)

##
## BOTTOM LEFT Stuff
# Image size slider
tk.Label(fr_botle, text="Size:").grid(row=0, column=0, stick="sw", pady=1)
imgscale = tk.Scale(fr_botle, from_=15, to=80, orient=tk.HORIZONTAL, showvalue=0, command=lambda x : redrawcards(
        float(x)/100, imagelist_o, imagelist, imagetklist, imagelabellist))
imgscale.set(29)
imgscale.grid(row=0, column=1, stick="ew", padx=2, pady=1)

# Text box
decktext = tk.Text(fr_botle, bd=1, width=30, relief=tk.SOLID)
decktext.grid(row=1, column=0, columnspan=2, stick="nesw")

# Buttons
fr_botle_but = tk.Frame(fr_botle)
fr_botle_but.grid(row=2, column=0, columnspan=2, sticky="we", padx=2)

quitbutton = tk.Button(fr_botle_but, width=10, text='Quit', command=root.quit)
quitbutton.pack(side=tk.LEFT)

startbutton = tk.Button(fr_botle_but, width=10, text='Start', command=lambda : nextcard(
    wr_botri, decktext, cardjson, imgscale, imagelist_o, imagelist, imagetklist, imagelabellist))
startbutton.pack(side=tk.RIGHT)

# WEIGHTS
fr_botle.grid_rowconfigure(1, weight=1)
fr_botle.grid_columnconfigure(1, weight=1)

##
## BOTTOM RIGHT STUFF

# Widget wrapper
wr_botri = tk.Text(fr_botri_scr, wrap="char", borderwidth=0,highlightthickness=0,state="disabled", cursor="arrow")
wr_botri.pack(fill="both", expand=True)

wr_botri.bind(
    "<Configure>",
    lambda e: cv_botri.configure(
        scrollregion=cv_botri.bbox("all")
    )
)

root.mainloop()
