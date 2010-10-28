""" Class for 2D slice GL wrapper """

# Adapted in part from image.py in glumpy.  See COPYING.txt

import numpy as np

from .textures import Texture1D, Texture2D
from . import gshaders


class Glice(object):
    def __init__(self, arr, shader=None, cmap=None, vmin=None, vmax=None):
        self._texture = Texture2D(arr)
        self._arr = arr
        if shader is None:
            shader = gshaders.Nearest(True, False)
        self.shader = shader
        self.cmap = cmap
        if vmin is None:
            vmin = arr.min()
        if vmax is None:
            vmax = arr.max()
        self.vmin, self.vmax = vmin, vmax

    def _get_cmap(self):
        return self._cmap

    def _set_cmap(self, cmap):
        if cmap is None:
            cmap = np.tile(
                np.linspace(0, 1, 512)[:,None], (1,3)).astype(np.float32)
        self._cmap = cmap
        self._lut = Texture1D(cmap)

    cmap = property(_get_cmap, _set_cmap, None, 'get / set cmap')

    def set_data(self, arr):
        self._texture.set_data(arr)
        self._arr = arr
        self.update()

    def update(self):
        s = self._lut.width
        vmin = self.vmin
        vmax = self.vmax
        self._texture.update(bias = 1.0/(s-1)-vmin*((s-3.1)/(s-1))/(vmax-vmin),
                             scale = ((s-3.1)/(s-1))/(vmax-vmin))

    def blit(self, x, y, w, h):
        ''' Blit array onto active framebuffer. '''
        self.shader.bind(self._texture, self._lut)
        self._texture.blit(x,y,w,h)
        self.shader.unbind()
