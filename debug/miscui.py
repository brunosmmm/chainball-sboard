from kivy.uix.spinner import Spinner
from kivy.properties import NumericProperty
from kivy.uix.gridlayout import GridLayout


class RootFinderMixin(object):

    def __init__(self, root_widget_class='RootWidget'):
        self.root_widget_class = root_widget_class

    def find_root(self):
        root = self.parent
        while root.__class__.__name__ != self.root_widget_class:
            root = root.parent
        return root


class ScoreSpinner(Spinner, RootFinderMixin):

    player = NumericProperty(-1)

    def __init__(self, *args, **kwargs):
        super(ScoreSpinner, self).__init__(*args, **kwargs)

        self.values = [str(x) for x in range(-10, 6)]

        self.updating = False

    def update_score(self, score):
        if score not in self.values and score != '-':
            return

        self.updating = True
        self.text = score

        if self.text == '-':
            self.disabled = True
        else:
            self.disabled = False

        self.updating = False

    def on_text(self, *args, **kwargs):
        if self.updating:
            return

        # set score
        self.find_root().do_set_score(self.player)

    def on_is_open(self, spinner, is_open):
        super(ScoreSpinner, self).on_is_open(spinner, is_open)

        #if is_open:
        #    self.find_root().stop_refreshing = True
        #else:
        #    self.find_root().stop_refreshing = False

    def on_press(self, *args):
        if self.is_open == False:
            # opening
            pass
