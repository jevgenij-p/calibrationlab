"""A simple Event system.
    Source: http://www.valuedlessons.com/2008/04/events-in-python.html
"""

class Event:
    """An Event controller class."""
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        """Add event handler."""
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        """Remove event handler."""
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        """Call event handler."""
        for handler in self.handlers:
            handler(*args, **kargs)

    def get_handler_count(self):
        """Get event handlers count."""
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = get_handler_count
