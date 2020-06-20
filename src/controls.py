import pyglet
import time

from math import pi

from pyglet.window import key

class Controls:
    MOD_MASK = key.MOD_CTRL | key.MOD_SHIFT

    def __init__(self, world):
        NOMODS = 0x0
        self.prev_moment = None

        self.press_actions = {
                (key.BRACKETLEFT, NOMODS): lambda: world.tilt_by(-0.1 * pi),
                (key.BRACKETRIGHT, NOMODS): lambda: world.tilt_by(0.1 * pi),
                (key.PLUS, NOMODS): lambda: world.zoom_by(5),
                (key.NUM_ADD, NOMODS): lambda: world.zoom_by(5),
                (key.MINUS, NOMODS): lambda: world.zoom_by(-5),
                (key.NUM_SUBTRACT, NOMODS): lambda: world.zoom_by(-5),
            }

        self.release_actions = {}

        self.repeatable_actions = {
                (key.A, NOMODS): lambda intv: world.move(-pi * intv, 0.0),
                (key.D, NOMODS): lambda intv: world.move(pi * intv, 0.0),
                (key.E, NOMODS): lambda intv: world.rotate_by(-0.5 * pi * intv),
                (key.Q, NOMODS): lambda intv: world.rotate_by(0.5 * pi * intv),
                (key.S, NOMODS): lambda intv: world.move(0.0, pi * intv),
                (key.W, NOMODS): lambda intv: world.move(0.0, -pi * intv),
                (key.LEFT, NOMODS): lambda intv: world.move(-pi * intv, 0.0),
                (key.RIGHT, NOMODS): lambda intv: world.move(pi * intv, 0.0),
                (key.UP, NOMODS): lambda intv: world.move(0.0, -pi * intv),
                (key.DOWN, NOMODS): lambda intv: world.move(0.0, pi * intv),
            }

        self.active_actions = {}

    def handle_key_press(self, symbol, modifiers):
        self.prev_moment = time.monotonic()
        key = (symbol, Controls.MOD_MASK & modifiers)

        if (action := self.press_actions.get(key, None)) is not None:
            action()
        elif (action := self.repeatable_actions.get(key, None)) is not None:
            self.active_actions[key] = action

    def handle_key_release(self, symbol, modifiers):
        key = (symbol, Controls.MOD_MASK & modifiers)

        if (action := self.release_actions.get(key, None)) is not None:
            action()
        elif key in self.repeatable_actions:
            del self.active_actions[key]

    def on_draw(self):
        current_moment = time.monotonic()
        if self.prev_moment is not None:
            interval = current_moment - self.prev_moment
            if interval > 0:
                for key, action in self.active_actions.items():
                    action(interval)

        active = len(self.active_actions) > 0
        if active:
            self.prev_moment = current_moment
        else:
            self.prev_moment = None

        return active

