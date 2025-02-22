import pygame

class Parameter():

    def __init__(self):
        self.value = None
        self.default = None

    def get(self):
        if self.value:
            return self.value
        return self.default

    def reset(self):
        self.value = self.default

class SelectParameter(Parameter):

    def __init__(self):
        super().__init__()
        self.vars = None
        self.cyclic = None

class SliderParameter(Parameter):

    def __init__(self):
        super().__init__()
        self.min = None
        self.max = None
        self.mark_count = 0

class BooleanParameter(Parameter):

    def __init__(self):
        super().__init__()

class KeyParameter(Parameter):

    def __init__(self):
        super().__init__()

class Settings():
    """
        Select,
        Slider,
        Boolean
    """

    def __init__(self):
        self._values = {}
        self.binds = {}
        self.keybinds = {}
        self.changingBind = None

    def __getattr__(self, name):
        return self._values.get(name, None)

    def add_select(self, name, default, vars, cyclic=True):
        self._values[name] = SelectParameter()
        self._values[name].default = default
        self._values[name].vars = vars
        self._values[name].cyclic = cyclic

    def add_slider(self, name, default, s_min=0, s_max=100, mark_count=0):
        self._values[name] = SliderParameter()
        self._values[name].default = default
        self._values[name].min = s_min
        self._values[name].max = s_max
        self._values[name].mark_count = mark_count

    def add_boolean(self, name, default):
        self._values[name] = BooleanParameter()
        self._values[name].default = default

    def add_keybind(self, name, default):
        self.binds[name] = KeyParameter()
        self.binds[name].default = default
        self.keybinds[default] = name

    def event(self, ev):
        if self.changingBind is None:
            return
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                ev.key = None
            self.set_keybind(self.changingBind, ev.key)
            self.changingBind = None

    def change_keybind(self, name):
        self.changingBind = name

    def set_keybind(self, name, key):
        self.binds[name].value = key
        if key:
            self.keybinds[key] = name
