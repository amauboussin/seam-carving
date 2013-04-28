from math import fabs
#gets energy using e1 algorithm. helper methods may be added later


def three_three_filter(pixel, neighbors, a, b):
    [n1, n2, n3, n4, px, n5, n6, n7, n8] = neighbors
    """
    | n1 n2 n3 |
    | n4 px n5 |
    | n6 n7 n8 |
     """
    pos_dx =  a * n4.gray + b * n1.gray + b * n6.gray
    neg_dx =  - a * n5.gray - b * n3.gray - b * n8.gray
    dx = pos_dx + neg_dx
    pos_dy =  a * n7.gray + b * n8.gray + b * n6.gray
    neg_dy = - a * n2.gray - b * n3.gray - b * n1.gray
    dy = pos_dy + neg_dy

    pixel.energy = fabs(dx) + fabs(dy)

    pixel.recalculate = False

    return pixel

def Kroon_op(pixel, neighbors):
    return three_three_filter(pixel, neighbors, 61, 17)

def Scharr_op(pixel, neighbors):
    return three_three_filter(pixel, neighbors, 10, 3)

def Sobel_op(pixel, neighbors):
    return three_three_filter(pixel, neighbors, 2, 1)

def five_five_filter(pixel, n, a, b, c, d, e, f):
    pos_dx = a*n[12].gray + b*n[11].gray + c*(n[7].gray + n[17].gray) + d*(n[6].gray + n[16].gray) + e*(n[2].gray + n[22].gray) + f*(n[1].gray+n[21].gray)
    neg_dx = a*n[14].gray + b*n[15].gray + c*(n[9].gray + n[19].gray) + d*(n[10].gray + n[20].gray) + e*(n[4].gray + n[24].gray) + f*(n[5].gray + n[25].gray)
    dx = pos_dx - neg_dx
    pos_dy = a*n[18].gray + b*n[23].gray + c*(n[17].gray + n[19].gray) + d*(n[22].gray + n[24].gray) + e*(n[16].gray + n[20].gray) + f*(n[21].gray+n[25].gray)
    neg_dy = a*n[8].gray + b*n[3].gray + c*(n[7].gray + n[9].gray) + d*(n[2].gray + n[4].gray) + e*(n[6].gray + n[10].gray) + f*(n[1].gray + n[5].gray)
    dy = pos_dy - neg_dy

    pixel.energy = fabs(dx) + fabs(dy)

    pixel.recalculate = False

    return pixel

def Sobel_five_op(pixel, neighbors):
    return five_five_filter(pixel, neighbors, 20, 10, 10, 8, 4, 5)

def Scharr_five_op(pixel, neighbors):
    return five_five_filter(pixel, neighbors, 6, 3, 2, 2, 1, 1)
#gets energy using entropy algorithm. helper methods may be added later
def entropy(pixel, square):
	raise NotImplementedError