import json
import os
import re
import sys

# #388 — כלי הבנייה רץ גם מ-cmd של Windows; פלט עברי לא צריך להפיל את הבנייה.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# #346 — הוסרה התלות ב-py7zr (ובתיקיית vendor/ שדרשה בינאריים של ווינדוס).
# המאגר הומר ל-tar.xz ונקרא דרך archive_access שמבוסס על tarfile+lzma.
# הקובץ הזה הוא כלי פיתוח שרץ ישירות, ולכן הייבוא אינו יחסי.
from archive_access import extract_targets, list_names


def extract_num(s, ret=0):
    p = re.compile(r'(\d+)')
    search = p.search(s)
    if search:
        return int(search.groups()[0])
    else:
        return ret


def rename_item(name):
    if not isinstance(name, str):
        return name
    return name.replace("_טו", "_יה") \
               .replace("_טז", "_יו") \
               .replace("_קטו", "_קיה") \
               .replace("_קטז", "_קיו") \
               .replace("כל המסכת", "אאכל המסכת") \
               .replace("פרק", "אאפרק")

def restore_item(name):
    if not isinstance(name, str):
        return name
    return name.replace("_יה", "_טו") \
               .replace("_יו", "_טז") \
               .replace("_קיה", "_קטו") \
               .replace("_קיו", "_קטז") \
               .replace("אאכל המסכת", "כל המסכת") \
               .replace("אאפרק", "פרק")

def check_empty_files_in_archive():
    empty_files = set()
    print("Scanning archive for empty files in memory...")

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        all_targets = list_names('.txt')
        extract_targets(all_targets, tmpdirname)

        for root, _, files in os.walk(tmpdirname):
            for file in files:
                if not file.endswith('.txt'):
                    continue
                full_path = os.path.join(root, file)
                # re-calculate the relative path exactly as in the 7z
                rel_path = os.path.relpath(full_path, tmpdirname).replace('\\', '/')

                try:
                    with open(full_path, encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(full_path, encoding='utf-16') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(full_path, encoding='windows-1255', errors='replace') as f:
                            content = f.read()

                lines = content.strip().split('\n')

                is_empty = True
                for line in lines:
                    l = line.strip()
                    if l and not l.startswith('#'):
                        is_empty = False
                        break

                if is_empty:
                    empty_files.add(rel_path)

    return empty_files

def unflatten_paths(file_paths):
    root = {}
    for path in file_paths:
        parts = [p for p in path.split('/') if p]
        curr = root
        for part in parts[:-1]:
            if part not in curr:
                curr[part] = {}
            curr = curr[part]
        curr[parts[-1]] = None  # file marker
    return root

ROOT_SUBJECT_ORDER = {
    "שס": 0,
    "משנה ברורה": 1,
    "שו''ע": 2,
    "משניות": 3,
    "תלמוד ירושלמי": 4,
    "על התורה": 5,
    "עניינים": 6,
}

TORAH_BOOK_ORDER = {
    "בראשית": 0,
    "שמות": 1,
    "ויקרא": 2,
    "במדבר": 3,
    "דברים": 4,
}


def build_children(node_dict, depth=0):
    children = []
    for name, content in node_dict.items():
        if content is None:
            children.append({"name": name, "type": "file"})
        else:
            children.append({
                "name": name,
                "type": "directory",
                "children": build_children(content, depth + 1)
            })

    # Apply identical sort logic
    for i in children:
        i["name"] = rename_item(i["name"])

    try:
        children = sorted(children, key=lambda c: c.get('name', 0), reverse=False)
    except TypeError:
        pass

    children = sorted(children, key=lambda c: extract_num(c["name"]))

    # #381 — סדר נושאי המאגר הוא סדר תוכני יציב, לא סדר אלפביתי מקרי. בלי העדיפות
    # הזו "שס" נדחק אחרי משנה ברורה ושאר המדורים בכל בנייה מחדש.
    if depth == 0:
        children = sorted(
            children,
            key=lambda c: ROOT_SUBJECT_ORDER.get(restore_item(c["name"]), 100),
        )

    for i in children:
        i["name"] = restore_item(i["name"])

    # חומשים מוצגים בסדר התורה ולא בסדר אלפביתי.
    if any(child["name"] in TORAH_BOOK_ORDER for child in children):
        children = sorted(
            children,
            key=lambda c: TORAH_BOOK_ORDER.get(c["name"], 100),
        )

    # בכל קטגוריה, תרומות הלומדים נשארות האפשרות האחרונה.
    children = sorted(
        children,
        key=lambda c: c["name"] == "שאלות מהלומדים",
    )

    return children

def build_zip_tree():
    empty_files = check_empty_files_in_archive()

    if empty_files:
        print(f"Found {len(empty_files)} empty files. Writing to empty_files_builder_log.txt...")
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "empty_files_builder_log.txt")
        with open(log_path, "w", encoding="utf-8") as clog:
            for ef in empty_files:
                print(f"קובץ ריק דולג והוסר מעץ החפיסות: {ef}")
                clog.write(ef + "\n")

    # list_names מחזיר קבצים בלבד, ולכן אין יותר צורך בסינון is_directory
    valid_paths = []
    for fname in list_names():
        if fname in empty_files or fname.endswith('.json') or 'media' in fname or '__MACOSX' in fname:
            continue
        valid_paths.append(fname)

    root_dict = unflatten_paths(valid_paths)

    base_folder_name = "מאגר השאלות"
    if base_folder_name in root_dict:
        nested_root = root_dict[base_folder_name]
    else:
        nested_root = root_dict

    tree = {
        "name": base_folder_name,
        "type": "directory",
        "children": build_children(nested_root, depth=0)
    }

    return tree

def onSaveSettings():
    tree = build_zip_tree()

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo_struct.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=10)
    print("Tree generated and saved to repo_struct.json successfully!")

if __name__ == '__main__':
    onSaveSettings()
