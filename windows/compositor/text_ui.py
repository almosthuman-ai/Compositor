"""Typography editing with installed faces and the document's actual text renderer."""
from PySide6.QtCore import Qt,QTimer,QEvent
from PySide6.QtGui import QColor,QPainter,QPixmap,QImage
from PySide6.QtWidgets import (QDialog,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPlainTextEdit,QSpinBox,
    QPushButton,QDialogButtonBox,QColorDialog)
from .chrome import EditorComboBox as QComboBox
from . import fonts,pixels
from .document import Layer


class TextProperties(QWidget):
    """Immediate type controls; unfinished input stays with its original layer."""
    def __init__(self,editor):
        super().__init__(); self.editor=editor; self.ws=editor.ws; self.target=None; self.syncing=False; self.dirty=set(); self.baselines={}; self.displayed={}
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(6)
        self.heading=QLabel('Character'); layout.addWidget(self.heading)
        self.family=QComboBox(); self.family.setEditable(True); self.family.addItems(fonts.families()); self.family.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.family.setAccessibleName('Font family'); self.family.setToolTip('Font family'); self.family.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); layout.addWidget(self.family)
        row=QHBoxLayout(); row.setSpacing(8)
        self.face=QComboBox(); self.face.setAccessibleName('Font style'); self.face.setToolTip('Font style'); row.addWidget(self.face,1)
        self.size=QSpinBox(); self.size.setRange(1,2048); self.size.setSuffix(' px'); self.size.setKeyboardTracking(False); self.size.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons); self.size.setFixedWidth(84)
        self.size.setAccessibleName('Font size'); self.size.setToolTip('Font size'); row.addWidget(self.size); layout.addLayout(row)
        self.message=QLabel(); self.message.setWordWrap(True); self.message.hide(); layout.addWidget(self.message)
        self.family.lineEdit().textEdited.connect(lambda:self.begin('family'))
        self.family.lineEdit().editingFinished.connect(lambda:self.apply('family'))
        self.family.activated.connect(lambda:self.choose('family'))
        self.face.activated.connect(lambda:self.choose('face'))
        self.size.lineEdit().textEdited.connect(lambda:self.begin('size'))
        self.size.valueChanged.connect(lambda:self.begin('size'))
        self.size.editingFinished.connect(lambda:self.apply('size'))
        for widget in (self.family,self.family.lineEdit(),self.face,self.size,self.size.lineEdit()): widget.installEventFilter(self)

    def eventFilter(self,watched,event):
        if event.type()==QEvent.Type.KeyPress and event.key()==Qt.Key.Key_Escape and self.dirty:
            self.dirty.clear(); self.baselines.clear(); self.message.hide(); self.refresh(); return True
        return super().eventFilter(watched,event)

    def field_value(self,params,field):
        if field=='size': return params.get('size',48)
        return tuple(params.get(key) for key in ('fontFamily','fontStyle','font','fontIndex'))

    def begin(self,field):
        if self.syncing or not self.target: return
        if field not in self.dirty: self.baselines[field]=self.field_value(self.displayed,field)
        self.dirty.add(field)

    def choose(self,field):
        self.begin(field); self.apply(field)

    def feedback(self,text):
        self.message.setText(text); self.message.show()

    def refresh(self):
        selected=None
        if self.ws.active:
            document=self.ws.document()
            if document.active and document.layer().kind=='text': selected=(document.id,document.active)
        if not self.dirty: self.target=selected
        self.setVisible(self.target is not None)
        if not self.target: return
        try: layer=self.ws.document(self.target[0]).layer(self.target[1])
        except ValueError:
            self.feedback('This text layer is no longer open. Esc discards the unfinished change.'); return
        if layer.kind!='text':
            self.feedback('This layer no longer contains editable text. Esc discards the unfinished change.'); return
        self.syncing=True
        try:
            params=layer.params; face=fonts.identify(params)
            self.heading.setText('Character' if self.target==selected else 'Character · '+layer.name)
            if 'family' not in self.dirty:
                name=params.get('fontFamily') or (face['family'] if face else 'Arial')
                if self.family.currentText()!=name: self.family.setCurrentText(name)
                if 'face' not in self.dirty:
                    choices=fonts.styles(name); current=params.get('fontStyle') or (face['style'] if face else 'Regular')
                    if [self.face.itemText(i) for i in range(self.face.count())]!=choices: self.face.clear(); self.face.addItems(choices)
                    if self.face.currentText()!=current: self.face.setCurrentText(current)
            if 'size' not in self.dirty and self.size.value()!=round(params.get('size',48)): self.size.setValue(round(params.get('size',48)))
            self.displayed=dict(params)
            for field in (self.family,self.face,self.size): field.setEnabled(not layer.locked)
            if not self.dirty: self.message.hide()
            elif self.target!=selected: self.feedback('Finish editing '+layer.name+'. Enter applies; Esc cancels.')
        finally: self.syncing=False

    def apply(self,field):
        if self.syncing or field not in self.dirty or not self.target: return
        try:
            document=self.ws.document(self.target[0]); layer=document.layer(self.target[1]); params=dict(layer.params)
            if layer.kind!='text': raise ValueError('This layer no longer contains editable text. Esc discards the unfinished change.')
            if layer.locked: raise ValueError('Unlock this text layer to change its type.')
            current=self.field_value(params,field)
            if current!=self.baselines[field]:
                self.baselines[field]=current
                raise ValueError('This setting changed elsewhere. Press Enter again to apply your choice, or Esc to cancel.')
            if field=='size': params['size']=self.size.value()
            else:
                family=self.family.currentText().strip() if field=='family' else params.get('fontFamily',self.family.currentText())
                style=params.get('fontStyle','Regular') if field=='family' else self.face.currentText()
                face=fonts.resolve(family,style)
                if face is None: raise ValueError('Choose an installed font from the list.')
                params.update(fontFamily=face['family'],fontStyle=face['style'],font=face['path'],fontIndex=face['index'])
            self.dirty.remove(field)
            try:
                if params!=layer.params: self.ws.dispatch('edit',{'documentId':document.id,'expectedRevision':document.revision,'operation':'update_layer','args':{'layerId':layer.id,'params':params}})
            except Exception:
                self.dirty.add(field); raise
            self.refresh()
        except Exception as error: self.feedback(str(error))


class TextPreview(QWidget):
    def __init__(self): super().__init__(); self.image=QPixmap(); self.setMinimumHeight(180)
    def paintEvent(self,event):
        painter=QPainter(self)
        for y in range(0,self.height(),16):
            for x in range(0,self.width(),16): painter.fillRect(x,y,16,16,QColor('#737373' if (x+y)%32 else '#808080'))
        if not self.image.isNull():
            image=self.image.scaled(max(1,self.width()-24),max(1,self.height()-24),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation) if self.image.width()>self.width()-24 or self.image.height()>self.height()-24 else self.image
            painter.drawPixmap((self.width()-image.width())//2,(self.height()-image.height())//2,image)


class TextDialog(QDialog):
    def __init__(self,parent,params=None,creating=False,commit=None):
        super().__init__(parent); self.initial=dict(params or {}); self.color=self.initial.get('color','#000000'); self.result_params=None; self.commit=commit
        self.setWindowTitle('Add text' if creating else 'Edit text'); self.resize(760,650); self.setMinimumSize(600,520)
        layout=QVBoxLayout(self); layout.setContentsMargins(20,18,20,18); layout.setSpacing(12)
        grid=QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(5)
        self.family=QComboBox(); self.family.setEditable(True); self.family.addItems(fonts.families()); self.family.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.family.setAccessibleName('Font family'); self.family.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.face=QComboBox(); self.face.setAccessibleName('Font style')
        self.size=QSpinBox(); self.size.setRange(1,2048); self.size.setSuffix(' px'); self.size.setValue(round(self.initial.get('size',48))); self.size.setAccessibleName('Font size')
        for column,label,widget in ((0,'Font',self.family),(1,'Style',self.face),(2,'Size',self.size)):
            grid.addWidget(QLabel(label),0,column); grid.addWidget(widget,1,column)
        grid.setColumnStretch(0,3); grid.setColumnStretch(1,2); grid.setColumnStretch(2,1); layout.addLayout(grid)
        row=QHBoxLayout(); row.addWidget(QLabel('Alignment')); self.align=QComboBox()
        for label,value in [('Left','left'),('Center','center'),('Right','right')]: self.align.addItem(label,value)
        self.align.setCurrentIndex(max(0,self.align.findData(self.initial.get('align','left')))); self.align.setAccessibleName('Text alignment'); row.addWidget(self.align)
        row.addSpacing(12); row.addWidget(QLabel('Line gap')); self.spacing=QSpinBox(); self.spacing.setRange(0,512); self.spacing.setSuffix(' px'); self.spacing.setValue(round(self.initial.get('spacing',8))); self.spacing.setAccessibleName('Line gap'); row.addWidget(self.spacing)
        row.addSpacing(12); self.color_button=QPushButton(); self.color_button.setMinimumWidth(110); self.color_button.setAccessibleName('Text color'); self.color_button.clicked.connect(self.choose_color); row.addWidget(self.color_button); layout.addLayout(row)
        self.text=QPlainTextEdit(self.initial.get('text','')); self.text.setPlaceholderText('Enter your text'); self.text.setAccessibleName('Text content'); self.text.setMinimumHeight(140); layout.addWidget(self.text,1)
        row=QHBoxLayout(); row.addWidget(QLabel('Preview')); row.addStretch(); self.dimensions=QLabel(); row.addWidget(self.dimensions); layout.addLayout(row)
        self.preview=TextPreview(); layout.addWidget(self.preview,1); self.message=QLabel(); self.message.setWordWrap(True); layout.addWidget(self.message)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        self.apply_button=buttons.button(QDialogButtonBox.StandardButton.Ok); self.apply_button.setText('Add text' if creating else 'Apply changes'); buttons.accepted.connect(self.apply); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(80); self.timer.timeout.connect(self.update_preview)
        self.family.currentTextChanged.connect(self.choose_family)
        for signal in (self.face.currentTextChanged,self.size.valueChanged,self.spacing.valueChanged,self.align.currentIndexChanged,self.text.textChanged): signal.connect(lambda *args:self.timer.start())
        face=fonts.identify(self.initial) or fonts.resolve('Arial')
        if face:
            self.family.setCurrentText(face['family']); self.choose_family(face['family']); self.face.setCurrentText(face['style'])
        if self.initial.get('fontFamily') and fonts.resolve(self.initial['fontFamily']) is None: self.family.setCurrentText(self.initial['fontFamily'])
        self.update_color(); self.update_preview()
        if creating: self.text.setFocus(); self.text.selectAll()

    def choose_family(self,family):
        previous=self.face.currentText(); self.face.blockSignals(True); self.face.clear(); self.face.addItems(fonts.styles(family)); self.face.setCurrentText(previous if previous in fonts.styles(family) else 'Regular'); self.face.blockSignals(False); self.timer.start()

    def values(self):
        face=fonts.resolve(self.family.currentText(),self.face.currentText())
        if face is None: raise ValueError('Choose an installed font from the list.')
        return {**self.initial,'text':self.text.toPlainText(),'font':face['path'],'fontIndex':face['index'],'fontFamily':face['family'],'fontStyle':face['style'],'size':self.size.value(),'spacing':self.spacing.value(),'align':self.align.currentData(),'color':self.color}

    def update_color(self):
        self.color_button.setText(self.color.upper()); ink='#171717' if QColor(self.color).lightness()>150 else '#fff'
        self.color_button.setStyleSheet(f'background:{self.color};color:{ink};border:1px solid #888;')

    def choose_color(self):
        color=QColorDialog.getColor(QColor(self.color),self,'Text color')
        if color.isValid(): self.color=color.name(); self.update_color(); self.update_preview()

    def update_preview(self):
        try:
            params=self.values(); im=pixels.content(Layer(kind='text',params=params)).convert('RGBA')
            self.preview.image=QPixmap.fromImage(QImage(im.tobytes(),im.width,im.height,im.width*4,QImage.Format.Format_RGBA8888).copy()); self.preview.update()
            self.dimensions.setText(f'{im.width} × {im.height} px'); self.message.clear(); self.apply_button.setEnabled(bool(params['text'].strip()))
        except Exception as error: self.message.setText(str(error)); self.apply_button.setEnabled(False)

    def apply(self):
        self.update_preview()
        if self.apply_button.isEnabled():
            self.result_params=self.values()
            try:
                if self.commit: self.commit(self.result_params)
            except Exception as error: self.message.setText(str(error)); return
            self.accept()
