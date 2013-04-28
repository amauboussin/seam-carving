import image

im = image.sc_Image.from_filepath2("comet.jpg")

im.enlarge(2, alg = 'dyn', orientation = 'vertical')
# image.shrink( 'horizontal', 300 , 'e1', 'dyn')

im.to_jpeg("comet_big.jpg")

