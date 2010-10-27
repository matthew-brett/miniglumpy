#!/usr/bin/env python
import numpy as np
import pyglet
import miniglumpy

window = pyglet.window.Window(512, 512, resizable=True)
Z = np.random.random((32,32)).astype(np.float32)
gslice = miniglumpy.Glice(Z)

@window.event
def on_draw():
    window.clear()
    gslice.blit(0, 0, window.width, window.height)

pyglet.app.run()
