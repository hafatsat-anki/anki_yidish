"""Searchable, measured file contents shared by all daily tracks."""
from aqt.qt import (
    QDialog, QLabel, QLineEdit, QPushButton, QSplitter,
    QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, Qt,
)
from .learning_catalog import source_catalog


def show_source_files(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("אינהאלט פון די מאגר השאלות טעקעס")
    dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    available = dialog.screen().availableGeometry()
    dialog.resize(min(1000, available.width() - 40), min(720, available.height() - 80))
    layout = QVBoxLayout(dialog)
    note = QLabel("קלייבט אויס א טעקע צו ווייזן די סימנים, סעיפים און בלעטער דערמאנט אין די שאלות. די ליסטע באווייזט נישט אז דער גאנצער פארנעם איז געדעקט.")
    note.setWordWrap(True)
    layout.addWidget(note)
    search = QLineEdit()
    search.setPlaceholderText("זוכן א מקור, טעקע, סימן, סעיף אדער בלאט…")
    layout.addWidget(search)
    splitter = QSplitter()
    tree = QTreeWidget()
    tree.setHeaderLabels(["מקור / טעקע", "שאלות"])
    tree.setColumnWidth(0, 430)
    details = QTextBrowser()
    splitter.addWidget(tree)
    splitter.addWidget(details)
    layout.addWidget(splitter, 1)
    entries = []
    for source, info in source_catalog().items():
        group = QTreeWidgetItem(tree, [source.replace("/", " / "), str(info["questions"])])
        for file in info.get("file_details", []):
            name = file["path"][len(source) + 1:]
            locations = file["locations"]
            content = file["path"].replace("_", " ") + "\n\n"
            if locations:
                content += "פלעצער דערמאנט אין די שאלות:\n" + "\n".join(locations)
            else:
                content += "א דעטאלירטער מקור פעלד איז נישט דערקענט געווארן; קאנטראלירט דעם פארנעם אינעם טעקע נאמען און די שאלות איידער איר אימפארטירט."
            item = QTreeWidgetItem(group, [name.replace("_", " "), str(file["questions"])])
            item.setData(0, Qt.ItemDataRole.UserRole, content)
            entries.append((item, (source + " " + content).casefold()))

    def select(item, previous=None):
        details.setPlainText((item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)) if item else "")

    def filter_files(query):
        terms = query.casefold().split()
        for item, text in entries:
            item.setHidden(not all(term in text for term in terms))
        for index in range(tree.topLevelItemCount()):
            group = tree.topLevelItem(index)
            group.setHidden(all(group.child(i).isHidden() for i in range(group.childCount())))
            group.setExpanded(bool(terms) and not group.isHidden())

    tree.currentItemChanged.connect(select)
    search.textChanged.connect(filter_files)
    close = QPushButton("פארמאכן")
    close.clicked.connect(dialog.accept)
    layout.addWidget(close)
    dialog.exec()
