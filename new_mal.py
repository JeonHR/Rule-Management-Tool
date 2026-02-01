import sys
import json
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QListWidget,
    QMessageBox, QLineEdit, QFormLayout, QGroupBox,
    QFileDialog
)
from PyQt5.QtCore import Qt

CONFIG_PATH = "product_config.json"


# ----------------------
# JSON
# ----------------------
def load_config():
    try: 
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f) 
            
        return {"products": {}} 
    
    except FileNotFoundError:
        return {"products": {}}


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False) 


# ----------------------
# TXT ENGINE
# ----------------------
def apply_txt_rule(rule):
    txt = rule["txt_path"] 
    match_paths = rule["match_paths"]
    new_path = rule["new_path"]

    if not os.path.exists(txt):
        raise RuntimeError(f"TXT_NOT_FOUND: {txt}")

    with open(txt, "r", encoding="utf-8") as f:
        lines = f.readlines()

    hit = []
    for i, line in enumerate(lines):
        if any(p in line for p in match_paths):
            hit.append(i)

    if len(hit) == 0:
        raise RuntimeError(f"NO_MATCH: {txt}")
    if len(hit) > 1:
        raise RuntimeError(f"MULTI_MATCH: {txt}")

    idx = hit[0]
    for p in match_paths:
        if p in lines[idx]:
            lines[idx] = lines[idx].replace(p, new_path)

    with open(txt, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ----------------------
# FILE ENGINE
# ----------------------
def apply_file_rule(rule):
    if not os.path.exists(rule["source"]):
        raise RuntimeError("SRC_NOT_FOUND")
    
    if not os.path.exists(os.path.dirname(rule["destination"])):
        os.makedirs(os.path.dirname(rule["destination"]), exist_ok=True)
    
       
    try : 
        shutil.copy(rule["source"], rule["destination"])
    except Exception as e:
        raise RuntimeError(f"FILE_COPY_ERROR: {e}")


# ----------------------
# UI
# ----------------------
class ProductManagerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Version Manager - HR")
        self.resize(900, 650)
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        main = QVBoxLayout()

        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode"))
        self.mode = QComboBox()
        self.mode.addItems(["Operator", "ENG"])
        self.mode.currentTextChanged.connect(self.on_mode_change)
        mode_layout.addWidget(self.mode)
        mode_layout.addStretch()
        main.addLayout(mode_layout)




        # Product / Version
        # hl = QHBoxLayout()
        # self.product_list = QListWidget()
        # self.version_list = QListWidget()
        # self.product_list.currentTextChanged.connect(self.refresh_versions)
        # hl.addWidget(self.wrap("Product", self.product_list))
        # hl.addWidget(self.wrap("Version", self.version_list))
        # main.addLayout(hl)

        hl = QHBoxLayout()
        self.product_list = QListWidget()
        self.version_list = QListWidget()
        self.product_list.currentTextChanged.connect(self.refresh_versions)
        self.version_list.currentTextChanged.connect(self.load_rules)

        # Product 영역
        prod_layout = QVBoxLayout()
        prod_layout.addWidget(self.wrap("Product", self.product_list))

        self.btn_del_product = QPushButton("Delete Product")
        self.btn_del_product.clicked.connect(self.delete_product)
        self.btn_del_product.setVisible(False)
        prod_layout.addWidget(self.btn_del_product)

        prod_container = QWidget()
        prod_container.setLayout(prod_layout)
        
        hl.addWidget(prod_container)

        # Version 영역
        ver_layout = QVBoxLayout()
        ver_layout.addWidget(self.wrap("Version", self.version_list))

        self.btn_del_version = QPushButton("Delete Version")
        self.btn_del_version.clicked.connect(self.delete_version)
        self.btn_del_version.setVisible(False)
        ver_layout.addWidget(self.btn_del_version)

        ver_container = QWidget()
        ver_container.setLayout(ver_layout)
        hl.addWidget(ver_container)

        main.addLayout(hl)



        # ---------------------- ENG UI ----------------------
        self.eng = QGroupBox("ENG Builder")
        form = QFormLayout() # 폼 레이아웃 사용

        self.change_type = QComboBox()
        self.change_type.addItems(["TXT_PATH_CHANGE", "FILE_CHANGE"])
        self.change_type.currentTextChanged.connect(self.on_change_type)

        self.in_product = QLineEdit()
        self.in_version = QLineEdit()

        form.addRow("Change Type", self.change_type)
        form.addRow("Product", self.in_product)
        form.addRow("Version", self.in_version)

        # --------------------- TXT rule ---------------------
        self.txt_group = QGroupBox("TXT Rule (1 file = 1 rule)")
        tv = QVBoxLayout()

        self.in_txt = QLineEdit()
        self.btn_txt = QPushButton("Browse")
        self.btn_txt.clicked.connect(self.browse_txt)

        h1 = QHBoxLayout()
        h1.addWidget(self.in_txt)
        h1.addWidget(self.btn_txt)

        self.in_match = QLineEdit()
        self.in_match.setPlaceholderText("D:/OLD_A, E:/OLD_B") # 매치 경로들 쉼표로 구분

        self.in_new = QLineEdit()
        self.btn_new = QPushButton("Browse")
        self.btn_new.clicked.connect(self.browse_new)

        h2 = QHBoxLayout()
        h2.addWidget(self.in_new)
        h2.addWidget(self.btn_new)

        
        self.rule_list = QListWidget()
        self.btn_add_rule = QPushButton("Add TXT Rule")
        self.btn_add_rule.clicked.connect(self.add_txt_rule)

        self.btn_delete_rule = QPushButton("Delete Selected")
        self.btn_delete_rule.clicked.connect(self.delete_txt_rule)
        
        h3 = QHBoxLayout()
        h3.addWidget(self.btn_add_rule)
        h3.addWidget(self.btn_delete_rule)
        
        tv.addLayout(h1)
        tv.addWidget(QLabel("Match Paths"))
        tv.addWidget(self.in_match)
        tv.addWidget(QLabel("New Path"))
        tv.addLayout(h2)
        tv.addLayout(h3)
        tv.addWidget(self.rule_list)

        self.txt_group.setLayout(tv)
        form.addRow(self.txt_group)

        # FILE rule
        self.file_group = QGroupBox("FILE Change")
        fv = QFormLayout()
        self.in_src = QLineEdit()
        self.in_dst = QLineEdit()
        fv.addRow("Source", self.in_src)
        fv.addRow("Destination", self.in_dst)
        self.file_group.setLayout(fv)
        form.addRow(self.file_group)

        self.btn_save = QPushButton("Save Version")
        self.btn_save.clicked.connect(self.save_version) # 버튼 클릭시 저장
        form.addRow(self.btn_save)

        self.eng.setLayout(form)
        main.addWidget(self.eng)

        # Execute
        self.btn_exec = QPushButton("Execute")
        self.btn_exec.clicked.connect(self.execute)
        main.addWidget(self.btn_exec, alignment=Qt.AlignRight)

        self.setLayout(main)
        self.refresh_products()
        self.on_mode_change(self.mode.currentText())
        self.on_change_type(self.change_type.currentText())

    # ----------------
    def wrap(self, t, w):
        v = QVBoxLayout()
        v.addWidget(QLabel(t))
        v.addWidget(w)
        c = QWidget()
        c.setLayout(v)
        return c

    def on_mode_change(self, m):
        self.eng.setVisible(m == "ENG")

        self.btn_del_product.setVisible(m == "ENG")
        self.btn_del_version.setVisible(m == "ENG")
        self.btn_delete_rule.setVisible(m == "ENG")



    def on_change_type(self, t):
        self.txt_group.setVisible(t == "TXT_PATH_CHANGE")
        self.file_group.setVisible(t == "FILE_CHANGE")

    # ---------------- TXT rule build
    def browse_txt(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select TXT", "", "All Files (*)")
        if f:
            self.in_txt.setText(f)

    def browse_new(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.in_new.setText(d)

    def add_txt_rule(self):
        rule = {
            "txt_path": self.in_txt.text().strip(),
            "match_paths": [x.strip() for x in self.in_match.text().split(",") if x.strip()],
            "new_path": self.in_new.text().strip()
        }
        self.rule_list.addItem(json.dumps(rule, ensure_ascii=False))

    # ---------------- Save
    def save_version(self): # 저장 버튼 클릭시 호출 
        p, v = self.in_product.text().strip(), self.in_version.text().strip()
        if not p or not v:
            QMessageBox.warning(self, "Error", "Product / Version required")
            return

        rules = []
        for i in range(self.rule_list.count()):
            rules.append(json.loads(self.rule_list.item(i).text())) # 룰 리스트에서 룰 불러오기

        self.config["products"].setdefault(p, {"versions": {}}) 
        self.config["products"][p]["versions"][v] = {
            "change_type": self.change_type.currentText(),
            "rules": rules
        }

        save_config(self.config)
        self.refresh_products()
        QMessageBox.information(self, "Saved", f"{p} / {v} saved")

    # ---------------- Execute
    def execute(self):
        p = self.product_list.currentItem()
        v = self.version_list.currentItem()
        if not p or not v:
            return

        cfg = self.config["products"][p.text()]["versions"][v.text()]
        for r in cfg["rules"]:
            if cfg["change_type"] == "TXT_PATH_CHANGE":
                apply_txt_rule(r)
            else:
                apply_file_rule(r)

        QMessageBox.information(self, "Done", "Completed")

    # ---------------- Refresh
    def refresh_products(self):
        self.product_list.clear()
        for p in self.config["products"]:
            self.product_list.addItem(p)

    def refresh_versions(self, p):
        self.version_list.clear()
        if p:
            for v in self.config["products"][p]["versions"]:
                self.version_list.addItem(v)
    # ---------------- Delete Rule
    # 클래스 내 새 메서드 추가
    
    def delete_txt_rule(self):
        selected = self.rule_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "경고", "삭제할 규칙을 선택해 주십시오.")
            return

        p_item = self.product_list.currentItem()
        v_item = self.version_list.currentItem()

        if not p_item or not v_item:
            QMessageBox.warning(self, "경고", "Product와 Version을 먼저 선택해 주십시오.")
            return

        product = p_item.text()
        version = v_item.text()

        reply = QMessageBox.question(
            self,
            "규칙 삭제 확인",
            f"선택한 {len(selected)}개 규칙을 정말 삭제하시겠습니까?\n(복구 불가)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        rules_list = self.config["products"][product]["versions"][version]["rules"]

        # UI에 표시된 순서대로 인덱스를 모음 (역순으로 처리)
        rows_to_remove = sorted([self.rule_list.row(item) for item in selected], reverse=True)

        for row in rows_to_remove:
            # UI에서 제거
            self.rule_list.takeItem(row)

            # config에서도 같은 순서의 항목 제거
            if row < len(rules_list):
                del rules_list[row]

        save_config(self.config)
        QMessageBox.information(self, "완료", f"{len(rows_to_remove)}개 규칙이 삭제되었습니다.")   

    # 새 메서드 추가 (클래스 내부)
    def delete_product(self):
        item = self.product_list.currentItem()
        if not item:
            QMessageBox.warning(self, "경고", "삭제할 제품을 선택해 주십시오.")
            return

        product_name = item.text()
        version_count = len(self.config["products"][product_name]["versions"])

        msg = (f"제품 '{product_name}'을 삭제하시겠습니까?\n"
            f"→ 포함된 버전 {version_count}개가 모두 함께 삭제됩니다.\n"
            "이 작업은 되돌릴 수 없습니다.")

        reply = QMessageBox.question(
            self, "제품 삭제 확인", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.config["products"][product_name]
            save_config(self.config)
            self.refresh_products()
            self.version_list.clear()
            QMessageBox.information(self, "완료", f"제품 '{product_name}'이 삭제되었습니다.")

    def delete_version(self):
        p_item = self.product_list.currentItem()
        v_item = self.version_list.currentItem()

        if not p_item or not v_item:
            QMessageBox.warning(self, "경고", "삭제할 버전을 선택해 주십시오.")
            return

        product = p_item.text()
        version = v_item.text()

        msg = f"버전 '{version}' ({product})을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다."

        reply = QMessageBox.question(
            self, "버전 삭제 확인", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.config["products"][product]["versions"][version]

            # 버전이 모두 사라졌다면 제품도 자동 삭제 (선택 사항)
            if not self.config["products"][product]["versions"]:
                del self.config["products"][product]
                self.refresh_products()
                self.version_list.clear()
            else:
                self.refresh_versions(product)

            save_config(self.config)
            QMessageBox.information(self, "완료", f"버전 '{version}'이 삭제되었습니다.")

    def load_rules(self, version):
        self.rule_list.clear()

        p_item = self.product_list.currentItem()
        if not p_item or not version:
            return

        product = p_item.text()
        rules = self.config["products"][product]["versions"][version]["rules"]

        for r in rules:
            self.rule_list.addItem(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ProductManagerUI()
    ui.show()
    sys.exit(app.exec_())
