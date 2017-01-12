from PIL import Image,ImageChops
import Image

import image_slicer
from image_slicer import Tile

from math import sqrt, ceil, floor
import os  
import numpy as np

from scipy.spatial import distance 

def get_average_color(image):
    """ Returns a 3-tuple containing the RGB value of the average color of the
    given image"""
 
    r, g, b = 0, 0, 0
    count = 0
    (x,y)=image.size
    for s in range(x):
        for t in range(y):
            pixlr, pixlg, pixlb = image.getpixel((s, t))
            r += pixlr
            g += pixlg
            b += pixlb
            count += 1
    return ((r/count), (g/count), (b/count))
 
def tint_image(image,size, tint_color):
	return ImageChops.multiply(image,Image.new('RGB', size, tint_color))
	
def slice(im, number_tiles, save=True):
    """
    Split an image into a specified number of tiles. Overwrite slice
    function from image_slicer to take in Image object directly.
    Args:
       im (Image):  Python Image object to be split.
       number_tiles (int):  The number of tiles required.
    Kwargs:
       save (bool): Whether or not to save tiles to disk.
    Returns:
        Tuple of :class:`Tile` instances.
    """
    # image read not required as Image is read outside the fn
    #im = Image.open(filename)
    # validate will limit number_tiles to ~9k
    #image_slicer.validate_image(im, number_tiles) 

    im_w, im_h = im.size
    columns, rows = image_slicer.calc_columns_rows(number_tiles)
    extras = (columns * rows) - number_tiles
    tile_w, tile_h = int(floor(im_w / columns)), int(floor(im_h / rows))

    tiles = []
    number = 1
    for pos_y in range(0, im_h - rows, tile_h): # -rows for rounding error.
        for pos_x in range(0, im_w - columns, tile_w): # as above.
            area = (pos_x, pos_y, pos_x + tile_w, pos_y + tile_h)
            image = im.crop(area)
            position = (int(floor(pos_x / tile_w)) + 1,
                        int(floor(pos_y / tile_h)) + 1)
            coords = (pos_x, pos_y)
            tile = Tile(image, number, position, coords)
            tiles.append(tile)
            number += 1
    if save:
        image_slicer.save_tiles(tiles,
                   prefix=get_basename(filename),
                   directory=os.path.dirname(filename))
    return tuple(tiles)

# Main code starts here

# Input image to be slpit
INPUT = 'data/image.jpg'

# This folder contains sub-images
FOLDER = 'composite'

# These numbers determine the output, start small and experiment

# Number of parts original image is split into
parts = 1024*8
# Original image is blown up by this ratio,to acheive better 
# final resolution
ratio = 5

# Read all sub image files and store in a dict with average color
color_dict ={}
for fn in os.listdir(FOLDER):
	FILENAME = FOLDER+'/'+fn
	print "Reading image " + FILENAME
	im = Image.open(FILENAME)
	color_dict[get_average_color(im)] =im
	

input_im  = Image.open(INPUT)
x,y = input_im.size
input_resized = input_im.resize((x*ratio,y*ratio))

tiles=slice(input_resized,int(parts),False)

# Replace each tile with a close match
for tile in tiles:

	(r, g, b) = get_average_color( tile.image)
	
	# TODO: Find better way to calc euclidean distance
	node = color_dict.keys()[distance.cdist([(r, g, b)], color_dict.keys()).argmin()] 
	sub_im = color_dict[node]
	
	maxsize = tile.image.size
	tb = sub_im.resize(maxsize, Image.ANTIALIAS)
	
	# Tint the sub image with pixel color
	#tb = tint_image(tb,maxsize, (r,g,b,0))
	
	tile.image.paste(tb, None)
	
image_slicer.join(tiles).save(INPUT[:-4]+'_composite.png')
