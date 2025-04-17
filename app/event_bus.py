class EventBus:
    _subscribers = {}

    @classmethod
    def subscribe(cls, event_name, callback):
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        cls._subscribers[event_name].append(callback)

    @classmethod
    def unsubscribe(cls, event_name, callback):
        if event_name in cls._subscribers:
            cls._subscribers[event_name].remove(callback)

    @classmethod
    def notify(cls, event_name, data=None):
        if event_name in cls._subscribers:
            for callback in cls._subscribers[event_name]:
                callback(data)
