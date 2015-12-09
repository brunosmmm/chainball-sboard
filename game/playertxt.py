class PlayerText(object):

    def __init__(self, panel_txt, web_txt=None):

        if panel_txt == None:
            raise ValueError('Display name cannot be empty')
        else:
            if len(panel_txt) == 0:
                raise ValueError('Display name cannot be empty')

        if web_txt:
            if len(web_txt) > 0:
                self.web_txt = web_txt
        else:
            self.web_txt = panel_txt

        self.panel_txt = panel_txt
