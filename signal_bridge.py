from PySide6.QtCore import QObject, Signal

class SignalBridge(QObject):
    message = Signal(dict)
