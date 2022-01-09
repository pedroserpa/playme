from PyQt5.QtWidgets import *
from PyQt5 import uic
from pygame import mixer
import sys
import os
from os import path, environ
import sqlite3
import atexit
from qt_material import apply_stylesheet

class PlayMe(QMainWindow):

    def __init__(self):
        super().__init__(parent=None)
        apply_stylesheet(app, theme='dark_yellow.xml', invert_secondary=True)
        uic.loadUi('layout.ui', self)  # Load the .ui file

        self.cwd = os.path.abspath(os.curdir)

        self.cnn = self.connect_db()

        if mixer.get_init() == None: mixer.init()

        #self.playlist = []
        self.paused = False
        self.get_file_list()

        self.chooseFileText.setText('')
        self.chooseFileBtn.clicked.connect(self.on_file_open)
        self.playBtn.clicked.connect(self.on_play)
        self.stopBtn.clicked.connect(self.on_stop)
        self.pauseBtn.clicked.connect(self.on_pause)
        self.volumeSlider.sliderReleased.connect(self.on_volume_set)

        if sys.platform == 'win32':
            appdata = path.join(environ['APPDATA'], 'PlayMe')
            print(appdata)

        atexit.register(self.on_exit_app)
        self.show()

    def connect_db(self):
        con_str = self.cwd + '/Data/list.db'
        self.cnn = sqlite3.connect(con_str)
        self.install_db()
        return self.cnn

    def install_db(self):
        cursor = self.cnn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS mp3_list (id INTEGER PRIMARY KEY, name TEXT NOT NULL, path TEXT NOT NULL)"
        cursor.execute(sql)
        self.cnn.commit()

    def close_db(self):
        self.cnn.close()

    def add_file_list(self, file_name, pathname):
        if not pathname:
            return False

        self.cnn = self.connect_db()
        cursor = self.cnn.cursor()

        sql = "SELECT * FROM mp3_list WHERE path=?"
        already_there = cursor.execute(sql, [pathname])
        already_there = already_there.fetchall()

        if not already_there:
            sql = "INSERT INTO mp3_list(name,path) VALUES(?,?)"
            cursor.execute(sql, (file_name, pathname))
            self.cnn.commit()
            self.get_file_list()

        return False

    def get_file_list(self):
        self.cnn = self.connect_db()
        cursor = self.cnn.cursor()
        sql = "SELECT id, name, path FROM mp3_list"
        data = cursor.execute(sql)
        data = data.fetchall()

        for value in data:
            name = value[1]
            path = value[2]
            item = QListWidgetItem(name, parent=self.listWidget)
            item.setData(1, path)
            #item.setText(name)
            self.listWidget.addItem(item)

        self.listWidget.itemClicked.connect(self.on_list_click)

    def on_list_click(self):
        self.load_file(self.listWidget.currentItem().data(1))

    def on_file_open(self, event):
        self.open_file_dialog()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                              "All Files (*);;Music (*.mp3)", options=options)
        #print(file)
        try:
            self.load_file(file)
        except IOError:
            print("Cannot open file '%s'." % file)

    def load_file(self, file):
        file_name = os.path.basename(file)
        self.chooseFileText.setText(file_name)

        self.add_file_list(file_name, file)

        mixer.music.load(file)
        mixer.music.play()

        self.on_play(self.on_play)

    def on_volume_set(self):
        new_volume = float(self.volumeSlider.value() / 100)
        mixer.music.set_volume(new_volume)

    def on_play(self, event):
        if self.paused:
            mixer.music.unpause()
        else:
            mixer.music.play()
        self.playBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.pauseBtn.setEnabled(True)
        # self.volBtn.Enable()

    def on_pause(self, event):
        self.paused = True
        mixer.music.pause()
        self.after_pause_stop()

    def on_stop(self, event):
        mixer.music.fadeout(1000)
        # mixer.music.stop()
        self.after_pause_stop()

    def after_pause_stop(self):
        self.playBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.pauseBtn.setEnabled(False)
        # self.volBtn.Disable()

    def on_exit_app(self):
        mixer.music.stop()
        self.close_db()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PlayMe()
    sys.exit(app.exec_())
