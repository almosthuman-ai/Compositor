"""Pixel conversion is a previewable choice, followed by editable pixel work."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog,QHBoxLayout,QVBoxLayout,QFormLayout,QLabel,QSpinBox,QCheckBox,QComboBox,QLineEdit,QDialogButtonBox,QGraphicsView,QGraphicsScene,QGraphicsPixmapItem
from .pixel_art import convert, source


class PixelArtDialog(QDialog):
    def __init__(self,editor):
        super().__init__(editor); self.editor=editor; self.document=editor.ws.document(); self.revision=self.document.revision
        self.setWindowTitle('Convert to pixel art'); self.resize(1000,700)
        outer=QHBoxLayout(self); controls=QVBoxLayout(); outer.addLayout(controls); form=QFormLayout(); controls.addLayout(form)
        self.width_input=QSpinBox(); self.height_input=QSpinBox()
        for field in (self.width_input,self.height_input): field.setRange(1,2048); field.setSuffix(' px')
        self.width_input.setValue(min(256,self.document.width)); self.height_input.setValue(max(1,round(self.width_input.value()*self.document.height/self.document.width)))
        form.addRow('Width',self.width_input); form.addRow('Height',self.height_input)
        self.aspect=QCheckBox('Keep proportions'); self.aspect.setChecked(True); form.addRow(self.aspect)
        self.colors=QSpinBox(); self.colors.setRange(2,256); self.colors.setValue(32); form.addRow('Colors',self.colors)
        self.sampling=QComboBox(); self.sampling.addItem('Nearest neighbor','nearest'); self.sampling.addItem('Area average','area'); form.addRow('Reduction',self.sampling)
        self.simplify=QComboBox()
        for name,value in [('None',0),('Light',1),('Medium',2),('Strong',3)]: self.simplify.addItem(name,value)
        form.addRow('Simplify detail',self.simplify)
        self.dither=QCheckBox('Dither'); form.addRow(self.dither)
        self.alpha=QSpinBox(); self.alpha.setRange(1,255); self.alpha.setValue(128); form.addRow('Alpha threshold',self.alpha)
        self.selection=QCheckBox('Use selected area'); self.selection.setEnabled(self.document.selection is not None); form.addRow(self.selection)
        self.palette=QLineEdit(); self.palette.setPlaceholderText('Optional: #18243a, #f5d690, …'); form.addRow('Custom palette',self.palette)
        note=QLabel('Creates a separate document with actual pixels and a limited palette. Refine its shapes and pixel clusters with the pencil.'); note.setWordWrap(True); note.setMaximumWidth(270); controls.addWidget(note)
        self.summary=QLabel(); self.summary.setWordWrap(True); self.summary.setMaximumWidth(270); controls.addWidget(self.summary); controls.addStretch()
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Create pixel document'); buttons.accepted.connect(self.commit); buttons.rejected.connect(self.reject); controls.addWidget(buttons)
        self.scene=QGraphicsScene(); self.view=QGraphicsView(self.scene); self.item=QGraphicsPixmapItem(); self.item.setTransformationMode(Qt.TransformationMode.FastTransformation); self.scene.addItem(self.item); outer.addWidget(self.view,1)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(150); self.timer.timeout.connect(self.preview)
        self.width_input.valueChanged.connect(lambda:self.dimension_changed('width')); self.height_input.valueChanged.connect(lambda:self.dimension_changed('height'))
        for field in (self.colors,self.alpha): field.valueChanged.connect(self.schedule)
        for field in (self.sampling,self.simplify): field.currentIndexChanged.connect(self.schedule)
        self.dither.toggled.connect(self.schedule); self.selection.toggled.connect(lambda:self.dimension_changed('width')); self.palette.textChanged.connect(self.schedule)
        QTimer.singleShot(0,self.preview)

    def arguments(self):
        args={'documentId':self.document.id,'expectedRevision':self.revision,'width':self.width_input.value(),'height':self.height_input.value(),'colors':self.colors.value(),'sampling':self.sampling.currentData(),'simplify':self.simplify.currentData(),'dither':self.dither.isChecked(),'alphaThreshold':self.alpha.value(),'useSelection':self.selection.isChecked()}
        if self.palette.text().strip(): args['palette']=[c.strip() for c in self.palette.text().split(',') if c.strip()]
        return args

    def dimension_changed(self,changed):
        if self.aspect.isChecked():
            image=source(self.document,{'useSelection':self.selection.isChecked()}); ratio=image.width/image.height
            field=self.height_input if changed=='width' else self.width_input; value=round(self.width_input.value()/ratio) if changed=='width' else round(self.height_input.value()*ratio)
            field.blockSignals(True); field.setValue(max(1,value)); field.blockSignals(False)
        self.schedule()

    def schedule(self,*_): self.timer.start()

    def preview(self):
        from .ui import pixmap
        try:
            args=self.arguments(); image,metadata=convert(source(self.document,args),args); self.item.setPixmap(pixmap(image)); self.scene.setSceneRect(0,0,image.width,image.height)
            zoom=max(1,min((self.view.viewport().width()-20)//image.width,(self.view.viewport().height()-20)//image.height)); self.view.resetTransform(); self.view.scale(zoom,zoom)
            self.summary.setText(f"{image.width} × {image.height} actual pixels · {len(metadata['palette'])} colors\nPreview {zoom}× · hard transparency edges")
        except Exception as error: self.summary.setText(str(error))

    def commit(self):
        try:
            self.editor.ws.dispatch('pixel_art',self.arguments()); self.editor.set_tool('pencil'); self.accept()
        except Exception as error: self.summary.setText(str(error))
