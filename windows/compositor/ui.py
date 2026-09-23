"""Native Windows art editor. Menus, pointer tools and MCP share Workspace commands."""
from pathlib import Path
import html, json, math
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter, QPen, QBrush, QPixmap, QImage, QPainterPath, QIcon, QKeySequence, QDesktopServices
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QSplitter,QTabWidget,QTabBar,QDockWidget,QToolBar,QLabel,QPushButton,QToolButton,QComboBox,QDoubleSpinBox,QSpinBox,QSlider,QLineEdit,QPlainTextEdit,QTextBrowser,QListWidget,QListWidgetItem,QGraphicsView,QGraphicsScene,QGraphicsPixmapItem,QGraphicsPathItem,QFileDialog,QColorDialog,QInputDialog,QMessageBox,QDialog,QDialogButtonBox,QCheckBox,QScrollArea,QAbstractItemView)
from PIL import Image
from . import pixels

STYLE='''
QMainWindow,QDialog { background:#20232a; color:#e7eaf0; }
QWidget { font-family:"Segoe UI"; font-size:13px; color:#e7eaf0; }
QMenuBar,QMenu,QToolBar,QDockWidget,QTabWidget::pane { background:#292d36; }
QMenu::item { padding:8px 24px; min-height:20px; } QMenu::item:selected { background:#465b78; }
QPushButton,QToolButton,QComboBox,QSpinBox,QDoubleSpinBox,QLineEdit { min-height:32px; border:1px solid #48505e; border-radius:4px; padding:0 8px; background:#323844; }
QPushButton:hover,QToolButton:hover { background:#445166; } QToolButton:checked { background:#436284; border-color:#83b7ee; }
QPlainTextEdit,QTextBrowser,QListWidget { background:#222630; border:1px solid #424956; padding:4px; }
QListWidget::item { min-height:34px; padding:3px; } QListWidget::item:selected { background:#405b7a; }
QTabBar::tab { min-height:32px; padding:0 15px; background:#2b303b; } QTabBar::tab:selected { background:#435b77; }
QTabBar::close-button { width:32px; height:32px; }
QDockWidget::title { padding:8px; background:#292d36; } QCheckBox { min-height:32px; }
QScrollBar:vertical { width:16px; } QScrollBar:horizontal { height:16px; }
QStatusBar { background:#252b34; } QSplitter::handle { background:#151a21; width:5px; }
'''

def pixmap(image):
    im=image.convert('RGBA'); return QPixmap.fromImage(QImage(im.tobytes(),im.width,im.height,im.width*4,QImage.Format.Format_RGBA8888).copy())

class Canvas(QGraphicsView):
    def __init__(self,window):
        super().__init__(); self.window=window; self.ws=window.ws; self.setScene(QGraphicsScene(self)); self.art=QGraphicsPixmapItem(); self.scene().addItem(self.art)
        self.overlay=QGraphicsPathItem(); self.overlay.setZValue(2); self.scene().addItem(self.overlay)
        pen=QPen(QColor('#8ac5ff'),1,Qt.PenStyle.DashLine); pen.setCosmetic(True); self.overlay.setPen(pen)
        tile=QPixmap(24,24); tile.fill(QColor('#747780')); p=QPainter(tile); p.fillRect(0,0,12,12,QColor('#999ca4')); p.fillRect(12,12,12,12,QColor('#999ca4')); p.end()
        self.checker=QBrush(tile); self.setBackgroundBrush(QColor('#171b22')); self.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse); self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setMouseTracking(True); self.setAcceptDrops(True); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.points=[]; self.start=None; self.end=None; self.pan=False; self.space=False; self.document_id=None; self.clone_source=None; self.last_stroke=None; self.pressure=1

    def drawBackground(self,painter,rect):
        super().drawBackground(painter,rect)
        if self.ws.active:
            d=self.ws.document(); painter.fillRect(QRectF(0,0,d.width,d.height),self.checker)

    def refresh(self):
        if not self.ws.active: self.art.setPixmap(QPixmap()); return
        d=self.ws.document(); changed=d.id!=self.document_id; self.document_id=d.id
        self.art.setPixmap(pixmap(d.render())); self.scene().setSceneRect(QRectF(-120,-120,d.width+240,d.height+240)); self.selection_overlay()
        if changed: self.fit()

    def fit(self):
        if self.ws.active:
            d=self.ws.document(); self.fitInView(QRectF(-24,-24,d.width+48,d.height+48),Qt.AspectRatioMode.KeepAspectRatio); self.window.zoom_label.setText(f'{self.transform().m11()*100:.0f}%')

    def selection_overlay(self):
        pen=QPen(QColor('#8ac5ff'),1,Qt.PenStyle.DashLine); pen.setCosmetic(True); self.overlay.setPen(pen)
        path=QPainterPath()
        if self.ws.active:
            d=self.ws.document()
            if d.selection is not None:
                import cv2, numpy as np
                contours,_=cv2.findContours(np.array(d.selection),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if len(contour)<2: continue
                    pts=contour[:,0,:]; path.moveTo(float(pts[0][0]),float(pts[0][1]))
                    for x,y in pts[1:]: path.lineTo(float(x),float(y))
                    path.closeSubpath()
            if self.window.tool=='move' and d.active:
                l=d.layer()
                if l.kind not in ('group','adjustment'):
                    im=pixels.content(l); w,h=im.width*abs(l.sx),im.height*abs(l.sy); path.addRect(l.x,l.y,w,h)
                    handle=6/self.transform().m11(); path.addRect(l.x+w-handle,l.y+h-handle,handle*2,handle*2)
                    path.addEllipse(QPointF(l.x+w/2,l.y-25/self.transform().m11()),handle,handle)
            for g in d.guides:
                if g.get('axis')=='x': path.moveTo(g['position'],0); path.lineTo(g['position'],d.height)
                else: path.moveTo(0,g['position']); path.lineTo(d.width,g['position'])
        self.overlay.setPath(path)

    def wheelEvent(self,event):
        factor=1.15 if event.angleDelta().y()>0 else 1/1.15; zoom=self.transform().m11()*factor
        if .01<zoom<64: self.scale(factor,factor); self.window.zoom_label.setText(f'{zoom*100:.0f}%')
        event.accept()

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Space: self.space=True; self.setCursor(Qt.CursorShape.OpenHandCursor); event.accept(); return
        super().keyPressEvent(event)
    def keyReleaseEvent(self,event):
        if event.key()==Qt.Key.Key_Space: self.space=False; self.unsetCursor(); event.accept(); return
        super().keyReleaseEvent(event)

    def mousePressEvent(self,event):
        if not self.ws.active: return
        if event.button()==Qt.MouseButton.MiddleButton or self.space or self.window.tool=='hand':
            self.pan=True; self.pan_point=event.position(); self.setCursor(Qt.CursorShape.ClosedHandCursor); return
        if event.button()!=Qt.MouseButton.LeftButton: return
        point=self.mapToScene(event.position().toPoint()); self.start=point; self.end=point; self.points=[[point.x(),point.y(),self.pressure]]
        self.source_revision=self.ws.document().revision
        self.move_mode='translate'
        tool=self.window.tool
        if tool=='eyedropper':
            d=self.ws.document(); x,y=int(point.x()),int(point.y())
            if 0<=x<d.width and 0<=y<d.height: self.window.color=QColor(*d.render().getpixel((x,y))).name(); self.window.update_color()
            self.start=None
        elif tool=='wand': self.window.edit('selection',{'kind':'wand','x':int(point.x()),'y':int(point.y()),'tolerance':self.window.tolerance.value(),'mode':self.selection_mode(event)}); self.start=None
        elif tool=='text': self.window.add_text(point); self.start=None
        elif tool=='clone' and event.modifiers() & Qt.KeyboardModifier.AltModifier: self.clone_source=point; self.start=None; self.window.statusBar().showMessage('Clone source set. Paint to copy from it.')
        elif tool=='move':
            d=self.ws.document()
            if d.active:
                l=d.layer(); im=pixels.content(l); corner=QPointF(l.x+im.width*abs(l.sx),l.y+im.height*abs(l.sy)); rotation=QPointF(l.x+im.width*abs(l.sx)/2,l.y-25/self.transform().m11())
                if (point-corner).manhattanLength()*self.transform().m11()<18:
                    self.move_mode='scale'; self.move_origin=(l.x,l.y); self.move_scale=(l.sx,l.sy); return
                if (point-rotation).manhattanLength()*self.transform().m11()<18:
                    self.move_mode='rotate'; self.move_origin=(l.x,l.y); self.move_angle=l.angle; return
            # Prefer the active layer when hit; otherwise select the top visible pixel layer.
            candidates=([d.layer()] if d.active else [])+[l for l in reversed(d.layers) if l.id!=d.active]
            for l in candidates:
                if not l.visible or l.locked or l.kind in ('group','adjustment'): continue
                im=pixels.content(l)
                if l.x<=point.x()<l.x+im.width*abs(l.sx) and l.y<=point.y()<l.y+im.height*abs(l.sy):
                    d.active=l.id; self.move_origin=(l.x,l.y); self.ws.changed.emit(); break

    def selection_mode(self,event):
        return 'add' if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 'subtract' if event.modifiers() & Qt.KeyboardModifier.AltModifier else 'replace'

    def mouseMoveEvent(self,event):
        point=self.mapToScene(event.position().toPoint())
        self.window.coords_label.setText(f'{int(point.x())}, {int(point.y())} px')
        if self.pan:
            delta=event.position()-self.pan_point; self.pan_point=event.position(); self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-int(delta.x())); self.verticalScrollBar().setValue(self.verticalScrollBar().value()-int(delta.y())); return
        if self.start is None: return
        self.end=point; tool=self.window.tool; path=QPainterPath()
        if tool in ('brush','erase','clone','heal','blur_brush','lasso'):
            self.points.append([point.x(),point.y(),self.pressure]); path.moveTo(self.start)
            for x,y,*_ in self.points: path.lineTo(x,y)
            if tool!='lasso':
                color=QColor(self.window.color if tool=='brush' else '#8ac5ff'); color.setAlphaF(self.window.brush_opacity.value()/100)
                pen=QPen(color,self.window.brush_size.value(),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin); self.overlay.setPen(pen)
        elif tool=='ellipse': path.addEllipse(QRectF(self.start,point).normalized())
        elif tool=='gradient': path.moveTo(self.start); path.lineTo(point)
        elif tool=='move' and self.ws.document().active:
            l=self.ws.document().layer(); im=pixels.content(l)
            if self.move_mode=='scale': path.addRect(l.x,l.y,max(1,point.x()-l.x),max(1,point.y()-l.y))
            elif self.move_mode=='rotate': path.moveTo(l.x+im.width*abs(l.sx)/2,l.y+im.height*abs(l.sy)/2); path.lineTo(point)
            else: path.addRect(l.x+point.x()-self.start.x(),l.y+point.y()-self.start.y(),im.width*abs(l.sx),im.height*abs(l.sy))
        else: path.addRect(QRectF(self.start,point).normalized())
        self.overlay.setPath(path)

    def mouseReleaseEvent(self,event):
        if self.pan: self.pan=False; self.unsetCursor(); return
        if self.start is None: return
        start=self.start; end=self.mapToScene(event.position().toPoint()); self.start=None; tool=self.window.tool
        rect=QRectF(start,end).normalized(); box={'x':int(rect.x()),'y':int(rect.y()),'width':max(1,int(rect.width())),'height':max(1,int(rect.height()))}
        if tool in ('brush','erase','clone','heal','blur_brush'):
            points=self.points
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and self.last_stroke: points=[self.last_stroke,points[-1]]
            args={'points':points,'size':self.window.brush_size.value(),'opacity':self.window.brush_opacity.value()/100,'hardness':self.window.hardness.value()/100,'color':self.window.color}
            if self.window.mask_target.isChecked(): args['target']='mask'; args['maskValue']=0 if tool=='erase' else 255
            if tool=='clone':
                if self.clone_source is None: self.window.statusBar().showMessage('Alt-click to choose a clone source first.'); self.selection_overlay(); return
                args['offset']=[start.x()-self.clone_source.x(),start.y()-self.clone_source.y()]
            self.window.edit(tool,args,expected=self.source_revision); self.last_stroke=points[-1]
        elif tool in ('rectangle','ellipse','lasso'):
            args={'kind':'polygon' if tool=='lasso' else tool,'mode':self.selection_mode(event),**box}
            if tool=='lasso': args['points']=[p[:2] for p in self.points]
            self.window.edit('selection',args)
        elif tool=='crop': self.window.edit('crop',box)
        elif tool=='move' and hasattr(self,'move_origin'):
            l=self.ws.document().layer(); im=pixels.content(l)
            if self.move_mode=='scale':
                sx=max(.01,(end.x()-l.x)/im.width); sy=max(.01,(end.y()-l.y)/im.height)
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier: sy=abs(self.move_scale[1])*sx/abs(self.move_scale[0])
                args={'sx':math.copysign(sx,l.sx),'sy':math.copysign(sy,l.sy)}
            elif self.move_mode=='rotate':
                cx,cy=l.x+im.width*abs(l.sx)/2,l.y+im.height*abs(l.sy)/2
                args={'angle':self.move_angle+math.degrees(math.atan2(end.y()-cy,end.x()-cx)-math.atan2(start.y()-cy,start.x()-cx))}
            else: args={'x':self.move_origin[0]+end.x()-start.x(),'y':self.move_origin[1]+end.y()-start.y()}
            self.window.edit('update_layer',args,expected=self.source_revision)
        elif tool=='shape': self.window.edit('add_layer',{'kind':'shape','name':self.window.shape_kind.currentText().title(),'x':box['x'],'y':box['y'],'params':{'shape':self.window.shape_kind.currentText(),'width':box['width'],'height':box['height'],'color':self.window.color}})
        elif tool=='gradient':
            d=self.ws.document(); self.window.edit('add_layer',{'kind':'gradient','name':'Gradient','params':{'width':d.width,'height':d.height,'start':[start.x(),start.y()],'end':[end.x(),end.y()],'color':self.window.color,'endColor':self.window.background_color,'radial':self.window.radial.isChecked()}})
        self.selection_overlay()

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dragMoveEvent(self,event): event.acceptProposedAction()
    def dropEvent(self,event):
        for url in event.mimeData().urls():
            if url.isLocalFile(): self.window.run('edit',{'operation':'import_image','args':{'path':url.toLocalFile()}}) if self.ws.active else self.window.run('open',{'path':url.toLocalFile()})
        event.acceptProposedAction()

class Editor(QMainWindow):
    def __init__(self,ws):
        super().__init__(); self.ws=ws; ws.window=self; self.tool='move'; self.color='#efab70'; self.background_color='#ffffff'; self.refreshing=False; self.references=[]
        self.setWindowTitle('Compositor'); self.resize(1500,960); self.setMinimumSize(960,640); self.setStyleSheet(STYLE)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks|QMainWindow.DockOption.AllowNestedDocks)
        self.zoom_label=QLabel('100%'); self.coords_label=QLabel(''); self.statusBar().addPermanentWidget(self.coords_label); self.statusBar().addPermanentWidget(self.zoom_label)
        self.canvas=Canvas(self); self.tabs=QTabBar(); self.tabs.setExpanding(False); self.tabs.setTabsClosable(True); self.tabs.currentChanged.connect(self.activate_tab); self.tabs.tabCloseRequested.connect(self.close_tab)
        central=QWidget(); layout=QVBoxLayout(central); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); layout.addWidget(self.tabs); layout.addWidget(self.canvas); self.setCentralWidget(central)
        self.build_menus(); self.build_tools(); self.build_layers(); self.build_generation(); self.build_chat()
        ws.changed.connect(self.refresh); ws.message.connect(lambda text:self.statusBar().showMessage(text,15000)); self.refresh()

    def action(self,menu,title,callback,shortcut=None):
        a=QAction(title,self)
        def invoke():
            try: callback()
            except Exception as e: self.statusBar().showMessage(str(e),18000)
        a.triggered.connect(invoke)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        menu.addAction(a); return a

    def build_menus(self):
        file=self.menuBar().addMenu('&File'); self.action(file,'New…',self.new_document,'Ctrl+N'); self.action(file,'Open…',self.open_file,'Ctrl+O'); self.action(file,'Add image as layer…',self.import_file,'Ctrl+Shift+O'); self.action(file,'Save',self.save,'Ctrl+S'); self.action(file,'Save as…',lambda:self.save(True),'Ctrl+Shift+S'); self.action(file,'Export image…',self.export,'Ctrl+Alt+Shift+S'); file.addSeparator(); self.action(file,'Settings…',self.settings_dialog); self.action(file,'Exit',self.close,'Alt+F4')
        edit=self.menuBar().addMenu('&Edit'); self.action(edit,'Undo',lambda:self.edit('undo'),'Ctrl+Z'); self.action(edit,'Redo',lambda:self.edit('redo'),'Ctrl+Shift+Z'); edit.addSeparator(); self.action(edit,'Copy selection to layer',lambda:self.edit('copy_selection'),'Ctrl+J'); self.action(edit,'Cut selection to layer',lambda:self.edit('cut_selection'),'Ctrl+Shift+J'); self.action(edit,'Copy merged to clipboard',self.copy_merged,'Ctrl+Shift+C'); self.action(edit,'Paste image',self.paste,'Ctrl+V'); self.action(edit,'Fill with foreground',lambda:self.edit('fill',{'color':self.color}),'Alt+Backspace'); self.action(edit,'Clear pixels',lambda:self.edit('clear'),'Delete'); self.action(edit,'Content-aware fill',lambda:self.edit('content_fill'),'Shift+Backspace')
        image=self.menuBar().addMenu('&Image'); self.action(image,'Image size…',lambda:self.size_dialog('image_size')); self.action(image,'Canvas size…',lambda:self.size_dialog('canvas_size')); self.action(image,'Crop to selection',self.crop_selection)
        layer=self.menuBar().addMenu('&Layer'); self.action(layer,'New transparent layer',lambda:self.edit('add_layer',{'name':'Paint layer'}),'Ctrl+Shift+N'); self.action(layer,'New group',lambda:self.edit('add_layer',{'kind':'group','name':'Group'})); self.action(layer,'Duplicate',lambda:self.edit('duplicate_layer')); self.action(layer,'Rename…',self.rename_layer); self.action(layer,'Delete layer',lambda:self.edit('delete_layer')); self.action(layer,'Rasterize',lambda:self.edit('rasterize')); self.action(layer,'Merge down',lambda:self.edit('merge_down'),'Ctrl+E'); self.action(layer,'Flatten',lambda:self.edit('flatten'),'Ctrl+Shift+E'); self.action(layer,'Flip horizontally',lambda:self.flip('sx')); self.action(layer,'Flip vertically',lambda:self.flip('sy')); self.action(layer,'Layer effects…',self.effects_dialog)
        mask=layer.addMenu('Mask');
        for title,mode in [('From selection','selection'),('Reveal all','white'),('Hide all','black'),('Invert','invert'),('Feather','blur'),('Remove','remove')]: self.action(mask,title,lambda mode=mode:self.edit('mask',{'mode':mode}))
        select=self.menuBar().addMenu('&Select')
        for title,kind,shortcut in [('All','all','Ctrl+A'),('Deselect','none','Ctrl+D'),('Inverse','invert','Ctrl+Shift+I'),('Layer pixels','layer_alpha',None),('Expand','expand',None),('Contract','contract',None),('Feather','feather',None)]: self.action(select,title,lambda kind=kind:self.edit('selection',{'kind':kind}),shortcut)
        adjust=self.menuBar().addMenu('&Adjustments')
        for label,kind in [('Exposure','exposure'),('Brightness','brightness'),('Contrast','contrast'),('Hue / Saturation','hue_saturation'),('Levels','levels'),('Curves','curves'),('Gradient map','gradient_map'),('Invert','invert'),('Grayscale','grayscale'),('Auto levels','auto_levels'),('Grain','grain')]: self.action(adjust,label+'…',lambda kind=kind:self.adjust_dialog(kind,True))
        filters=self.menuBar().addMenu('F&ilters')
        for label,kind in [('Gaussian blur','gaussian_blur'),('Motion blur','motion_blur'),('Sharpen','sharpen'),('Noise','noise')]: self.action(filters,label+'…',lambda kind=kind:self.adjust_dialog(kind,False))
        view=self.menuBar().addMenu('&View'); self.action(view,'Fit canvas',self.canvas.fit,'Ctrl+0'); self.action(view,'Actual pixels',lambda:self.canvas.resetTransform(),'Ctrl+1'); self.action(view,'Add guide…',self.guide_dialog)
        projects=self.menuBar().addMenu('&Projects'); self.action(projects,'Open production studio',self.open_studio); self.action(projects,'Bring project image into editor…',self.pull_project); self.action(projects,'Return artwork to project',self.push_project)
        help_menu=self.menuBar().addMenu('&Help'); self.action(help_menu,'About Compositor',lambda:QMessageBox.information(self,'Compositor','Compositor for Windows\nBased on Robbie Tilton’s MIT-licensed Compositor.\nWindows edition by the Compositor contributors.\n\nSpace-drag to pan; wheel to zoom.\nAlt-click sets a clone source.\nShift adds to selections; Alt subtracts.\n\nSave .compwin for editable layers.'))

    def build_tools(self):
        toolbar=QToolBar('Tools'); toolbar.setMovable(False); toolbar.setOrientation(Qt.Orientation.Vertical); self.addToolBar(Qt.ToolBarArea.LeftToolBarArea,toolbar); self.tool_actions={}; group=QActionGroup(self); group.setExclusive(True)
        for label,key,shortcut in [('Move','move','V'),('Select','rectangle','M'),('Ellipse','ellipse',None),('Lasso','lasso','L'),('Wand','wand','W'),('Crop','crop','C'),('Brush','brush','B'),('Erase','erase','E'),('Heal','heal','J'),('Clone','clone','S'),('Blur','blur_brush',None),('Type','text','T'),('Shape','shape','U'),('Gradient','gradient','G'),('Pick','eyedropper','I'),('Hand','hand','H')]:
            a=QAction(label,self); a.setCheckable(True); a.setToolTip(label+(f' ({shortcut})' if shortcut else '')); a.triggered.connect(lambda checked,key=key:self.set_tool(key)); group.addAction(a); toolbar.addAction(a); self.tool_actions[key]=a
            if shortcut: a.setShortcut(shortcut)
            toolbar.widgetForAction(a).setMinimumSize(64,34)
        self.tool_actions['move'].setChecked(True)
        options=QToolBar('Tool options'); options.setMovable(False); self.addToolBar(options)
        self.color_button=QPushButton('Color'); self.color_button.clicked.connect(self.pick_color); options.addWidget(self.color_button); self.update_color()
        self.brush_size=QSpinBox(); self.brush_size.setRange(1,2048); self.brush_size.setValue(32); self.brush_size.setSuffix(' px'); options.addWidget(QLabel('  Size ')); options.addWidget(self.brush_size)
        self.brush_opacity=QSpinBox(); self.brush_opacity.setRange(1,100); self.brush_opacity.setValue(100); self.brush_opacity.setSuffix('%'); options.addWidget(QLabel('  Opacity ')); options.addWidget(self.brush_opacity)
        self.hardness=QSpinBox(); self.hardness.setRange(0,100); self.hardness.setValue(80); options.addWidget(QLabel('  Hardness ')); options.addWidget(self.hardness)
        self.mask_target=QCheckBox('Paint mask'); options.addWidget(self.mask_target)
        self.tolerance=QSpinBox(); self.tolerance.setRange(0,255); self.tolerance.setValue(32); self.tolerance.setToolTip('Magic wand tolerance'); options.addWidget(self.tolerance)
        self.shape_kind=QComboBox(); self.shape_kind.addItems(['rectangle','ellipse','rounded','line']); options.addWidget(self.shape_kind)
        self.radial=QCheckBox('Radial'); options.addWidget(self.radial)
        self.option_actions=options.actions(); self.update_tool_options()

    def dock(self,title,widget):
        dock=QDockWidget(title,self); dock.setWidget(widget); dock.setMinimumWidth(350); dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock)
        return dock

    def build_layers(self):
        panel=QWidget(); layout=QVBoxLayout(panel); row=QHBoxLayout(); self.blend=QComboBox(); self.blend.addItems(pixels.BLENDS); self.blend.currentTextChanged.connect(lambda v:self.property_changed('blend',v)); row.addWidget(self.blend)
        self.opacity=QSpinBox(); self.opacity.setRange(0,100); self.opacity.setSuffix('%'); self.opacity.valueChanged.connect(lambda v:self.property_changed('opacity',v/100)); row.addWidget(self.opacity); layout.addLayout(row)
        self.layers=QListWidget(); self.layers.setIconSize(QSize(40,32)); self.layers.itemClicked.connect(self.select_layer); self.layers.itemChanged.connect(self.layer_changed); self.layers.itemDoubleClicked.connect(lambda _:self.rename_layer()); layout.addWidget(self.layers)
        buttons=QHBoxLayout()
        for label,fn in [('+',lambda:self.edit('add_layer')),('Copy',lambda:self.edit('duplicate_layer')),('↑',lambda:self.reorder(1)),('↓',lambda:self.reorder(-1)),('−',lambda:self.edit('delete_layer'))]:
            b=QPushButton(label); b.setMinimumWidth(32); b.clicked.connect(fn); buttons.addWidget(b)
        layout.addLayout(buttons)
        form=QFormLayout(); self.transform_fields={}
        for key,label in [('x','X'),('y','Y'),('sx','Scale X'),('sy','Scale Y'),('angle','Rotation')]:
            spin=QDoubleSpinBox(); spin.setRange(-100000,100000); spin.setDecimals(2); spin.setMinimumWidth(100); spin.setMaximumWidth(180); spin.setSingleStep(.1 if key in ('sx','sy') else 1); spin.editingFinished.connect(lambda key=key,spin=spin:self.property_changed(key,spin.value())); self.transform_fields[key]=spin; form.addRow(label,spin)
        layout.addLayout(form); self.locked=QCheckBox('Lock layer'); self.locked.toggled.connect(lambda v:self.property_changed('locked',v)); layout.addWidget(self.locked)
        self.parent_group=QComboBox(); self.parent_group.currentIndexChanged.connect(self.change_group); layout.addWidget(self.parent_group)
        edit_content=QPushButton('Edit layer content…'); edit_content.clicked.connect(self.edit_layer_content); layout.addWidget(edit_content)
        self.clipping=QCheckBox('Clip to layer below'); self.clipping.toggled.connect(lambda v:self.property_changed('clipping',v)); layout.addWidget(self.clipping)
        self.layer_dock=self.dock('Layers',panel)

    def build_generation(self):
        panel=QWidget(); layout=QVBoxLayout(panel); self.prompt=QPlainTextEdit(); self.prompt.setPlaceholderText('Describe an image or the change you want…'); self.prompt.setMaximumHeight(105); layout.addWidget(self.prompt)
        row=QHBoxLayout(); self.gen_kind=QComboBox(); self.gen_kind.addItem('New image','generate'); self.gen_kind.addItem('Edit whole image','edit'); self.gen_kind.addItem('Refine selected area','patch'); row.addWidget(self.gen_kind)
        self.gen_size=QComboBox(); self.gen_size.setEditable(True); self.gen_size.addItems(['1024x1024','1536x1024','1024x1536','2048x1152']); row.addWidget(self.gen_size); layout.addLayout(row)
        row=QHBoxLayout(); ref=QPushButton('References…'); ref.clicked.connect(self.choose_references); row.addWidget(ref); self.ref_label=QLabel('None'); row.addWidget(self.ref_label); layout.addLayout(row)
        self.gen_provider_label=QLabel(); self.gen_provider_label.setWordWrap(True); layout.addWidget(self.gen_provider_label)
        generate=QPushButton('Generate candidate'); generate.clicked.connect(self.generate); layout.addWidget(generate)
        self.jobs=QListWidget(); self.jobs.setIconSize(QSize(56,48)); self.jobs.setMaximumHeight(190); layout.addWidget(self.jobs)
        row=QHBoxLayout()
        for title,fn in [('Inspect',self.inspect_job),('Apply',self.apply_job),('Place as layer',self.import_job)]:
            b=QPushButton(title); b.clicked.connect(fn); row.addWidget(b)
        layout.addLayout(row); self.generation_dock=self.dock('Generate',panel); self.tabifyDockWidget(self.layer_dock,self.generation_dock); self.layer_dock.raise_()

    def build_chat(self):
        panel=QWidget(); layout=QVBoxLayout(panel); top=QHBoxLayout(); self.login_button=QPushButton('Sign in with ChatGPT'); self.login_button.clicked.connect(self.chat_login); top.addWidget(self.login_button)
        logout=QPushButton('Sign out'); logout.clicked.connect(lambda:self.chat.logout() if self.chat else None); top.addWidget(logout); layout.addLayout(top)
        self.chat_status=QLabel('Not connected'); self.chat_status.setWordWrap(True); layout.addWidget(self.chat_status)
        self.chat_model=QComboBox(); self.chat_model.addItem('Account default',None); self.chat_model.currentIndexChanged.connect(self.choose_chat_model); layout.addWidget(self.chat_model)
        self.chat_log=QTextBrowser(); self.chat_log.setOpenExternalLinks(True); layout.addWidget(self.chat_log)
        self.chat_history_limit=100; self.load_chat_history()
        earlier=QPushButton('Load earlier messages'); earlier.clicked.connect(self.earlier_chat); layout.addWidget(earlier)
        self.chat_stream=QPlainTextEdit(); self.chat_stream.setReadOnly(True); self.chat_stream.setMaximumHeight(160); self.chat_stream.hide(); layout.addWidget(self.chat_stream)
        self.chat_input=QPlainTextEdit(); self.chat_input.setPlaceholderText('Talk through your artwork…'); self.chat_input.setMaximumHeight(90); layout.addWidget(self.chat_input)
        row=QHBoxLayout(); send=QPushButton('Send'); send.clicked.connect(self.chat_send); row.addWidget(send); stop=QPushButton('Stop'); stop.clicked.connect(self.chat_stop); row.addWidget(stop); layout.addLayout(row)
        self.chat_dock=self.dock('ChatGPT',panel); self.tabifyDockWidget(self.generation_dock,self.chat_dock); self.layer_dock.raise_(); self.chat=None

    def run(self,action,args=None):
        try:
            result=self.ws.dispatch(action,args)
            if isinstance(result,dict) and result.get('conversionReport'): QMessageBox.information(self,'Import notes','\n'.join(result['conversionReport']))
            return result
        except Exception as e: self.statusBar().showMessage(str(e),18000); QMessageBox.warning(self,'Compositor',str(e)); return None
    def edit(self,operation,args=None,expected=None): return self.run('edit',{'operation':operation,'args':args or {},'expectedRevision':expected})
    def set_tool(self,key): self.tool=key; self.update_tool_options(); self.canvas.selection_overlay(); self.statusBar().showMessage(self.tool_actions[key].toolTip())
    def update_tool_options(self):
        if not hasattr(self,'option_actions'): return
        paint=self.tool in ('brush','erase','heal','clone','blur_brush')
        visible={0:self.tool in ('brush','text','shape','gradient','eyedropper'),1:paint,2:paint,3:paint,4:paint,5:paint,6:paint,7:paint,8:self.tool=='wand',9:self.tool=='shape',10:self.tool=='gradient'}
        for i,action in enumerate(self.option_actions): action.setVisible(visible.get(i,False))
    def update_color(self): self.color_button.setStyleSheet(f'background:{self.color};color:{"black" if QColor(self.color).lightness()>130 else "white"}')
    def pick_color(self):
        color=QColorDialog.getColor(QColor(self.color),self,'Foreground color')
        if color.isValid(): self.color=color.name(); self.update_color()

    def refresh(self):
        self.refreshing=True
        try:
            self.tabs.blockSignals(True)
            while self.tabs.count(): self.tabs.removeTab(0)
            for d in self.ws.documents.values():
                i=self.tabs.addTab(d.title+(' •' if d.revision!=d.saved_revision else '')); self.tabs.setTabData(i,d.id)
                if d.id==self.ws.active: self.tabs.setCurrentIndex(i)
            self.tabs.blockSignals(False); self.layers.clear()
            if self.ws.active:
                d=self.ws.document(); self.setWindowTitle(d.title+' — Compositor')
                for l in reversed(d.layers):
                    item=QListWidgetItem(('    ' if l.parent else '')+l.name+('  ◐' if l.mask else '')); item.setData(Qt.ItemDataRole.UserRole,l.id); item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked if l.visible else Qt.CheckState.Unchecked)
                    if l.kind not in ('group','adjustment'):
                        im=pixels.content(l).copy(); im.thumbnail((40,32)); item.setIcon(QIcon(pixmap(im)))
                    self.layers.addItem(item)
                    if l.id==d.active: self.layers.setCurrentItem(item)
                if d.active:
                    l=d.layer(); self.blend.setCurrentText(l.blend); self.opacity.setValue(round(l.opacity*100)); self.locked.setChecked(l.locked); self.clipping.setChecked(l.clipping)
                    for k,spin in self.transform_fields.items(): spin.setValue(getattr(l,k))
                    self.parent_group.clear(); self.parent_group.addItem('Outside groups',None)
                    for group in d.layers:
                        if group.kind=='group' and group.id!=l.id: self.parent_group.addItem(group.name,group.id)
                    self.parent_group.setCurrentIndex(max(0,self.parent_group.findData(l.parent)))
            selected=self.jobs.currentItem().data(Qt.ItemDataRole.UserRole) if self.jobs.currentItem() else None; self.jobs.clear()
            for job in sorted(self.ws.generation.jobs.values(),key=lambda j:j['created'],reverse=True):
                if job.get('documentId')!=self.ws.active: continue
                text=('Applied' if job.get('applied') else job['status'].title())+' · '+job['prompt'][:48]; item=QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole,job['id']); item.setToolTip(job.get('error') or job.get('applyError') or job['prompt'])
                if job.get('result'):
                    im=Image.open(job['result']); im.thumbnail((56,48)); item.setIcon(QIcon(pixmap(im)))
                self.jobs.addItem(item)
                if job['id']==selected: self.jobs.setCurrentItem(item)
            if not self.jobs.currentItem() and self.jobs.count(): self.jobs.setCurrentRow(0)
            self.gen_provider_label.setText(f"API provider: {self.ws.settings.values['provider']} · {self.ws.settings.values['model']}")
            self.canvas.refresh()
        finally: self.refreshing=False

    def activate_tab(self,index):
        if not self.refreshing and index>=0: self.run('activate',{'documentId':self.tabs.tabData(index)})
    def close_tab(self,index):
        d=self.ws.document(self.tabs.tabData(index))
        if d.revision!=d.saved_revision:
            answer=QMessageBox.question(self,'Close document','Save changes to '+d.title+'?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
            if answer==QMessageBox.StandardButton.Cancel: return
            if answer==QMessageBox.StandardButton.Save:
                self.run('activate',{'documentId':d.id})
                if not self.save(): return
        self.run('close',{'documentId':d.id,'discard':True})
    def property_changed(self,key,value):
        if not self.refreshing and self.ws.active and self.ws.document().active:
            if getattr(self.ws.document().layer(),key)!=value: self.edit('update_layer',{key:value})
    def select_layer(self,item):
        if not self.refreshing: self.ws.document().active=item.data(Qt.ItemDataRole.UserRole); self.ws.changed.emit()
    def layer_changed(self,item):
        if not self.refreshing: self.edit('update_layer',{'layerId':item.data(Qt.ItemDataRole.UserRole),'visible':item.checkState()==Qt.CheckState.Checked})
    def reorder(self,direction):
        d=self.ws.document(); self.edit('reorder_layer',{'index':d.layers.index(d.layer())+direction})
    def rename_layer(self):
        d=self.ws.document(); text,ok=QInputDialog.getText(self,'Rename layer','Name',text=d.layer().name)
        if ok: self.edit('update_layer',{'name':text})
    def flip(self,key): self.edit('update_layer',{key:-getattr(self.ws.document().layer(),key)})
    def change_group(self,index):
        if not self.refreshing and self.ws.active and self.ws.document().active: self.property_changed('parent',self.parent_group.itemData(index))
    def edit_layer_content(self):
        if not self.ws.active or not self.ws.document().active: return
        layer=self.ws.document().layer()
        if layer.kind not in ('text','shape','gradient','adjustment'): self.rename_layer(); return
        params={k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in layer.params.items()}
        result=self.form_dialog('Edit '+layer.kind,params)
        if result is not None:
            try:
                for k,v in layer.params.items():
                    if isinstance(v,(list,dict)): result[k]=json.loads(result[k])
                self.edit('update_layer',{'params':result})
            except ValueError as e: QMessageBox.warning(self,'Layer',str(e))

    def form_dialog(self,title,fields):
        dialog=QDialog(self); dialog.setWindowTitle(title); layout=QFormLayout(dialog); controls={}
        for key,value in fields.items():
            if isinstance(value,bool): control=QCheckBox(); control.setChecked(value)
            elif isinstance(value,(int,float)):
                control=QDoubleSpinBox(); control.setRange(-100000,100000); control.setDecimals(3); control.setValue(value)
            elif key=='text': control=QPlainTextEdit(str(value)); control.setMinimumSize(320,120)
            else: control=QLineEdit(str(value))
            layout.addRow(key.replace('_',' ').title(),control); controls[key]=control
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); layout.addRow(buttons)
        if dialog.exec()!=QDialog.DialogCode.Accepted: return None
        return {k:c.isChecked() if isinstance(c,QCheckBox) else c.value() if isinstance(c,QDoubleSpinBox) else c.toPlainText() if isinstance(c,QPlainTextEdit) else c.text() for k,c in controls.items()}

    def new_document(self):
        a=self.form_dialog('New document',{'title':'Untitled','width':1536,'height':1024,'background':'#ffffff'})
        if a: self.run('new',a)
    def open_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Open image or document','','Images and documents (*.compwin *.ora *.psd *.png *.jpg *.jpeg *.webp *.tif *.tiff *.heic *.bmp);;All files (*)')
        if path: self.run('open',{'path':path})
    def import_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Add image as layer','','Images (*.png *.jpg *.jpeg *.webp *.tif *.tiff *.heic *.bmp)')
        if path: self.edit('import_image',{'path':path})
    def save(self,as_copy=False):
        if not self.ws.active: return None
        d=self.ws.document(); path=d.path
        if as_copy or not path: path,_=QFileDialog.getSaveFileName(self,'Save layered document',d.title+'.compwin','Compositor document (*.compwin);;OpenRaster (*.ora)')
        return self.run('save',{'path':path}) if path else None
    def export(self):
        if not self.ws.active: return
        path,_=QFileDialog.getSaveFileName(self,'Export image',self.ws.document().title+'.png','PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;TIFF (*.tif)')
        if path: self.run('export',{'path':path})
    def size_dialog(self,operation):
        d=self.ws.document(); a=self.form_dialog(operation.replace('_',' ').title(),{'width':d.width,'height':d.height})
        if a: self.edit(operation,a)
    def crop_selection(self):
        box=self.ws.document().selection.getbbox() if self.ws.document().selection is not None else None
        if box: self.edit('crop',{'x':box[0],'y':box[1],'width':box[2]-box[0],'height':box[3]-box[1]})
    def add_text(self,point):
        a=self.form_dialog('Text',{'text':'Your text','size':48,'font':'C:/Windows/Fonts/arial.ttf','color':self.color,'spacing':8})
        if a: self.edit('add_layer',{'kind':'text','name':a['text'][:36],'x':point.x(),'y':point.y(),'params':a})
    def adjust_dialog(self,kind,layer):
        fields={'exposure':{'value':0},'brightness':{'value':0},'contrast':{'value':1},'hue_saturation':{'hue':0,'saturation':1,'value':1},'levels':{'black':0,'white':1,'gamma':1},'curves':{'points':'[[0,0],[0.5,0.5],[1,1]]'},'gradient_map':{'color':'#1c3154','endColor':'#ffdda1'},'grain':{'amount':.05},'noise':{'amount':.05},'gaussian_blur':{'radius':3},'motion_blur':{'radius':15,'angle':0},'sharpen':{'radius':2,'percent':150}}.get(kind,{})
        a=self.form_dialog(kind.replace('_',' ').title(),fields) if fields else {}
        if a is None: return
        if 'points' in a:
            try: a['points']=json.loads(a['points'])
            except ValueError: QMessageBox.warning(self,'Curves','Use pairs such as [[0,0],[0.5,0.7],[1,1]].'); return
        a['kind']=kind
        if layer:
            result=self.edit('add_layer',{'kind':'adjustment','name':kind.replace('_',' ').title(),'params':a})
            if result and self.ws.document().selection is not None: self.edit('mask',{'mode':'selection'})
        else: self.edit('filter',a)
    def effects_dialog(self):
        a=self.form_dialog('Layer effects',{'shadow':True,'shadow_blur':12,'shadow_x':8,'shadow_y':8,'stroke':False,'stroke_width':3,'stroke_color':'#ffffff','glow':False,'glow_radius':12})
        if a:
            effects={}
            if a['shadow']: effects['shadow']={'blur':a['shadow_blur'],'x':a['shadow_x'],'y':a['shadow_y']}
            if a['stroke']: effects['stroke']={'width':a['stroke_width'],'color':a['stroke_color']}
            if a['glow']: effects['glow']={'radius':a['glow_radius']}
            self.edit('update_layer',{'effects':effects})
    def guide_dialog(self):
        a=self.form_dialog('Add guide',{'axis':'x','position':100})
        if a: self.edit('guides',{'guides':self.ws.document().guides+[a]})
    def copy_merged(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setPixmap(pixmap(self.ws.document().render()))
    def paste(self):
        from PySide6.QtWidgets import QApplication
        import uuid
        im=QApplication.clipboard().image()
        if not im.isNull():
            folder=self.ws.settings.root/'clipboard'; folder.mkdir(exist_ok=True); path=folder/(str(uuid.uuid4())+'.png'); im.save(str(path)); self.edit('import_image',{'path':str(path)})
    def choose_references(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Reference images','','Images (*.png *.jpg *.jpeg *.webp)'); self.references=paths; self.ref_label.setText(f'{len(paths)} selected')
    def generate(self): self.run('generate',{'prompt':self.prompt.toPlainText(),'kind':self.gen_kind.currentData(),'size':self.gen_size.currentText(),'references':self.references})
    def selected_job(self): return self.ws.generation.jobs.get(self.jobs.currentItem().data(Qt.ItemDataRole.UserRole)) if self.jobs.currentItem() else None
    def inspect_job(self):
        job=self.selected_job()
        if job and job.get('result'): QDesktopServices.openUrl(QUrl.fromLocalFile(job['result']))
    def apply_job(self):
        job=self.selected_job()
        if job: self.run('apply_generation',{'jobId':job['id']})
    def import_job(self):
        job=self.selected_job()
        if job and job.get('result'): self.edit('import_image',{'path':job['result'],'provenance':{'generationId':job['id']}})

    def settings_dialog(self):
        s=self.ws.settings; dialog=QDialog(self); dialog.setWindowTitle('Settings'); form=QFormLayout(dialog)
        provider=QComboBox(); provider.addItems(['openai','gemini']); provider.setCurrentText(s.values['provider']); form.addRow('Image provider',provider)
        model=QLineEdit(s.values['model']); form.addRow('Image model',model)
        key=QLineEdit(); key.setEchoMode(QLineEdit.EchoMode.Password); key.setPlaceholderText('Leave blank to keep the saved key'); form.addRow('API key',key)
        endpoint=QLineEdit(s.values['openai_url']); form.addRow('OpenAI-compatible URL',endpoint)
        studio=QLineEdit(s.values.get('studio_url','')); studio.setPlaceholderText('Optional local production service'); form.addRow('Project connector URL',studio)
        note=QLabel('API keys are stored in Windows Credential Manager.\nChatGPT sign-in is separate and uses your subscription.'); note.setWordWrap(True); form.addRow(note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            try:
                if key.text(): s.set_key(provider.currentText(),key.text())
                self.run('settings',{'provider':provider.currentText(),'model':model.text(),'openai_url':endpoint.text(),'studio_url':studio.text()})
            except Exception as e: QMessageBox.warning(self,'Settings',str(e))
    def open_studio(self):
        url=self.ws.settings.values.get('studio_url')
        if not url: self.settings_dialog(); return
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            if not hasattr(self,'studio_window'):
                self.studio_window=QMainWindow(self); self.studio_window.setWindowTitle('Production studio — Compositor'); self.studio_window.resize(1380,900); browser=QWebEngineView(); browser.setUrl(QUrl(url)); self.studio_window.setCentralWidget(browser)
            self.studio_window.show(); self.studio_window.raise_()
        except Exception as e: QMessageBox.warning(self,'Production studio',str(e))
    def pull_project(self):
        projects=self.run('connector_projects')
        if not projects: return
        options=[p['title']+'  ·  '+p['id'] for p in projects]; choice,ok=QInputDialog.getItem(self,'Project image','Project',options,0,False)
        if ok:
            a=self.form_dialog('Project image',{'role':'background','page':1})
            if a: self.run('connector_pull',{'projectId':projects[options.index(choice)]['id'],**a})
    def push_project(self):
        d=self.ws.document()
        if not d.studio: QMessageBox.information(self,'Return to project','Bring an image from a project first, or use the project tools to choose a destination.'); return
        self.run('connector_push',{'projectId':d.studio['lessonId'],'role':d.studio.get('role','background'),'page':d.studio.get('page',1)})

    def ensure_chat(self):
        if self.chat is not None and self.chat.proc.state()==self.chat.proc.ProcessState.NotRunning:
            self.chat.shutdown(); self.chat.deleteLater(); self.chat=None
        if self.chat is None:
            from .chat import ChatSession
            self.chat=ChatSession(self.ws,self); self.chat.display.connect(self.chat_log.append); self.chat.status.connect(self.chat_status.setText); self.chat.stream.connect(self.show_chat_stream)
            self.chat.models_changed.connect(self.populate_chat_models)
        return self.chat
    def populate_chat_models(self):
        self.chat_model.blockSignals(True); self.chat_model.clear()
        for model in self.chat.model_options:
            value=model.get('model') or model.get('id'); self.chat_model.addItem(model.get('displayName') or value,value)
        self.chat_model.setCurrentIndex(max(0,self.chat_model.findData(self.chat.model))); self.chat_model.blockSignals(False)
    def choose_chat_model(self,index):
        if getattr(self,'chat',None): self.chat.model=self.chat_model.itemData(index)
    def load_chat_history(self):
        from collections import deque
        path=self.ws.settings.root/'chat/conversation.jsonl'
        if not path.exists(): return
        with path.open(encoding='utf-8') as source: lines=deque(source,maxlen=self.chat_history_limit)
        self.chat_log.clear()
        for line in lines:
            try: row=json.loads(line)
            except ValueError: continue
            label='You' if row['role']=='user' else 'ChatGPT'
            self.chat_log.append('<b>'+label+'</b><br>'+html.escape(row['text']).replace('\n','<br>'))
    def earlier_chat(self):
        self.chat_history_limit+=100; self.load_chat_history()
    def show_chat_stream(self,text):
        self.chat_stream.setVisible(bool(text)); self.chat_stream.setPlainText(text); self.chat_stream.verticalScrollBar().setValue(self.chat_stream.verticalScrollBar().maximum())
    def chat_login(self):
        try:
            from .chat import runtime_command
            runtime_command(self.ws.settings.values.get('codex_path'))
            self.ensure_chat().login()
        except RuntimeError:
            self.install_chat_runtime()
        except Exception as e: self.chat_status.setText(str(e))
    def install_chat_runtime(self):
        from PySide6.QtCore import QThread, Signal
        from .codex_runtime import install_runtime
        if hasattr(self,'runtime_install') and self.runtime_install.isRunning(): return
        class Installer(QThread):
            progress=Signal(str); completed=Signal(str); failed=Signal(str)
            def run(worker):
                try: worker.completed.emit(install_runtime(self.ws.settings.root,worker.progress.emit))
                except Exception as e: worker.failed.emit(str(e))
        self.runtime_install=Installer(self); self.runtime_install.progress.connect(self.chat_status.setText); self.runtime_install.failed.connect(self.chat_status.setText)
        def installed(path):
            self.ws.settings.values['codex_path']=path; self.ws.settings.save(); self.chat_login()
        self.runtime_install.completed.connect(installed); self.runtime_install.start()
    def chat_send(self):
        text=self.chat_input.toPlainText().strip()
        if not text: return
        try: self.ensure_chat().send_message(text); self.chat_log.append('<b>You</b><br>'+html.escape(text).replace('\n','<br>')); self.chat_input.clear()
        except Exception as e: self.chat_status.setText(str(e))
    def chat_stop(self):
        if self.chat: self.chat.interrupt()
    def closeEvent(self,event):
        if hasattr(self,'runtime_install') and self.runtime_install.isRunning():
            QMessageBox.information(self,'ChatGPT setup','ChatGPT support is still installing. Keep Compositor open until setup finishes.'); event.ignore(); return
        active=[j for j in self.ws.generation.jobs.values() if j['status'] in ('queued','running')]
        if active:
            QMessageBox.information(self,'Images are still generating','Generation is still running. Minimize Compositor to keep these requests alive, or wait for them to finish.'); event.ignore(); return
        self.ws.save_recovery()
        if self.chat: self.chat.shutdown()
        event.accept()
