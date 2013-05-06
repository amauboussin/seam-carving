import energy
from seams import seam_dijk, seam_dyn
from random import randrange

import copy
import Image

# Grayscales the image so that we can run energy calculations on it
def to_grayscale (img):

    return img.convert("L")

# creates image sc object from python image library representation of a picture
def from_pil (im):

    this_id = 0
    pixels = {}
    width, height = im.size
    data = im.getdata()
    for w in range (width):
        for h in range (height):

            color = data[ h * width + w]
            #we are working with a color image for the normal picture and have an rgb tuple
            if isinstance (color, tuple) :
                pixels[(w,h)] = Pixel( (w,h), color  )
                this_id += 1

            #we are working with a grayscale image for the energy picture and an int
            elif isinstance (color, int) :
                pixels[(w,h)] = Pixel( (w,h), (0,0,0), gray = color  )
    return pixels, width, height

# representation of an image for seam carving with all the methods encapsulating critical
# functions to seam generation
class sc_Image:
    def __init__(self, dimensions, pixels, PIL): 
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.pixels = pixels
        self.dim = 3
        self.PIL = PIL
    
    # @classmethod
    # def from_filepath(cls, filepath):
    #     """ Given an image file turns into an sc_Image class.
    #     eventually replace the im.getpixels calls with an im.getdata for performance reasons
    #     """

    #     pixels = {}
    #     im = Image.open (filepath)
    #     width, height = im.size
    #     for h in range(height):
    #         for w in range(width):
    #             pixels[(w,h)] = Pixel( (w,h), im.getpixel((w,h)) )
    #     return cls ((width, height), pixels, im)       
    

    #BEGINNING OF PUBLIC METHODS

    #Given an image file turns into an sc_Image class.
    #Replaced the im.getpixels calls with an im.getdata for performance reasons
    @classmethod
    def from_filepath (cls, filepath):

        print 'converting to object'
        im = Image.open (filepath)
        pixels, width, height = from_pil(im)

        print 'calculating energies'
        return cls ((width, height), pixels, im)


    #write a jpeg representation of this image to a file
    def to_jpeg (self, filepath):

        data = [(0,0, 0)] * (self.width * self.height)
        for w in range (self.width):
            for h in range(self.height):
                # print "(%s, %s); (%s, %s)" % (w,h, self.width, self.height)
                data[h*self.width + w] = self.pixels[(w,h)].rgb
        im = Image.new("RGB", (self.width, self.height))
        im.putdata(data)
        im.save(filepath, "JPEG")


    # shrinks a picture by continouslly removing the lowest energy seem
    def shrink (self, to_remove, orientation = "vertical", energy = 'sobel', alg = 'dyn'):

        self.validate_number_of_seams(to_remove, orientation)
        if orientation == 'horizontal' :
            self.transpose()
        counter = 0
        for i in range(to_remove) :
            counter += 1
            self.set_energies (energy)
            seam = self.remove_seam_vert2 (alg)
            print "Removed %d seams" % (counter)
        if orientation == 'horizontal' :
            self.transpose() 


    #calculate the lowest energy seams then add duplicates of them to the picture
    def enlarge (self,  new_pixels, orientation = 'vertical', energy = 'e1', alg = 'dyn', inverse=False):

        self.validate_number_of_seams(new_pixels, orientation)

        if orientation == 'horizontal' :
            self.transpose()

        original_pixels = copy.deepcopy(self.pixels)
        original_width =self.width
        original_height = self.height
        seams = self.get_n_seams(new_pixels, energy, alg, inverse)

        print "Enlarging image..."

        self.width = original_width
        self.height = original_height
        for s in seams:
            self.insert_seam(original_pixels, s)
        self.pixels = original_pixels

        if orientation == 'horizontal' :
            self.transpose()


    # one dimensional implementation of which operates to resize all high energy objects by shrinking the
    # background around them and inverting and enlarging the objects in the new background, 
    # writing the new image to an output file
    def enlarge_object_1d (self, new_pixels, orientation="vertical", energy='sobel', alg='dyn'):

         self.shrink(new_pixels,orientation,energy,alg)
         self.enlarge(new_pixels,orientation,energy,alg,True)


    # two dimensional implementation of object enlargement, which grows the object in two dimensions
    # by them same method writing the new image to an output file
    def enlarge_object(self, seams, energy = 'sobel', alg = 'dyn'):

        self.shrink(seams/2, 'vertical', energy, alg)
        self.shrink(seams/2, 'horizontal', energy, alg)

        self.enlarge(seams/2, 'vertical', energy, alg)
        self.enlarge(seams/2, 'horizontal', energy, alg)


    #remove an object that has been painted over with a color with rgb value "rgb".
    #tolerance specifies how closely a pixel must match "rgb" to be removed
    def remove_object(self,rgb, tolerance = 5, energy = 'sobel', alg = 'dyn'):

         # compare the rgb values for two pixels to check for changes is coleration
         # denoting the start of an object
        def check_rgb(self, rgb1, rgb2, tolerance):
            r1,g1,b1 = rgb1
            r2,g2,b2 = rgb2
            return (r2-tolerance < r1 < r2+tolerance and  
                g2-tolerance < g1 < g2+tolerance and b2-tolerance < b1 < b2+tolerance )

        max_width = 0
        for h in range(self.height): 
            width = 0
            for w in range(self.width):
                if self.check_rgb(self.pixels[(w,h)].rgb, rgb, tolerance):
                    self.pixels[(w,h)].energy = -99999999999
                    self.pixels[(w,h)].to_remove = True
                    self.pixels[(w,h)].recalculate = False
                    width += 1
            if width > max_width:
                max_width = width

        self.shrink(max_width, energy = energy, alg = alg )

        #fix the original positions for enlargement
        for h in range(self.height): 
            for w in range(self.width):
                self.pixels[(w,h)].original_pos = self.pixels[(w,h)].pos
        
        self.enlarge(max_width, energy = energy, alg = alg)


    #Uses the grayscale of the image to get an energy map
    def to_energy_pic (self, filepath, energy = 'sobel'):

        original_pixels = self.pixels
        gray_pixels, w, h = from_pil (to_grayscale(self.PIL))
        self.pixels = gray_pixels
        self.set_energies(energy)

        data = [0] * (self.width * self.height)
        for w in range (self.width):
            for h in range(self.height):
                data[h*self.width + w] = self.pixels[(w,h)].energy
        im = Image.new("L", (self.width, self.height))
        im.putdata(data)
        im.save(filepath, "JPEG")

        self.pixels = original_pixels

    # creates an images that higlights all discovered seams in red during a standard removal process, on the original picture and 
    # writes the new hilighted image to the specified file path 
    def to_seam_pic (self, filepath, n, energy = 'sobel', alg = 'dyn', orientation = 'vertical'):

        if orientation == 'horizontal' :
            self.transpose()

        original_pixels = copy.deepcopy(self.pixels)
        original_width = self.width
        original_height = self.height
        
        seams = self.get_n_seams(n, energy, alg)

        to_color = []
        for seam in seams:
            to_color.append(map (lambda p : p.original_pos , filter(None,seam )))
        

        for seam in to_color:
            for pos in seam:
                original_pixels[pos].rgb = (300,0,0)

        self.pixels = original_pixels
        self.width = original_width
        self.height = original_height

        if orientation == 'horizontal' :
            self.transpose()

        self.to_jpeg(filepath)

    #END OF PUBLIC METHODS


    # gets neigbors to pixel at given position in image in form of pixle list
    def get_neighbors_simple (self, pos, pixels):

        x, y = pos
        data = []
        for j in range(y+(self.dim/2), y-(self.dim/2+1), -1):
            for i in range(x-(self.dim/2),x+(self.dim/2+1)):
                try:
                    data.append(pixels[(i,j)])
                except KeyError:
                    data.append(None)
        return data


    # flags neigboring pixles to pixle being removed so they can be recalculated by energy algorithm 
    def recalculate_neighbors(self, pos):

        for p in self.get_neighbors_simple (pos, self.pixels):
            if p is not None:
                p.to_recalculate()


    # gets the dim x dim square of pixels of the pixel at pos for energy functions
    def get_neighbors (self, pos, pixels):

        data = self.get_neighbors_simple(pos, pixels)

        if (self.dim == 3):
            edge_replace = {0 : [2,6,8], 1 : [7], 2 : [0,8,6],
            3 : [5], 5 : [3], 6 : [0,8,2],  7 : [1], 8 : [2,6,0]}

            for i in range(len(data)):
                if data[i] is None:
                    for replace_with in edge_replace[i] : 
                        if data[replace_with] is not None:
                            data [i] = data [replace_with]
                            break
        return data


    # gets pixel object at given postion
    def get_pixel(self, pos):

        if pos in self.pixels:
            return self.pixels[pos]
        else:
            return None


    # makes a pixel dictionary of the mirror reflection of the image and retunrs it
    def make_mirror_dic (self) :

        marg = self.dim/2
        temp_pix = self.pixels

        for h in range(-marg, 0) + range(self.height, self.height + marg): 
            for w in range(self.width):
                if h < 0 :
                    temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(w, 0)].gray )
                else :
                    temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(w, self.height -1)].gray )

        for w in range(-marg, 0) + range(self.width, self.width + marg): 
            for h in range(- marg, self.height + marg):
                if w < 0:
                    if h < 0:
                        temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(0,0)].gray )
                    elif h >= self.height:
                        temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(0,self.height-1)].gray )
                    else:
                        temp_pix[(w,h)] = Pixel((w,h), (w,h), self.pixels[(0, h)].gray )
                else:
                    if h < 0:
                        temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(self.width-1,0)].gray )
                    elif h >= self.height:
                        temp_pix[(w,h)] = Pixel( (w,h), (w,h), self.pixels[(self.width-1,self.height-1)].gray)
                    else:
                        temp_pix[(w,h)] = Pixel((w,h), (w,h), self.pixels[(self.width-1, h)].gray)
        return temp_pix


    # sets the energies of each pixel using the specified algorithm
    def set_energies (self, algorithm = 'sobel') :

        #map the energy calculating function to the pixel objects
        #print self.pixels[(127,107)

        def set_energy_e1_Sobel (pixel):
            if pixel.recalculate :
                return energy.Sobel_op (pixel, self.get_neighbors (pixel.pos,self.pixels) )
            else :
                return pixel

        def set_energy_e1_Scharr (pixel):
            if pixel.recalculate :
                return energy.Scharr_op (pixel, self.get_neighbors (pixel.pos,self.pixels) )
            else :
                return pixel
            
        def set_energy_e1_Kroon (pixel):
            if pixel.recalculate :
                return energy.Kroon_op (pixel, self.get_neighbors (pixel.pos,self.pixels) )
            else :
                return pixel

        def set_energy_e1_Sobel_5 (pixel, pixels) :
            if pixel.recalculate :
                return energy.Sobel_five_op (pixel, self.get_neighbors (pixel.pos, pixels) )
            else :
                return pixel
            
        def set_energy_e1_Scharr_5 (pixel, pixels) :
            if pixel.recalculate :
                return energy.Scharr_five_op (pixel, self.get_neighbors (pixel.pos, pixels) )
            else :
                return pixel

        def set_energy_entropy(pixel, pixels):
            if pixel.recalculate :
                return energy.entropy (pixel, self.get_neighbors (pixel.pos,self.pixels) )
            else :
                return pixel

        #print 'p127-0 is None ', ( self.pixels[(127,0)] is None)
        self.dim = 3
        if algorithm == 'sobel':
            map (set_energy_e1_Sobel ,self.pixels.values() )

        elif algorithm == 'scharr':
            map (set_energy_e1_Scharr ,self.pixels.values() )

        elif algorithm == 'kroon':
            map (set_energy_e1_Kroon ,self.pixels.values() ) 

        elif (algorithm == 'sobel5' or algorithm == 'scharr5'):
            self.dim = 5
            temp_pix = self.make_mirror_dic()

            for h in range(self.height):
                for w in range(self.width):
                    if algorithm == 'sobel5':
                        set_energy_e1_Sobel_5( self.pixels[(w,h)], temp_pix )
                    if algorithm == 'scharr5':
                        set_energy_e1_Scharr_5( self.pixels[(w,h)], temp_pix )

        elif algorithm == 'entropy':
            self.dim = 9
            temp_pix = self.make_mirror_dic()
            for h in range(self.height):
                for w in range(self.width):
                    set_energy_entropy( self.pixels[(w,h)], temp_pix) 

        else:
            raise Exception("%s is not one of the implemented algorithms" % algorithm)


    # If resize is vertical, then calls seam_for_start_vert on every 
    # pixel at the left edge of the image and finds the lowest.
    # If resize is horizontal, then calls seam_for_start_hor on every
    # pixel at the top edge of the image and finds the lowest.
    def get_next_seam (self, alg ) :

        #get all of the starting pixel
        if alg == 'dijk' :
            return seam_dijk(self)
        else :
            return seam_dyn(self)
        return seam

    
    # gets the leftmost verical row in ordered list
    def top_vert_row (self) :

        return map (self.get_pixel, [(0,h) for h in range(self.height)] )


    # gets the top horizonal row of pixles in ordered list
    def top_horz_row (self) :

        return map (self.get_pixel, [(w,0) for w in range(self.width)] )


    # removes vertical seams from the image after discovery
    def remove_seam_vert2 (self, alg, return_pixels = False):

        seam = self.get_next_seam(alg)

        #print "To be removed: ",seam

        to_remove = seam

        # copy all pixels to return later if needed

        #try making new ones instead of deep copy
        if return_pixels:
            pixels = map( lambda p : copy.deepcopy (self.get_pixel(p)), seam)
        else:
            pixels = []

        #to_remove = map ( lambda p:  p.pos , filter(None, seam))

        for h in range(self.height):
            decrement = False
            for w in range (self.width):
                if not decrement:
                    if (w,h) in to_remove:
                        decrement = True
                        self.recalculate_neighbors((w,h))

                else:
                    self.pixels[(w,h)].shift_pos(-1,0)
                    self.pixels[(w-1,h)] = self.pixels[(w,h)]

            del self.pixels[self.width-1, h]

        self.width -= 1

        return pixels


    #debugging function that makes sure self.pixels is consistent
    def check_for_mismatch(self):
        for h in range(self.height): 
            for w in range (self.width): 
                if self.pixels[(w,h)].pos != (w,h) :
                    print 'mismatch at ', w, h, "-- ",self.pixels[(w,h)].pos

    #debugging function that checks self.pixels for None types
    def check_for_none(self):
        for h in range(self.height): 
            for w in range (self.width):
                if self.pixels[(w,h)] is None:
                    print "(%s, %s) is None" % (w,h)

    # copies back in a remembered seam for enlargement
    def insert_seam(self,pixels, seam):

        for pixel in seam:
            h = pixel.pos[1]

            for w in range (self.width-1, -1, -1):
                if pixel.original_pos == (w,h):
                    pixel.pos = (w+1,h)
                    pixels[(w+1,h)] = pixel
                    #update rgb value
                    left = pixels[(w,h)].rgb

                    if (w+2,h) in pixels:
                        right = pixels[(w+2,h)].rgb
                    else :
                        right  = pixel.rgb

                    pixel.rgb = self.average_rbg(left, right)
                    break

                else :
                    pixels[(w,h)].shift_pos(1,0)
                    pixels[(w+1,h)] = pixels[(w,h)]

        self.width += 1
        return pixels


    # averages the coler of two rgbs from pixels
    def average_rbg(self, rgb1, rgb2):

        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2

        return ((r1+r2)/2, (g1+g2)/2, (b1+b2)/2)

    # finds n seams for image enlargement, and returns thems as a list of pixle lists
    def get_n_seams(self,n, energy, alg,  inverse=False) :

        seams = []
        for i in range(n):
            self.set_energies(energy)
            if inverse:
                self.invert_energies()
            seam = self.remove_seam_vert2(alg, return_pixels = True)
            seams.append( seam )

            print "Got %d seams" % (i+1)
        
        return seams

    #  inverts all the energies in the image to preform backgrounds aware resizing of objetcs in
    # methods like object enlargement
    def invert_energies(self):

        for w in range (self.width):
            for h in range(self.height):
                self.pixels[(w,h)].energy*=-1


    # a small input validation function to ensure there are not an illegal amoount of seams being removed
    def validate_number_of_seams(self, n, orientation):

        if orientation == 'vertical':
            if not (0 < n <= self.width):
                raise Exception("Number of seams to remove must be greater than 0 and less than the image width %d" % (self.width))
        
        elif orientation == 'horizontal' :
            if not (0 < n <= self.height):
                raise Exception("Number of seams to remove must be greater than 0 and less than image height %d" % (self.height))           

        else :
            raise Exception("Orientation must be 'vertical' or 'horizontal' ")


    # transposes the image by manipulating the dictionary of pixles, so we can run horizontal seams without changing the entire pathfinding algorithm,
    # hence allowing for generality in the seam discovery code.
    def transpose (self) :

        new_pix = {}
        for i in range(self.width):
            for j in range(self.height):
                new_pix[(j,i)]= Pixel( (j,i), self.pixels[(i,j)].rgb )
        self.pixels = new_pix
        tmp = self.height
        self.height = self.width
        self.width = tmp

        
# Class that encapsulates pixle data in image sc object including the energy, the unique identifier, the color the postion
# and a suite of methods to interact with it in the context of the image object
class Pixel:
    def __init__(self, pos, rgb, gray = None): 
        self.pos = pos
        self.original_pos = pos
        self.rgb = rgb

        #if gray wasn't explicitly set initialize it based off color
        if gray is None:
            r, g, b = self.rgb
            self.gray =  r + 256 * g + (256^2) * b
        else:
            self.gray = gray

        self.energy = 0

        self.to_remove = False

        self.recalculate = True

    # shifts pixle position by updating ivar
    def shift_pos(self, dx, dy):
        self.pos = (self.pos[0]+dx, self.pos[1]+dy)


    #flag to recalculate energy unless this pixel is part of an object getting removed
    def to_recalculate(self):
        if not self.to_remove:
            self.recalculate = True

    # to string function
    def __str__(self):
        return "[%s , %s]" % (str(self.pos), str(self.energy))
