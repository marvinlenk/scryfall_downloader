# scryfall_downloader

Python based GUI for downloading high resolution images from Scryfall.

Decklists can be pasted to the text box. Supported formats are plain-text outputs of Deckstats, Archidekt and .dec files. Sideboards are **not** supported yet.

By pressing "Start", the first entry of the list will be checked. All possible options will be presented in the bottom right panel. The appropriate card can be chosen by left-clicking the image. Selecting a card will start the download to the specified folder, comment the corresponding entry in the text box and initiate the preview for the next card.
Double-faced cards will be shown as front and back sides side-by-side. If one of the faces is clicked, both sides will be downloaded.

If the request yields only one card, the card is automatically downloaded. This is especially usefull when providing a specific set and/or collector number.

**Basic** lands will take a longer time to preview due to the large number of pictures.