"""An example of use from compute index lexical availability score and index lexical availability standarized score

.. moduleauthor:: Gabriela Ramirez (github/gabyrr)

"""

import get_idlv

dirIn = "input/"
dirOut = "output/"
resolution = 1
get_idlv.main(dirIn, dirOut, resolution)


import get_idlv_st as idlvmod

dirIn = "input/"
dirOut = "output/"
resolution = 1
k = 5
w = 0.1
m = 1.0

idlvmod.main(dirIn, dirOut, resolution, k, w, m)
