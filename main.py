import image

im = image.sc_Image.from_filepath2("skateboarder.jpg")

im.enlarge(80, alg = 'dyn', orientation = 'vertical')
# image.shrink( 'horizontal', 300 , 'e1', 'dyn')

im.to_jpeg("skateboarder_big.jpg")

