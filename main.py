import image

im = image.sc_Image.from_filepath2("comet.jpg")

im.to_energy_pic('comet_energy2.jpg')
im.shrink(50, alg = 'dyn', orientation = 'vertical')
# image.shrink( 'horizontal', 300 , 'e1', 'dyn')

im.to_jpeg("comet_vert.jpg")

