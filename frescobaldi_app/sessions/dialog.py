# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Session dialog for named session stuff.
"""

from __future__ import unicode_literals

import json

from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QGridLayout, 
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout)

import app
import widgets.listedit
import widgets.urlrequester
import sessions
import userguide


class SessionManagerDialog(QDialog):
    def __init__(self, mainwindow):
        super(SessionManagerDialog, self).__init__(mainwindow)
        self.mainwindow = mainwindow
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(app.caption(_("Manage Sessions")))
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.sessions = SessionList(self)
        layout.addWidget(self.sessions)
        
        self.imp = QPushButton(self)
        self.exp = QPushButton(self)
        self.imp.clicked.connect(self.importSession)
        self.exp.clicked.connect(self.exportSession)
        self.imp.clicked.connect(self.accept)
        ielayout = QVBoxLayout()
        ielayout.addWidget(self.imp, alignment=Qt.AlignRight)
        ielayout.addWidget(self.exp, alignment=Qt.AlignRight)
        layout.addLayout(ielayout)
        layout.addWidget(widgets.Separator())
        app.translateUI(self)
        
        self.buttons = b = QDialogButtonBox(self)
        layout.addWidget(b)
        b.setStandardButtons(QDialogButtonBox.Close)
        b.rejected.connect(self.accept)
        userguide.addButton(b, "sessions")
        self.sessions.load()
        
    def translateUI(self):
        self.imp.setText(_("Import"))
        self.exp.setText(_("Export"))
        
    def importSession(self):
        filetypes = '{0} (*.json);;{1} (*)'.format(_("JSON Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import session"))
        import os
        directory = os.path.dirname(self.mainwindow.currentDocument().url().toLocalFile()) or app.basedir()
        importfile = QFileDialog.getOpenFileName(self.mainwindow, caption, directory, filetypes)
        if not importfile:
            return # cancelled by user
        f = open(importfile)
        self.sessions.importItem(json.load(f))
        f.close()
		
    def exportSession(self):
        itemname, jsondict = self.sessions.exportItem()
        filename = itemname+".json"
        caption = app.caption(_("dialog title", "Export session"))
        filetypes = '{0} (*.json);;{1} (*)'.format(_("JSON Files"), _("All Files"))
        filename = QFileDialog.getSaveFileName(self.mainwindow, caption, filename, filetypes)
        if not filename:
            return False # cancelled
        f = open(filename, 'w')
        json.dump(jsondict, f, indent=4)
        f.close()


class SessionList(widgets.listedit.ListEdit):
    """Manage the list of sessions."""
    def load(self):
        names = sessions.sessionNames()
        current = sessions.currentSession()
        self.setValue(names)
        if current in names:
            self.setCurrentRow(names.index(current))

    def removeItem(self, item):
        sessions.deleteSession(item.text())
        super(SessionList, self).removeItem(item)

    def openEditor(self, item):
        name = SessionEditor(self).edit(item.text())
        if name:
            item.setText(name)
            return True
            
    def importItem(self, data):
        session = sessions.sessionGroup(data['name'])
        for key in data:
            if key == 'urls':
                urls = []
                for u in data[key]:
                    urls.append(QUrl(u))
                session.setValue("urls", urls)
            elif key != 'name':
                session.setValue(key, data[key])
		
    def exportItem(self):
        jsondict = {}
        item = self.listBox.currentItem()
        s = sessions.sessionGroup(item.text())
        for key in s.allKeys():
			if key == 'urls':
				urls = []
				for u in s.value(key):
					urls.append(u.toString())
				jsondict[key] = urls 
			else:
				jsondict[key] = s.value(key)
        return (item.text(), jsondict)


class SessionEditor(QDialog):
    def __init__(self, parent=None):
        super(SessionEditor, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        grid = QGridLayout()
        layout.addLayout(grid)
        
        self.name = QLineEdit()
        self.nameLabel = l = QLabel()
        l.setBuddy(self.name)
        grid.addWidget(l, 0, 0)
        grid.addWidget(self.name, 0, 1)
        
        self.autosave = QCheckBox()
        grid.addWidget(self.autosave, 1, 1)
        
        self.basedir = widgets.urlrequester.UrlRequester()
        self.basedirLabel = l = QLabel()
        l.setBuddy(self.basedir)
        grid.addWidget(l, 2, 0)
        grid.addWidget(self.basedir, 2, 1)
        
        layout.addWidget(widgets.Separator())
        self.buttons = b = QDialogButtonBox(self)
        layout.addWidget(b)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "sessions")
        app.translateUI(self)
        
    def translateUI(self):
        self.nameLabel.setText(_("Name:"))
        self.autosave.setText(_("Always save the list of documents in this session"))
        self.basedirLabel.setText(_("Base directory:"))
    
    def load(self, name):
        settings = sessions.sessionGroup(name)
        self.autosave.setChecked(settings.value("autosave", True, bool))
        self.basedir.setPath(settings.value("basedir", "", type("")))
        # more settings here
        
    def save(self, name):
        settings = sessions.sessionGroup(name)
        settings.setValue("autosave", self.autosave.isChecked())
        settings.setValue("basedir", self.basedir.path())
        # more settings here
        
    def defaults(self):
        self.autosave.setChecked(True)
        self.basedir.setPath('')
        # more defaults here
        
    def edit(self, name=None):
        self._originalName = name
        if name:
            caption = _("Edit session: {name}").format(name=name)
            self.name.setText(name)
            self.load(name)
        else:
            caption = _("Edit new session")
            self.name.clear()
            self.name.setFocus()
            self.defaults()
        self.setWindowTitle(app.caption(caption))
        if self.exec_():
            # name changed?
            name = self.name.text()
            if self._originalName and name != self._originalName:
                sessions.renameSession(self._originalName, name)
            self.save(name)
            return name

    def done(self, result):
        if not result or self.validate():
            super(SessionEditor, self).done(result)
        
    def validate(self):
        """Checks if the input is acceptable.
        
        If this method returns True, the dialog is accepted when OK is clicked.
        Otherwise a messagebox could be displayed, and the dialog will remain
        visible.
        """
        name = self.name.text().strip()
        self.name.setText(name)
        if not name:
            self.name.setFocus()
            QMessageBox.warning(self, app.caption(_("Warning")),
                _("Please enter a session name."))
            if self._originalName:
                self.name.setText(self._originalName)
            return False
        
        elif name == '-':
            self.name.setFocus()
            QMessageBox.warning(self, app.caption(_("Warning")),
                _("Please do not use the name '{name}'.".format(name="-")))
            return False
        
        elif self._originalName != name and name in sessions.sessionNames():
            self.name.setFocus()
            box = QMessageBox(QMessageBox.Warning, app.caption(_("Warning")),
                _("Another session with the name {name} already exists.\n\n"
                  "Do you want to overwrite it?").format(name=name),
                QMessageBox.Discard | QMessageBox.Cancel, self)
            box.button(QMessageBox.Discard).setText(_("Overwrite"))
            result = box.exec_()
            if result != QMessageBox.Discard:
                return False
            
        return True

