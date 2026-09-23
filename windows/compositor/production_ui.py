"""General production pages, references and a distraction-free presentation surface."""
from pathlib import Path
import json
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QPainter
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,QListWidget,QListWidgetItem,
    QLineEdit,QPlainTextEdit,QLabel,QTextBrowser,QFileDialog,QInputDialog,QDialog,QCheckBox,QGraphicsView,QGraphicsScene,QMessageBox,QScrollArea,QTabWidget,QMenu)
from .chrome import icon_button, EditorComboBox as QComboBox


class ProductionPanel(QWidget):
    def __init__(self,editor):
        super().__init__(); self.editor=editor; self.ws=editor.ws; self.refreshing=False; self.key=None; self.drafts={}
        self.draft_path=self.ws.settings.root/'production-drafts.json'
        if self.draft_path.exists():
            try: self.drafts={tuple(row['key']):row['value'] for row in json.loads(self.draft_path.read_text(encoding='utf-8'))}
            except (ValueError,KeyError): pass
        self.draft_timer=QTimer(self); self.draft_timer.setSingleShot(True); self.draft_timer.setInterval(500); self.draft_timer.timeout.connect(self.save_drafts)
        root=QVBoxLayout(self); root.setContentsMargins(10,10,10,10); row=QHBoxLayout()
        for title,fn in [('New project',self.create),('Open…',self.open),('Save',self.save)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        menu=QMenu(self); menu.addAction('Save as…',lambda:self.save(save_as=True)); menu.addAction('Open a copy…',lambda:self.open(as_copy=True))
        more=QPushButton('⋯'); more.setFixedWidth(32); more.setAccessibleName('Project file options'); more.setToolTip('Project file options'); more.setMenu(menu); row.addWidget(more)
        root.addLayout(row); self.empty=QLabel('Create an artwork, comic or book.\n\nKeep its pages, references and writing together.'); self.empty.setWordWrap(True); self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter); root.addWidget(self.empty,1)
        self.body=QWidget(); scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame); scroll.setWidget(self.body); root.addWidget(scroll,1); layout=QVBoxLayout(self.body); layout.setContentsMargins(0,0,4,0); layout.setSpacing(8)
        self.projects=QComboBox(); self.projects.currentIndexChanged.connect(self.select_project); layout.addWidget(self.projects)
        self.file_status=QLabel(); self.file_status.setWordWrap(True); self.file_status.setStyleSheet('color:#aaa'); layout.addWidget(self.file_status)
        self.pages=QListWidget(); self.pages.setMinimumHeight(90); self.pages.setMaximumHeight(160); self.pages.itemClicked.connect(self.select_page); layout.addWidget(self.pages,1)
        row=QHBoxLayout()
        for name,title,fn in [('plus','Add page',self.add_page),('up','Move page earlier',lambda:self.reorder(-1)),('down','Move page later',lambda:self.reorder(1)),('delete','Remove page',self.remove_page)]: row.addWidget(icon_button(name,title,fn))
        row.addStretch()
        layout.addLayout(row)
        self.title=QLineEdit(); self.title.setPlaceholderText('Page title'); layout.addWidget(self.title)
        self.page_tabs=QTabWidget(); writing=QWidget(); writing_layout=QVBoxLayout(writing); writing_layout.setContentsMargins(6,8,6,6); self.page_tabs.addTab(writing,'Page'); direction=QWidget(); direction_layout=QVBoxLayout(direction); direction_layout.setContentsMargins(6,8,6,6); self.page_tabs.addTab(direction,'Style && cast'); layout.addWidget(self.page_tabs,1)
        writing_layout.addWidget(QLabel('Writing')); self.text=QPlainTextEdit(); self.text.setPlaceholderText('Page prose for reading and PDF exports'); self.text.setFixedHeight(85); writing_layout.addWidget(self.text)
        writing_layout.addWidget(QLabel('Image prompt')); self.prompt=QPlainTextEdit(); self.prompt.setPlaceholderText('Describe the scene for this page'); self.prompt.setFixedHeight(85); writing_layout.addWidget(self.prompt); writing_layout.addStretch()
        for field in (self.title,self.text,self.prompt): field.textChanged.connect(self.remember_draft)
        self.draft_status=QLabel(); writing_layout.addWidget(self.draft_status)
        from .creative_ui import GenerationRoutePicker
        layout.addWidget(GenerationRoutePicker(self.ws))
        row=QHBoxLayout()
        for title,fn in [('Save page text',self.save_text),('Generate page',self.generate)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        layout.addLayout(row)
        self.style_label=QLabel(); self.style_label.setWordWrap(True); direction_layout.addWidget(self.style_label)
        row=QHBoxLayout();
        for title,fn in [('Project style…',self.edit_style),('Characters…',self.characters)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        direction_layout.addLayout(row); direction_layout.addWidget(QLabel('Characters on this page'))
        self.cast=QListWidget(); self.cast.setMinimumHeight(80); self.cast.setMaximumHeight(110); self.cast.itemChanged.connect(self.choose_cast); direction_layout.addWidget(self.cast)
        row=QHBoxLayout()
        for title,fn in [('Project details',self.details),('Other references…',self.references)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        direction_layout.addLayout(row); direction_layout.addStretch()
        row=QHBoxLayout()
        for title,fn in [('Export reading copy',self.export),('Present',self.present)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        layout.addLayout(row); self.ws.changed.connect(self.refresh); self.refresh()

    def project(self): return self.ws.projects.items.get(self.projects.currentData())
    def call(self,operation,args=None):
        args=args or {}; project=self.project()
        if project and operation not in ('new','open'): args.setdefault('projectId',project['id'])
        return self.editor.run('production',{'operation':operation,'args':args})

    def refresh(self):
        self.refreshing=True
        try:
            self.projects.blockSignals(True); self.projects.clear()
            all_projects=list(self.ws.projects.items.values())
            for project in all_projects:
                duplicates=[p for p in all_projects if p['title']==project['title']]
                saved=self.ws.projects.files.get(project['id'],{}).get('path')
                label=project['title']
                if len(duplicates)>1: label+=' · '+(Path(saved).name if saved else f'Working copy {duplicates.index(project)+1}')
                self.projects.addItem(label,project['id']); self.projects.setItemData(self.projects.count()-1,saved or 'Working copy',Qt.ItemDataRole.ToolTipRole)
            self.projects.setCurrentIndex(max(0,self.projects.findData(self.ws.projects.active))); self.projects.blockSignals(False)
            project=self.project(); self.pages.clear(); self.body.setVisible(project is not None); self.empty.setVisible(project is None)
            if project:
                saved=self.ws.projects.files.get(project['id'],{}).get('path')
                self.file_status.setText(Path(saved).name if saved else 'Not saved to a project file'); self.file_status.setToolTip(saved or '')
                for i,page in enumerate(project['pages']):
                    item=QListWidgetItem(f"{i+1}. {page['title']}"); item.setData(Qt.ItemDataRole.UserRole,page['id']); self.pages.addItem(item)
                    if page['id']==project['activePage']: self.pages.setCurrentItem(item)
                page=self.ws.projects.page(project); self.key=(project['id'],page['id'])
                self.style_label.setText('Style: '+(project.get('style') or {}).get('name','None'))
                self.cast.clear()
                for character in project.get('characters',[]):
                    item=QListWidgetItem(character['name']); item.setData(Qt.ItemDataRole.UserRole,character['id']); item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked if character['id'] in page.get('characterIds',[]) else Qt.CheckState.Unchecked); self.cast.addItem(item)
                value=self.drafts.get(self.key,page)
                for field,key in ((self.title,'title'),(self.text,'text'),(self.prompt,'prompt')):
                    current=field.text() if isinstance(field,QLineEdit) else field.toPlainText()
                    if current!=value[key]: field.setText(value[key]) if isinstance(field,QLineEdit) else field.setPlainText(value[key])
            else:
                self.key=None; self.title.clear(); self.text.clear(); self.prompt.clear()
            self.draft_status.setText('Unsaved page text' if self.key in self.drafts else '')
        finally: self.refreshing=False

    def remember_draft(self):
        if self.refreshing or not self.key: return
        project=self.project(); page=self.ws.projects.page(project,self.key[1])
        existing=self.drafts.get(self.key)
        baseline=existing['baseline'] if existing else {key:page[key] for key in ('title','text','prompt')}
        self.drafts[self.key]={'title':self.title.text(),'text':self.text.toPlainText(),'prompt':self.prompt.toPlainText(),'baseline':baseline}
        self.draft_status.setText('Unsaved page text'); self.draft_timer.start()

    def save_drafts(self):
        from .settings import atomic_json
        atomic_json(self.draft_path,[{'key':list(k),'value':v} for k,v in self.drafts.items()])

    def save_text(self):
        if self.key not in self.drafts: return True
        key=self.key; draft=self.drafts[key]; page=self.ws.projects.page(self.project(),key[1])
        if any(page[k]!=draft['baseline'][k] for k in ('title','text','prompt')):
            answer=QMessageBox.question(self,'Page text changed','This page was edited elsewhere while you were writing. Replace its current text with your draft?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes: return False
        result=self.call('update_page',{'pageId':key[1],**{k:draft[k] for k in ('title','text','prompt')}})
        if result: self.drafts.pop(key,None); self.save_drafts(); self.refresh()
        return bool(result)

    def save_all_text(self):
        project=self.project()
        if not project: return False
        for key in list(self.drafts):
            if key[0]!=project['id']: continue
            original=self.key; self.key=key
            if not self.save_text(): self.key=original; self.refresh(); return False
            self.key=original
        self.refresh(); return True

    def select_project(self,index):
        if not self.refreshing and index>=0: self.call('select',{'projectId':self.projects.itemData(index)})
    def select_page(self,item): self.call('select',{'pageId':item.data(Qt.ItemDataRole.UserRole)})
    def create(self):
        from .creative_ui import NewProjectDialog
        dialog=NewProjectDialog(self)
        if dialog.exec()==QDialog.DialogCode.Accepted: self.call('new',dialog.values())

    def edit_style(self):
        from .creative_ui import StyleDialog
        if self.project(): StyleDialog(self.editor,self.project()).exec()
    def characters(self):
        from .creative_ui import CharacterDialog
        if self.project(): CharacterDialog(self.editor,self.project()).exec()
    def choose_cast(self,item):
        if self.refreshing or not self.key: return
        ids=[self.cast.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.cast.count()) if self.cast.item(i).checkState()==Qt.CheckState.Checked]
        self.call('update_page',{'pageId':self.key[1],'characterIds':ids})
    def open(self,checked=False,as_copy=False):
        path,_=QFileDialog.getOpenFileName(self,'Open a copy' if as_copy else 'Open project','','Compositor project (*.compbook)')
        if path: self.call('open',{'path':path,'asCopy':as_copy})
    def save(self,checked=False,save_as=False):
        project=self.project()
        if not project or not self.save_all_text(): return
        path=self.ws.projects.files.get(project['id'],{}).get('path')
        if not path or save_as: path,_=QFileDialog.getSaveFileName(self,'Save project',path or project['title']+'.compbook','Compositor project (*.compbook)')
        if path: return self.call('save',{'path':path,'projectId':project['id']})
    def add_page(self):
        if self.project(): self.call('add_page')
    def reorder(self,delta):
        project=self.project()
        if project and self.key:
            page=self.ws.projects.page(project,self.key[1]); self.call('reorder_page',{'pageId':page['id'],'index':project['pages'].index(page)+delta})
    def remove_page(self):
        if self.key: self.call('remove_page',{'pageId':self.key[1]})
    def details(self):
        project=self.project()
        if project:
            fields=self.editor.form_dialog('Project details',{k:project[k] for k in ('title','story','artDirection')})
            if fields: self.call('update',fields)
    def references(self):
        project=self.project()
        if not project: return
        dialog=QDialog(self); dialog.setWindowTitle('Project references'); dialog.resize(550,380); layout=QVBoxLayout(dialog); listing=QListWidget(); layout.addWidget(listing)
        def refresh():
            listing.clear()
            for reference in project['references']:
                item=QListWidgetItem(reference['role']+' · '+reference['label']); item.setData(Qt.ItemDataRole.UserRole,reference['id']); listing.addItem(item)
        def add():
            path,_=QFileDialog.getOpenFileName(dialog,'Add reference','','Images (*.png *.jpg *.jpeg *.webp *.tif *.heic)')
            if not path: return
            role,ok=QInputDialog.getItem(dialog,'Reference role','Use as',['character','style','composition'],0,False)
            if ok: self.call('add_reference',{'path':path,'role':role,'projectId':project['id']}); refresh()
        def remove():
            if listing.currentItem(): self.call('remove_reference',{'referenceId':listing.currentItem().data(Qt.ItemDataRole.UserRole),'projectId':project['id']}); refresh()
        row=QHBoxLayout()
        for title,fn in [('Add…',add),('Remove',remove),('Close',dialog.accept)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        layout.addLayout(row); refresh(); dialog.exec()
    def generate(self):
        if not self.project() or not self.save_text(): return
        result=self.call('generate',{'pageId':self.key[1]})
        if result: self.editor.show_panel(self.editor.chat_dock if result.get('route')=='chatgpt' else self.editor.generation_dock)
    def export(self):
        project=self.project()
        if not project or not self.save_all_text(): return
        path,_=QFileDialog.getSaveFileName(self,'Export reading copy',project['title']+'.html','Portable reading copy (*.html);;PDF (*.pdf)')
        if path: self.call('export',{'path':path,'projectId':project['id']})
    def present(self,project=None,two_panels=False):
        project=project if isinstance(project,dict) else self.project()
        if project:
            if hasattr(self,'presentation'): self.presentation.close()
            self.presentation=Presentation(self.editor,project); self.presentation.panels.setChecked(two_panels); self.presentation.showFullScreen()


class Presentation(QDialog):
    def __init__(self,editor,project):
        super().__init__(editor); self.editor=editor; self.project=project; self.index=next((i for i,p in enumerate(project['pages']) if p['id']==project['activePage']),0)
        self.setWindowTitle(project['title']); self.setStyleSheet('QDialog{background:#15171b;color:white} QPushButton,QCheckBox{min-height:32px;min-width:32px}')
        layout=QVBoxLayout(self); row=QHBoxLayout(); self.label=QLabel(); row.addWidget(self.label); row.addStretch()
        self.panels=QCheckBox('Two panels'); self.panels.toggled.connect(self.render); row.addWidget(self.panels)
        for title,fn in [('Previous',lambda:self.step(-1)),('Next',lambda:self.step(1)),('Close',self.close)]:
            button=QPushButton(title); button.clicked.connect(fn); row.addWidget(button)
        layout.addLayout(row); self.view=QGraphicsView(); self.view.setScene(QGraphicsScene(self.view)); self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform); layout.addWidget(self.view)
        self.prose=QTextBrowser(); self.prose.setMaximumHeight(200); self.prose.setStyleSheet('font-size:22px;padding:12px'); layout.addWidget(self.prose)
        QShortcut(QKeySequence('Right'),self,activated=lambda:self.step(1)); QShortcut(QKeySequence('Left'),self,activated=lambda:self.step(-1)); QShortcut(QKeySequence('Escape'),self,activated=self.close)
        self.editor.ws.changed.connect(self.sync); self.render()
    def sync(self):
        self.index=next((i for i,p in enumerate(self.project['pages']) if p['id']==self.project['activePage']),0); self.render()
    def step(self,delta):
        index=max(0,min(len(self.project['pages'])-1,self.index+delta))
        self.editor.ws.dispatch('production',{'operation':'select','args':{'projectId':self.project['id'],'pageId':self.project['pages'][index]['id']}})
    def render(self):
        from .ui import pixmap
        page=self.project['pages'][self.index]; image=self.editor.ws.projects.document(self.project,page).render()
        self.editor.ws.view['presentation']={'projectId':self.project['id'],'pageId':page['id'],'twoPanels':self.panels.isChecked()}
        self.view.scene().clear(); split=page.get('splitY') or image.height//2
        if self.panels.isChecked():
            first=image.crop((0,0,image.width,split)); second=image.crop((0,split,image.width,image.height))
            self.view.scene().addPixmap(pixmap(first)); item=self.view.scene().addPixmap(pixmap(second)); item.setPos(first.width+32,0)
        else: self.view.scene().addPixmap(pixmap(image))
        self.label.setText(f"{self.project['title']} · {self.index+1} / {len(self.project['pages'])}"); self.prose.setPlainText(page['text']); self.prose.setVisible(bool(page['text']))
        self.fit()
    def fit(self): self.view.fitInView(self.view.scene().itemsBoundingRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def resizeEvent(self,event): super().resizeEvent(event); self.fit()
    def closeEvent(self,event):
        self.editor.ws.changed.disconnect(self.sync); self.editor.ws.view.pop('presentation',None); super().closeEvent(event)
