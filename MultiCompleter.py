# From https://stackoverflow.com/questions/35628257/pyqt-auto-completer-with-qlineedit-multiple-times

from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import Qt

class MultiCompleter(QCompleter):

    def __init__(self, parent=None):
        super(MultiCompleter, self).__init__(parent)

        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setWrapAround(False)
        
    def pathFromIndex(self, index):
        path = QCompleter.pathFromIndex(self, index)

        lst = str(self.widget().text()).split(',')

        if len(lst) > 1:
            path = '%s, %s' % (','.join(lst[:-1]), path)

        return path

    def splitPath(self, path):
        path = str(path.split(',')[-1]).lstrip(' ')
        return [path]