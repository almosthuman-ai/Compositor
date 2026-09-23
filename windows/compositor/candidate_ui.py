"""Review the pixels that will actually be placed in the source document."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QGraphicsView,QGraphicsScene,QGraphicsPixmapItem
from pathlib import Path
from PIL import Image


class CandidateDialog(QDialog):
    def __init__(self,editor,job):
        super().__init__(editor); self.editor=editor; self.job=job
        self.document=editor.ws.document(job['documentId'])
        self.setWindowTitle('Review candidate'); self.resize(1000,760)
        layout=QVBoxLayout(self); controls=QHBoxLayout(); layout.addLayout(controls)
        self.version=QComboBox(); self.version.addItems(['With candidate','Current artwork','Original generation']); controls.addWidget(self.version)
        self.palette=QComboBox(); self.palette.addItem('Document palette','document'); self.palette.addItem('Candidate colors','candidate')
        if self.document.pixel_art: controls.addWidget(self.palette)
        else: self.palette.hide()
        self.zoom=QComboBox()
        for scale in (.25,.5,1,2,3,4,6,8,12,16): self.zoom.addItem(f'{scale*100:g}%',scale)
        self.zoom.setCurrentIndex(4 if self.document.pixel_art else 2); controls.addWidget(self.zoom); controls.addStretch()
        self.scene=QGraphicsScene(); self.view=QGraphicsView(self.scene); self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.item=QGraphicsPixmapItem(); self.item.setTransformationMode(Qt.TransformationMode.FastTransformation if self.document.pixel_art else Qt.TransformationMode.SmoothTransformation); self.scene.addItem(self.item); layout.addWidget(self.view,1)
        self.note=QLabel(); self.note.setWordWrap(True); layout.addWidget(self.note)
        row=QHBoxLayout(); row.addStretch(); layout.addLayout(row)
        close=QPushButton('Close'); close.clicked.connect(self.reject); row.addWidget(close)
        self.apply_button=QPushButton('Apply as layer'); self.apply_button.clicked.connect(self.apply); row.addWidget(self.apply_button)
        self.version.currentIndexChanged.connect(self.refresh); self.palette.currentIndexChanged.connect(self.refresh); self.zoom.currentIndexChanged.connect(self.change_zoom)
        QTimer.singleShot(0,self.refresh)

    def change_zoom(self):
        self.view.resetTransform(); self.view.scale(self.zoom.currentData(),self.zoom.currentData())

    def refresh(self):
        from .ui import pixmap
        try:
            mode=self.version.currentIndex(); self.palette.setEnabled(mode==0)
            if mode==2:
                path=Path(self.job['result']).with_name('provider-original')
                with Image.open(path if path.exists() else self.job['result']) as original: im=original.convert('RGBA')
            else: im=self.document.render() if mode==1 else self.editor.ws.generation.preview(self.document,self.job['id'],self.palette.currentData())
            self.item.setPixmap(pixmap(im)); self.scene.setSceneRect(self.item.boundingRect()); self.change_zoom()
            error=self.editor.ws.generation.application_error(self.document,self.job['id'])
            self.apply_button.setEnabled(error is None and mode==0)
            if mode==2: message=f'{im.width} × {im.height} original provider image. Choose With candidate to review its placement.'
            elif error: message=error
            elif self.document.pixel_art: message=f'{self.document.width} × {self.document.height} pixel canvas with solid pixel edges. The original generated image is retained.'
            else: message=('Preview includes the saved selection mask. ' if self.job.get('selectionBox') else '')+'Application adds an editable layer.'
            actual=self.job.get('actualSize'); working=self.job.get('workingSize')
            if mode==0 and actual and working and actual[0]*working[1]!=actual[1]*working[0]: message+=' The provider returned a different aspect ratio; placement uses a centered crop. Original generation shows the full image.'
            self.note.setText(message)
        except Exception as error: self.note.setText(str(error)); self.apply_button.setEnabled(False)

    def apply(self):
        result=self.editor.run('apply_generation',{'documentId':self.document.id,'jobId':self.job['id'],'paletteMode':self.palette.currentData()})
        if result: self.accept()
