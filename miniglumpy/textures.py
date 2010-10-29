''' Texture object.

    A texture is an image loaded into video memory that can be efficiently
    drawn to the framebuffer.
'''
# Modified from texture.py in glumpy - see COPYING.txt

import numpy as np

import pyglet.gl as gl

class TextureError(Exception):
    pass


def make_texture(arr):
    arr = np.asarray(arr)
    shape = arr.shape
    ndim = len(shape)
    if ndim == 1 or ndim == 2 and shape[-1] <=4:
        return Texture1D(arr)
    return Texture2D(arr)


_DIM_TO_FMTS = {
    1: (gl.GL_ALPHA, gl.GL_ALPHA16),
    2: (gl.GL_LUMINANCE_ALPHA, gl.GL_LUMINANCE16_ALPHA16),
    3: (gl.GL_RGB, gl.GL_RGB16),
    4: (gl.GL_RGBA, gl.GL_RGBA16)
}


def fmts_from_shape(shape, texture_dim):
    """ Return source and destination GL formats from array shape

    Parameters
    ----------
    shape : tuple
    texture_dim : int
       shape index that should contain texture.  For 1D textures this will == 2,
       for 2D arrays `texture_dim` == 3

    Returns
    -------
    src_format : int
        GL code for source array format
    dst_format : int
        GL code for destination array format
    """
    ndim = len(shape)
    if ndim == texture_dim:
        t_len = shape[-1]
        if t_len > 4:
            raise TextureError(
                '%s dimension of texture array must be <=4' % t_len)
    elif ndim == texture_dim - 1:
        t_len = 1
    else:
        raise TextureError('Texture must have %s or %s dimensions'
                          % (texture_dim, texture_dim-1))
    return _DIM_TO_FMTS[t_len]


class Texture1D(object):
    target = gl.GL_TEXTURE_1D
    _texture_dim = 2

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
        ''' GL texture identifier

        Returns
        -------
        res : int
        '''
        return self._id.value

    def set_data(self, arr):
        arr = np.asarray(arr)
        self.src_format, self.dst_format = fmts_from_shape(arr.shape,
                                                           self._texture_dim)
        # Float is default type
        if arr.dtype == np.uint8:
            arr = np.ascontiguousarray(arr)
            self.src_type = gl.GL_UNSIGNED_BYTE
        elif arr.dtype == np.float32:
            arr = np.ascontiguousarray(arr)
            self.src_type = gl.GL_FLOAT
        else:
            arr = np.astype(np.float32)
            self.src_type = gl.GL_FLOAT
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

    def update(self, bias=0.0, scale=1.0):
        ''' Update texture with bias and scale '''
        gl.glBindTexture(self.target, self._id)
        # Autoscale array using OpenGL pixel transfer parameters
        if self.src_type == gl.GL_FLOAT:
            gl.glPixelTransferf(gl.GL_ALPHA_SCALE, scale)
            gl.glPixelTransferf(gl.GL_ALPHA_BIAS, bias)
        self._subimage()
        if self.src_type == gl.GL_FLOAT:
            # Reset to default parameters
            gl.glPixelTransferf(gl.GL_ALPHA_SCALE, 1)
            gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 0)

    # The following are class-specific implementations

    def _setup_tex(self):
        self._width, self._height = self._arr.shape[0], 0
        gl.glTexImage1D (self.target, 0,
                         self.dst_format,
                         self._width, 0,
                         self.src_format, self.src_type, 0)

    def _subimage(self):
        gl.glTexSubImage1D (self.target, 0, 0,
                            self._width,
                            self.src_format,
                            self.src_type,
                            self._arr.ctypes.data)

    def blit(self, x, y, w, h, z=0, s=(0,1), **kwargs):
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
    _texture_dim = 3

    def _setup_tex(self):
        self._height, self._width = self._arr.shape
        gl.glTexImage2D (self.target, 0, self.dst_format,
                         self._width, self._height, 0,
                         self.src_format, self.src_type, 0)
        self.update()

    def _subimage(self):
        gl.glTexSubImage2D (self.target, 0, 0, 0,
                            self._arr.shape[1],
                            self._arr.shape[0],
                            self.src_format,
                            self.src_type,
                            self._arr.ctypes.data)

    def blit(self, x, y, w, h, z=0, s=(0,1), **kwargs):
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
