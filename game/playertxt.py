"""Player text."""


class PlayerText(object):
    """Player text and display storage."""

    def __init__(self, panel_txt, web_txt=None):
        """Initialize.

        Args
        ----
        panel_txt: str
           Player name as displayed in panels
        web_txt: str
           Complete player name displayed in web interface
        """
        if panel_txt is None:
            raise ValueError('Display name cannot be empty')
        else:
            if len(panel_txt) == 0:
                raise ValueError('Display name cannot be empty')

        if web_txt is not None:
            if len(web_txt) > 0:
                self.web_txt = web_txt
        else:
            self.web_txt = panel_txt

        self.panel_txt = panel_txt

    def __repr__(self):
        """Dump representation."""
        return '{}, {}'.format(self.panel_txt, self.web_txt)
