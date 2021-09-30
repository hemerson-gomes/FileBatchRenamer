import sys, os, json, io
from MainWindowUI import *
from SupportClasses import *
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QDialog

class MainProgram(QMainWindow):
    def __init__(self):
        #Initializing super class
        super().__init__()
        #Setting up ui elements
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('File Batch Renamer')
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.setWindowIcon(QIcon('./icons/main_icon.png'));

        #Setting up language and instances of support classes
        self.display_lang = 'en_US'
        self.lang_setter = LanguageSetter(self)
        self.lang_setter.translate(self.display_lang)
        self.info_msg = WarningWidget(self.lang_setter.langs)
        self.about_msg = InfoWidget(self.lang_setter.langs)

        #Creating main variables
        self.files = list()
        self.changes_available = False
        self.files_total = 0

        #Defining signals and slots for radiobuttons
        self.style_selected = str()
        self.ui.radioButtonDot.released.connect(lambda: self.set_selected_style('.'))
        self.ui.radioButtonDash.released.connect(lambda: self.set_selected_style(' - '))
        self.ui.radioButtonUnderline.released.connect(lambda: self.set_selected_style('_'))
        self.ui.radioButtonDot.click()

        #Defining singals and slots for pushbuttons
        self.ui.pushButtonApply.clicked.connect(self.call_operation)
        self.ui.pushButtonSave.clicked.connect(self.save_changes)
        self.ui.pushButtonMoveUp.clicked.connect(self.move_up)
        self.ui.pushButtonMoveDown.clicked.connect(self.move_down)

        #Defining signals and slots for action menu buttons
        self.ui.actionAbout.triggered.connect(
                    lambda: self.about_msg.show_info(self.ui.actionAbout.text(), self.display_lang))
        self.ui.actionOpen_files.triggered.connect(self.open_files_dialog)
        self.ui.actionPortugu_s_Brasil.triggered.connect(lambda: self.lang_setter.translate('pt_BR'))
        self.ui.actionEnglish.triggered.connect(lambda: self.lang_setter.translate('en_US'))
        self.ui.actionSave.triggered.connect(self.save_changes)
        self.ui.actionExit.triggered.connect(self.close)

        #Display UI
        self.show()

    def open_files_dialog(self): #Dialog for loading files
        dialog = QFileDialog.getOpenFileNames(self, 'Open file', os.path.expanduser('~'))
        if len(dialog[0]) > 0:
            self.clear_all_names()
            self.files_total = len(dialog[0])
            for file in dialog[0]:
                full_name = os.path.basename(file)
                name, extension = os.path.splitext(full_name)
                path = os.path.dirname(file)
                self.files.append(FileModel(name, extension, path))
            self.changes_available = False
            self.update_display_originals()

    def save_changes(self): #Dialog for saving changes
        if self.changes_available:
            for i in range(self.files_total):
                try:
                    old_path = self.files[i].get_old_path()
                    new_path = self.files[i].get_modified_path()
                    os.rename(old_path, new_path)
                except:
                    self.info_msg.show_popup(self.display_lang, 'WritingError', 'Error')
                    return
            for i in range(self.files_total):
                self.files[i].override_old_name()
            self.info_msg.show_popup(self.display_lang, 'SaveSuccess')
            self.update_display_originals()
            self.changes_available = False
        elif self.files_total == 0:
            return
        else:
            self.info_msg.show_popup(self.display_lang, 'NoChanges')

    def set_selected_style(self, style: str): #Method for defining separator style
        self.style_selected = style

    def call_operation(self): #Method for calling the function associated with each radiobutton
        if self.files_total > 0:
            dispatch = {0:self.rename_sequentially,
                        1:self.replace_string,
                        2:self.remove_string}
            current_index = self.ui.tabWidget.currentIndex()
            dispatch[current_index]()

    def rename_sequentially(self): #Method for renaming sequentially feature
        common_string = self.ui.lineEditStandardName.text()
        separator_style = self.style_selected
        try:
            count = int(self.ui.lineEditStartingPoint.text())
        except:
            self.info_msg.show_popup(self.display_lang, 'InvalidNumber', 'Error')
            return
        if common_string != '' and count >= 0 and self.files_total > 0:
            counter_length = len(str(count + self.files_total - 1))
            for i in range(self.files_total):
                counter = '0'*(counter_length - len(str(count))) + str(count)
                new_name = common_string + separator_style + counter
                self.files[i].set_new_name(new_name)
                count += 1
            self.update_display_modified()
            self.changes_available = True
        elif count < 0:
            self.info_msg.show_popup(self.display_lang, 'NegativeInteger')
            return
        else:
            self.info_msg.show_popup(self.display_lang, 'InvalidName')

    def replace_string(self): #Method for replacing string feature
        replaced = self.ui.lineEditReplaced.text()
        inserted = self.ui.lineEditInserted.text()
        if inserted != '':
            for i in range(self.files_total):
                if replaced not in self.files[i].get_old_name():
                    self.info_msg.show_popup(self.display_lang, 'MissingString')
                    return
            for i in range(self.files_total):
                old_name = self.files[i].get_old_name()
                new_name = old_name.replace(replaced, inserted, 1)
                self.files[i].set_new_name(new_name)
            self.update_display_modified()
            self.changes_available = True
        else:
            self.info_msg.show_popup(self.display_lang, 'EmptyString')

    def remove_string(self): #Method for removing string feature
        target = self.ui.lineEditRemove.text()
        if target != '':
            for i in range(self.files_total):
                trial = self.files[i].get_old_name()
                if trial.replace(target, '') == trial:
                    self.info_msg.show_popup(self.display_lang, 'MissingString')
                    return
            for i in range(self.files_total):
                old_name = self.files[i].get_old_name()
                new_name = old_name.replace(target, '', 1)
                self.files[i].set_new_name(new_name)
            self.update_display_modified()
            self.changes_available = True

    def move_up(self): #Method for moving up selected files in the list
        selected = list()
        items = self.ui.listWidgetFilesOld.selectedIndexes()
        for item in items:
            selected.append(int(item.row()))
        selected.sort()
        if len(items) == 0 or selected[0] == 0:
            return
        for row in selected:
            temp = self.files[row-1]
            self.files[row-1] = self.files[row]
            self.files[row] = temp
        self.update_display_originals()
        for row in selected:
            self.ui.listWidgetFilesOld.item(row-1).setSelected(True)
        self.ui.listWidgetFilesOld.setFocus()

    def move_down(self): #Method for moving down selected files in the list
        selected = list()
        items = self.ui.listWidgetFilesOld.selectedIndexes()
        for item in items:
            selected.append(int(item.row()))
        selected.sort(reverse=True)
        if len(items) == 0 or selected[0] == self.files_total-1:
            return
        for row in selected:
            temp = self.files[row+1]
            self.files[row+1] = self.files[row]
            self.files[row] = temp
        self.update_display_originals()
        for row in selected:
            self.ui.listWidgetFilesOld.item(row+1).setSelected(True)
        self.ui.listWidgetFilesOld.setFocus()

    def clear_all_names(self): #Method for clearing all names
        self.ui.listWidgetFilesOld.clear()
        self.ui.listWidgetFilesNew.clear()
        self.files.clear()

    def update_display_originals(self): #Method for updating List Widget
        self.ui.listWidgetFilesOld.clear()
        for i in range(self.files_total):
            item = self.files[i].get_old_name()
            self.ui.listWidgetFilesOld.addItem(item)

    def update_display_modified(self): #Method for updating List Widget
        self.ui.listWidgetFilesNew.clear()
        for i in range(self.files_total):
            item = self.files[i].get_modified_name()
            self.ui.listWidgetFilesNew.addItem(item)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainProgram()
    sys.exit(app.exec_())
