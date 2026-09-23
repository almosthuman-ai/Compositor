"""Style direction, project cast and reference sheets in the shared editor."""
from pathlib import Path
from PySide6.QtCore import Qt,QSize,QUrl
from PySide6.QtGui import QIcon,QPixmap,QDesktopServices
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QPlainTextEdit,
    QPushButton,QDialogButtonBox,QListWidget,QListWidgetItem,QFileDialog,QSplitter,QWidget,QInputDialog,QSpinBox)
from .chrome import EditorComboBox as QComboBox


def button(row,label,fn):
    value=QPushButton(label); value.clicked.connect(fn); row.addWidget(value); return value


class GenerationRoutePicker(QWidget):
    def __init__(self,workspace):
        super().__init__(); self.ws=workspace; row=QHBoxLayout(self); row.setContentsMargins(0,0,0,0); row.addWidget(QLabel('Generate with'))
        self.choice=QComboBox(); self.choice.setAccessibleName('Generation route'); self.choice.addItem('API provider','api'); self.choice.addItem('ChatGPT subscription','chatgpt'); row.addWidget(self.choice,1)
        self.choice.currentIndexChanged.connect(self.choose); self.ws.changed.connect(self.refresh); self.refresh()
    def refresh(self):
        self.choice.blockSignals(True); self.choice.setCurrentIndex(max(0,self.choice.findData(self.ws.settings.values['generationRoute']))); self.choice.blockSignals(False)
    def choose(self,index): self.ws.dispatch('settings',{'generationRoute':self.choice.itemData(index)})


class StyleDialog(QDialog):
    def __init__(self,editor,project=None,style_id=None):
        super().__init__(editor); self.editor=editor; self.ws=editor.ws; self.project=project; self.selected_id=style_id; self.refs=[]; self.loaded=None
        self.setWindowTitle('Project style' if project else 'Style library'); self.resize(720,690)
        root=QVBoxLayout(self); root.setContentsMargins(20,18,20,18); root.setSpacing(10)
        self.choice=QComboBox(); self.choice.setAccessibleName('Style'); root.addWidget(self.choice)
        self.name=QLineEdit(); self.name.setAccessibleName('Style name'); root.addWidget(QLabel('Style name')); root.addWidget(self.name)
        self.prefix=QPlainTextEdit(); self.suffix=QPlainTextEdit()
        for title,field in [('Before your prompt',self.prefix),('After your prompt',self.suffix)]:
            root.addWidget(QLabel(title)); field.setAccessibleName(title); root.addWidget(field,1)
        root.addWidget(QLabel('Style references')); self.references=QListWidget(); self.references.setIconSize(QSize(64,48)); self.references.setMaximumHeight(110); root.addWidget(self.references)
        row=QHBoxLayout(); button(row,'Add image…',self.add_reference); button(row,'Remove image',self.remove_reference); row.addStretch(); root.addLayout(row)
        self.message=QLabel('Style direction is included automatically with each image request.'); self.message.setWordWrap(True); root.addWidget(self.message)
        row=QHBoxLayout(); button(row,'Save to library',self.save_library); button(row,'Save as new style',lambda:self.save_library(as_copy=True)); row.addStretch(); root.addLayout(row)
        controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); controls.button(QDialogButtonBox.StandardButton.Ok).setText('Use style'); controls.accepted.connect(self.apply); controls.rejected.connect(self.reject); root.addWidget(controls)
        self.choice.currentIndexChanged.connect(self.load); self.fill()

    def fill(self,chosen=None):
        self.choice.blockSignals(True); self.choice.clear(); self.choice.addItem('No style',None)
        if self.project and self.project.get('style'): self.choice.addItem('Current project style','project')
        for style in self.ws.styles.list(): self.choice.addItem(style['name'],style['id'])
        key=chosen or ('project' if self.project and self.project.get('style') else self.selected_id)
        self.choice.setCurrentIndex(max(0,self.choice.findData(key))); self.choice.blockSignals(False); self.load()

    def load(self,*args):
        key=self.choice.currentData()
        if key=='project':
            style=dict(self.project['style']); style['references']=[{'path':str(self.ws.projects.folder(self.project)/r['file']),'label':r['label']} for r in self.project['references'] if r.get('styleOwned')]
        else: style=self.ws.styles.get(key) if key else {}
        self.loaded=style; self.name.setText(style.get('name','')); self.prefix.setPlainText(style.get('prefix','')); self.suffix.setPlainText(style.get('suffix','')); self.refs=list(style.get('references',[])); self.render_references()

    def render_references(self):
        self.references.clear()
        for ref in self.refs: self.references.addItem(QListWidgetItem(QIcon(ref['path']),ref.get('label',Path(ref['path']).stem)))

    def add_reference(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Style reference images','','Images (*.png *.jpg *.jpeg *.webp *.tif)')
        self.refs.extend({'path':p,'label':Path(p).stem,'role':'style'} for p in paths); self.render_references()
    def remove_reference(self):
        index=self.references.currentRow()
        if index>=0: self.refs.pop(index); self.render_references()
    def values(self): return {'name':self.name.text(),'prefix':self.prefix.toPlainText(),'suffix':self.suffix.toPlainText(),'references':self.refs}

    def save_library(self,checked=False,as_copy=False):
        values=self.values()
        if not as_copy and self.loaded and not self.loaded.get('builtin') and self.choice.currentData()!='project': values['id']=self.loaded['id']
        try:
            result=self.ws.dispatch('save_style',values); self.fill(result['id']); self.message.setText('Saved to your style library. Existing projects keep their own style direction.')
        except Exception as error: self.message.setText(str(error))

    def apply(self):
        try:
            key=self.choice.currentData(); values=self.values()
            if key is None and not any((values['name'],values['prefix'],values['suffix'],values['references'])): chosen=None
            elif self.loaded and all(values[k]==self.loaded.get(k,[] if k=='references' else '') for k in values) and key!='project': chosen=key
            elif key=='project' and values['references']==self.loaded.get('references',[]):
                self.ws.dispatch('production',{'operation':'update_style','args':{'projectId':self.project['id'],**{k:values[k] for k in ('name','prefix','suffix')}}}); self.accept(); return
            else: chosen=self.ws.dispatch('save_style',values)['id']
            if self.project: self.ws.dispatch('production',{'operation':'set_style','args':{'projectId':self.project['id'],'styleId':chosen}})
            self.selected_id=chosen; self.accept()
        except Exception as error: self.message.setText(str(error))


class CharacterDialog(QDialog):
    def __init__(self,editor,project):
        super().__init__(editor); self.editor=editor; self.ws=editor.ws; self.project=project; self.current=None; self.baseline=None
        self.setWindowTitle('Characters — '+project['title']); self.resize(880,700)
        root=QVBoxLayout(self); root.setContentsMargins(18,18,18,18); split=QSplitter(); root.addWidget(split,1)
        left=QWidget(); col=QVBoxLayout(left); col.setContentsMargins(0,0,12,0); col.addWidget(QLabel('Project characters'))
        self.cast=QListWidget(); self.cast.setMinimumWidth(190); self.cast.setIconSize(QSize(48,48)); col.addWidget(self.cast,1)
        row=QHBoxLayout(); button(row,'Add…',self.add); button(row,'Remove',self.remove); col.addLayout(row); split.addWidget(left)
        right=QWidget(); form=QVBoxLayout(right); form.setContentsMargins(0,0,0,0); self.name=QLineEdit(); form.addWidget(QLabel('Name')); form.addWidget(self.name)
        form.addWidget(QLabel('Identity & appearance')); self.description=QPlainTextEdit(); self.description.setPlaceholderText('Face, build, clothing, colors and other details that should stay consistent.'); self.description.setMaximumHeight(125); form.addWidget(self.description)
        row=QHBoxLayout(); button(row,'Save character',self.save); row.addStretch(); form.addLayout(row)
        form.addWidget(QLabel('Character references')); self.references=QListWidget(); self.references.setIconSize(QSize(80,72)); self.references.setMinimumHeight(90); form.addWidget(self.references,1)
        row=QHBoxLayout(); button(row,'Attach image…',self.attach); button(row,'Remove reference',self.remove_reference); form.addLayout(row)
        form.addWidget(QLabel('Reference sheet candidates')); self.candidates=QListWidget(); self.candidates.setIconSize(QSize(80,72)); form.addWidget(self.candidates,1)
        form.addWidget(GenerationRoutePicker(self.ws)); row=QHBoxLayout(); button(row,'Generate sheet',self.generate); button(row,'Inspect',self.inspect_candidate); button(row,'Use reference',self.accept_candidate); form.addLayout(row); split.addWidget(right); split.setSizes([220,620])
        self.message=QLabel('Choose the characters on each page in the Projects panel.'); self.message.setWordWrap(True); root.addWidget(self.message)
        row=QHBoxLayout(); row.addStretch(); button(row,'Close',self.accept); root.addLayout(row)
        self.cast.currentItemChanged.connect(self.select); self.ws.changed.connect(self.refresh); self.refresh()

    def action(self,operation,**args):
        try: return self.ws.dispatch('production',{'operation':operation,'args':{'projectId':self.project['id'],**args}})
        except Exception as error: self.message.setText(str(error)); return None
    def refresh(self):
        selected=self.current
        if selected and not any(c['id']==selected for c in self.project.get('characters',[])):
            self.current=None; self.baseline=None; self.name.clear(); self.description.clear()
        self.cast.blockSignals(True); self.cast.clear()
        for character in self.project.get('characters',[]):
            item=QListWidgetItem(character['name']); item.setData(Qt.ItemDataRole.UserRole,character['id'])
            ref=next((r for r in self.project['references'] if r.get('characterId')==character['id']),None)
            if ref: item.setIcon(QIcon(str(self.ws.projects.folder(self.project)/ref['file'])))
            self.cast.addItem(item)
            if selected==character['id']: self.cast.setCurrentItem(item)
        self.cast.blockSignals(False)
        if not self.cast.currentItem() and self.cast.count(): self.cast.setCurrentRow(0)
        self.refresh_images()
    def select(self,item,previous=None):
        if not item: return
        cid=item.data(Qt.ItemDataRole.UserRole)
        # Changing cast selection preserves an unfinished draft until explicitly saved.
        if self.current and self.baseline and (self.name.text(),self.description.toPlainText())!=self.baseline:
            if not self.save():
                self.refresh(); return
        self.current=cid; character=self.ws.projects.character(self.project,self.current)
        self.name.setText(character['name']); self.description.setPlainText(character['description']); self.baseline=(character['name'],character['description']); self.refresh_images()
        self.cast.blockSignals(True)
        for i in range(self.cast.count()):
            if self.cast.item(i).data(Qt.ItemDataRole.UserRole)==cid: self.cast.setCurrentRow(i); break
        self.cast.blockSignals(False)
    def refresh_images(self):
        self.references.clear(); self.candidates.clear()
        for ref in self.project['references']:
            if ref.get('characterId')==self.current:
                item=QListWidgetItem(QIcon(str(self.ws.projects.folder(self.project)/ref['file'])),ref['label']); item.setData(Qt.ItemDataRole.UserRole,ref['id']); self.references.addItem(item)
        for job in sorted(self.ws.generation.jobs.values(),key=lambda j:j['created'],reverse=True):
            context=job.get('creativeContext',{})
            if context.get('projectId')!=self.project['id'] or context.get('characterId')!=self.current: continue
            used=any(r.get('generationId')==job['id'] for r in self.project['references'])
            item=QListWidgetItem(('In use' if used else job['status'].title())+' · '+job.get('userPrompt',job['prompt'])[:45]); item.setData(Qt.ItemDataRole.UserRole,job['id']); item.setToolTip(job.get('error') or job['prompt'])
            if job.get('result'): item.setIcon(QIcon(job['result']))
            self.candidates.addItem(item)
        if self.candidates.count(): self.candidates.setCurrentRow(0)
    def add(self):
        name,ok=QInputDialog.getText(self,'New character','Name')
        if ok and name.strip():
            result=self.action('add_character',name=name)
            if result:
                cid=result['characters'][-1]['id']
                for i in range(self.cast.count()):
                    if self.cast.item(i).data(Qt.ItemDataRole.UserRole)==cid: self.cast.setCurrentRow(i); break
    def save(self):
        if not self.current: return False
        character=self.ws.projects.character(self.project,self.current)
        if self.baseline!=(character['name'],character['description']):
            self.baseline=(character['name'],character['description']); self.message.setText('This character changed elsewhere. Your draft is kept. Save again to replace its current details.'); return False
        result=self.action('update_character',characterId=self.current,name=self.name.text(),description=self.description.toPlainText())
        if result: self.baseline=(self.name.text().strip(),self.description.toPlainText().strip()); self.name.setText(self.baseline[0]); self.description.setPlainText(self.baseline[1]); self.message.setText('Character saved.')
        return bool(result)
    def remove(self):
        if self.current:
            cid=self.current; self.current=None; self.baseline=None; self.name.clear(); self.description.clear(); self.action('remove_character',characterId=cid)
    def attach(self):
        if not self.current: return
        paths,_=QFileDialog.getOpenFileNames(self,'Character reference images','','Images (*.png *.jpg *.jpeg *.webp *.tif)')
        for path in paths: self.action('add_reference',path=path,characterId=self.current)
    def remove_reference(self):
        if self.references.currentItem(): self.action('remove_reference',referenceId=self.references.currentItem().data(Qt.ItemDataRole.UserRole))
    def generate(self):
        if self.save():
            result=self.action('generate_character',characterId=self.current)
            if result:
                self.message.setText('Request sent to ChatGPT.' if result.get('route')=='chatgpt' else 'Generating a reference sheet. Review the candidate, then choose Use reference.')
                if result.get('route')=='chatgpt': self.editor.chat.status.connect(self.message.setText,Qt.ConnectionType.UniqueConnection)
    def accept_candidate(self):
        if self.current and self.candidates.currentItem(): self.action('accept_character_reference',characterId=self.current,jobId=self.candidates.currentItem().data(Qt.ItemDataRole.UserRole))
    def inspect_candidate(self):
        if self.candidates.currentItem():
            job=self.ws.generation.jobs[self.candidates.currentItem().data(Qt.ItemDataRole.UserRole)]
            if job.get('result'): QDesktopServices.openUrl(QUrl.fromLocalFile(job['result']))
    def done(self,result):
        if self.current and self.baseline and (self.name.text(),self.description.toPlainText())!=self.baseline:
            if not self.save(): return
        self.ws.changed.disconnect(self.refresh); super().done(result)


class NewProjectDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent); self.setWindowTitle('New project'); self.resize(480,360); root=QVBoxLayout(self); form=QFormLayout(); root.addLayout(form)
        self.title=QLineEdit('Untitled project'); form.addRow('Title',self.title); self.kind=QComboBox()
        for label,value in [('Artwork','artwork'),('Comic','comic'),('Illustrated book','book')]: self.kind.addItem(label,value)
        form.addRow('Format',self.kind); self.count=QSpinBox(); self.count.setRange(1,64); form.addRow('Pages',self.count)
        self.width=QSpinBox(); self.height=QSpinBox()
        for label,widget,value in [('Width',self.width,1536),('Height',self.height,1024)]: widget.setRange(1,16384); widget.setValue(value); widget.setSuffix(' px'); form.addRow(label,widget)
        self.kind.currentIndexChanged.connect(lambda _:self.count.setValue(1 if self.kind.currentData()=='artwork' else 4))
        hint=QLabel('Add a project style and characters after creating your pages.'); hint.setWordWrap(True); root.addWidget(hint); root.addStretch()
        controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); controls.button(QDialogButtonBox.StandardButton.Ok).setText('Create project'); controls.accepted.connect(self.accept); controls.rejected.connect(self.reject); root.addWidget(controls)
    def values(self): return {'title':self.title.text(),'kind':self.kind.currentData(),'pageCount':self.count.value(),'width':self.width.value(),'height':self.height.value()}
