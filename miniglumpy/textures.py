''' Texture object.

    A texture is an image loaded into video memory that can be efficiently
    drawn to the framebuffer.
'''
# Modified from texture.py in glumpy
#-----------------------------------------------------------------------------
# Glumpy copyright (C) 2009-2010  Nicolas P. Rougier
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
#
# Modifications by Matthew Brett also under terms of BSD license - see
# COPYING.txt

import numpy as np

import pyglet.gl as gl

import gshaders


class Texture1D(object):
    target = gl.GL_TEXTURE_1D
    src_format = gl.GL_RGB
    dst_format = gl.GL_RGB16

    def __init__(self, arr):
        self._id = 0
        self.set_data(arr)

    def __del__(self):
        if self._id:
            gl.glDeleteTextures(1, gl.byref(self._id))

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def id(self):
        ''' GL texture name.

        :type: int, read-only
        '''
        return self._id.value

    def set_data(self, arr):
        arr = np.asarray(arr)
        src_type = gl.GL_FLOAT
        if arr.dtype in (np.dtype(np.float32), np.dtype(np.uint8)):
            arr = np.ascontiguousarray(arr)
            if arr.dtype == np.dtype(np.uint8):
                src_type = gl.GL_UNSIGNED_BYTE
        else:
            arr = arr.astype(np.float32)
        self.src_type = src_type
        self._arr = arr
        if self._id:
            gl.glDeleteTextures(1, gl.byref(self._id))
        id = gl.GLuint()
        gl.glGenTextures(1, gl.byref(id))
        self._id = id
        gl.glPixelStorei (gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei (gl.GL_PACK_ALIGNMENT, 1)
        gl.glBindTexture (self.target, self._id)
        gl.glTexParameterf (self.target,
                            gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameterf (self.target,
                            gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameterf (self.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameterf (self.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        self._setup_tex()
        self.update()

    def _setup_tex(self):
        self._width, self._height = self._arr.shape[0], 0
        gl.glTexImage1D (self.target, 0,
                         self.dst_format,
                         self._width, 0,
                         self.src_format, self.src_type, 0)

    def update(self, bias=0.0, scale=1.0):
        ''' Update texture. '''
        gl.glBindTexture(self.target, self.id)
        gl.glTexSubImage1D (self.target, 0, 0,
                            self._width,
                            self.src_format,
                            self.src_type,
                            self._arr.ctypes.data)

    def blit(self, x, y, w, h, z=0, s=(0,1), t=(0,1)):
        ''' Draw texture to active framebuffer. '''
        gl.glDisable (gl.GL_TEXTURE_2D)
        gl.glEnable (gl.GL_TEXTURE_1D)
        gl.glBindTexture(self.target, self._id)
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord1f(s[0]), gl.glVertex2f(x,   y)
        gl.glTexCoord1f(s[0]), gl.glVertex2f(x,   y+h)
        gl.glTexCoord1f(s[1]), gl.glVertex2f(x+w, y+h)
        gl.glTexCoord1f(s[1]), gl.glVertex2f(x+w, y)
        gl.glEnd()


class Texture2D(Texture1D):
    target = gl.GL_TEXTURE_2D
    src_format = gl.GL_ALPHA
    dst_format = gl.GL_ALPHA16

    def _setup_tex(self):
        self._height, self._width = self._arr.shape
        gl.glTexImage2D (self.target, 0, self.dst_format,
                         self._width, self._height, 0,
                         self.src_format, self.src_type, 0)
        self.update()

    def update(self, bias=0.0, scale=1.0):
        ''' Update texture. '''
        gl.glBindTexture(self.target, self._id)
        gl.glPixelTransferf(gl.GL_ALPHA_SCALE, scale)
        gl.glPixelTransferf(gl.GL_ALPHA_BIAS, bias)
        gl.glTexSubImage2D (self.target, 0, 0, 0,
                            self._arr.shape[1],
                            self._arr.shape[0],
                            self.src_format,
                            self.src_type,
                            self._arr.ctypes.data)
        # Default parameters
        gl.glPixelTransferf(gl.GL_ALPHA_SCALE, 1)
        gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 0)

    def blit(self, x, y, w, h, z=0, s=(0,1), t=(0,1)):
        ''' Draw texture to active framebuffer. '''
        gl.glEnable (gl.GL_TEXTURE_2D)
        gl.glDisable (gl.GL_TEXTURE_1D)
        gl.glBindTexture(self.target, self._id)
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(s[0], 1), gl.glVertex2f(x,   y)
        gl.glTexCoord2f(s[0], 0), gl.glVertex2f(x,   y+h)
        gl.glTexCoord2f(s[1], 0), gl.glVertex2f(x+w, y+h)
        gl.glTexCoord2f(s[1], 1), gl.glVertex2f(x+w, y)
        gl.glEnd()


class Glice(object):
    def __init__(self, arr, shader=None, cmap=None, vmin=None, vmax=None):
        self._texture = Texture2D(arr)
        self._arr = arr
        if shader is None:
            shader = gshaders.Nearest(True, False)
        self.shader = shader
        if cmap is None:
            cmap = np.tile(
                np.linspace(0, 1, 512)[:,None], (1,3)).astype(np.float32)
        self.cmap = cmap
        self._lut = Texture1D(cmap)
        if vmin is None:
            vmin = arr.min()
        if vmax is None:
            vmax = arr.max()
        self.vmin, self.vmax = vmin, vmax

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

