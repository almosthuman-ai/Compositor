"""Native Windows art editor. Menus, pointer tools and MCP share Workspace commands."""
from pathlib import Path
import html, json, math
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QTimer, QUrl, QEvent
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter, QPen, QBrush, QPixmap, QImage, QPainterPath, QIcon, QKeySequence, QDesktopServices, QMouseEvent
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QSplitter,QTabWidget,QTabBar,QDockWidget,QToolBar,QLabel,QPushButton,QToolButton,QComboBox,QDoubleSpinBox,QSpinBox,QSlider,QLineEdit,QPlainTextEdit,QTextBrowser,QListWidget,QListWidgetItem,QGraphicsView,QGraphicsScene,QGraphicsPixmapItem,QGraphicsPathItem,QFileDialog,QColorDialog,QInputDialog,QMessageBox,QDialog,QDialogButtonBox,QCheckBox,QScrollArea,QAbstractItemView)
from PIL import Image
from . import pixels
from .chrome import icon, icon_button, Ruler, ColorPanel, LayerDelegate, configure_application
from .chrome import EditorComboBox as QComboBox
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QFrame
from .gesture import EditPreview

STYLE='''
QMainWindow,QDialog { background:#303030; color:#dedede; }
QWidget { font-family:"Segoe UI"; font-size:12px; color:#dedede; }
QToolTip { background:#eee; color:#222; border:1px solid #888; padding:5px; }
QMenuBar { background:#393939; border-bottom:1px solid #252525; }
QMenuBar::item { padding:8px 9px; }
QMenuBar::item:selected,QMenu::item:selected { background:#585858; }
QMenu { background:#393939; border:1px solid #222; }
QMenu::item { padding:0 28px; min-height:32px; }
QMenu::separator { height:1px; background:#252525; margin:4px 8px; }
QToolBar { background:#454545; border:0; border-bottom:1px solid #282828; spacing:4px; padding:3px; }
QToolBar#toolRail { background:#3c3c3c; border-right:1px solid #282828; padding:3px; spacing:1px; }
QToolBar::separator { background:#2c2c2c; width:1px; height:1px; margin:4px; }
QPushButton,QComboBox,QSpinBox,QDoubleSpinBox,QLineEdit { min-height:30px; border:1px solid #2d2d2d; border-radius:2px; padding:0 7px; background:#3b3b3b; }
QPushButton:hover,QComboBox:hover { background:#515151; border-color:#747474; }
QPushButton:pressed { background:#292929; }
QToolButton { min-width:30px; min-height:30px; padding:0; border:1px solid transparent; border-radius:2px; background:transparent; }
QToolButton:hover { background:#565656; border-color:#626262; }
QToolButton:checked { background:#242424; border-color:#727272; }
QToolButton:disabled,QPushButton:disabled { color:#888; }
QLineEdit:focus,QPlainTextEdit:focus { border-color:#8b8b8b; }
QComboBox::drop-down { width:24px; border:0; }
QComboBox QAbstractItemView { background:#393939; selection-background-color:#656565; min-height:32px; }
QSpinBox::up-button,QDoubleSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::down-button { width:0; }
QPlainTextEdit,QTextBrowser { background:#353535; border:1px solid #282828; padding:7px; selection-background-color:#53697e; }
QListWidget { background:#414141; border:0; outline:0; padding:0; }
QListWidget::item { min-height:34px; padding:3px; border-bottom:1px solid #3b3b3b; }
QListWidget::item:selected { background:#626262; }
QTabWidget::pane { background:#454545; border:0; }
QTabBar { background:#333; }
QTabBar::tab { min-height:32px; padding:0 12px; background:#383838; border-right:1px solid #292929; }
QTabBar::tab:selected { background:#4a4a4a; color:white; }
QTabBar::tab:hover { background:#515151; }
QTabBar::close-button { width:32px; height:32px; }
QDockWidget { background:#454545; }
QDockWidget::title { background:#383838; padding:8px 10px; }
QCheckBox { min-height:32px; spacing:6px; }
QCheckBox::indicator { width:16px; height:16px; }
QCheckBox::indicator:unchecked { background:#353535; border:1px solid #767676; border-radius:2px; }
QScrollBar:vertical { background:#303030; width:12px; margin:0; }
QScrollBar:horizontal { background:#303030; height:12px; margin:0; }
QScrollBar::handle { background:#5b5b5b; min-width:32px; min-height:32px; border:2px solid #303030; }
QScrollBar::add-line,QScrollBar::sub-line { width:0; height:0; }
QScrollBar::add-page,QScrollBar::sub-page { background:transparent; }
QStatusBar { background:#393939; border-top:1px solid #292929; min-height:24px; }
QStatusBar::item { border:0; } QStatusBar QLabel { color:#bdbdbd; padding:0 8px; }
QSplitter::handle { background:#292929; width:4px; height:4px; }
QWidget#inspector { background:#454545; }
QLabel#sectionLabel { color:#c7c7c7; font-weight:600; padding:4px 0; }
'''

def pixmap(image):
    im=image.convert('RGBA'); return QPixmap.fromImage(QImage(im.tobytes(),im.width,im.height,im.width*4,QImage.Format.Format_RGBA8888).copy())

class ArtworkItem(QGraphicsPixmapItem):
    def __init__(self): super().__init__(); self.preview_canvas=None
    def paint(self,painter,option,widget=None):
        if self.preview_canvas is not None: painter.drawPixmap(0,0,self.preview_canvas)
        else: super().paint(painter,option,widget)

class Canvas(QGraphicsView):
    def __init__(self,window):
        super().__init__(); self.window=window; self.ws=window.ws; self.setScene(QGraphicsScene(self)); self.art=ArtworkItem(); self.scene().addItem(self.art)
        self.preview_box=None; self.art.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.gesture=None; self.preview_timer=QTimer(self); self.preview_timer.setSingleShot(True); self.preview_timer.setInterval(24); self.preview_timer.timeout.connect(self.render_preview)
        self.overlay=QGraphicsPathItem(); self.overlay.setZValue(2); self.scene().addItem(self.overlay)
        pen=QPen(QColor('#8ac5ff'),1,Qt.PenStyle.DashLine); pen.setCosmetic(True); self.overlay.setPen(pen)
        tile=QPixmap(24,24); tile.fill(QColor('#747780')); p=QPainter(tile); p.fillRect(0,0,12,12,QColor('#999ca4')); p.fillRect(12,12,12,12,QColor('#999ca4')); p.end()
        self.checker=QBrush(tile); self.setBackgroundBrush(QColor('#262626')); self.setFrameShape(QFrame.Shape.NoFrame); self.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse); self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setMouseTracking(True); self.setAcceptDrops(True); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.points=[]; self.start=None; self.end=None; self.pan=False; self.space=False; self.document_id=None; self.clone_source=None; self.last_stroke=None; self.pressure=1
        self.horizontalScrollBar().valueChanged.connect(self.update_view_chrome); self.verticalScrollBar().valueChanged.connect(self.update_view_chrome)

    def update_view_chrome(self):
        for ruler in getattr(self.window,'rulers',[]): ruler.update()
        if hasattr(self.window,'zoom_label'): self.window.zoom_label.setText(f'{self.transform().m11()*100:.0f}%')

    def viewportEvent(self,event):
        routes={QEvent.Type.TabletPress:(QEvent.Type.MouseButtonPress,self.mousePressEvent),QEvent.Type.TabletMove:(QEvent.Type.MouseMove,self.mouseMoveEvent),QEvent.Type.TabletRelease:(QEvent.Type.MouseButtonRelease,self.mouseReleaseEvent)}
        if event.type() in routes:
            kind,handler=routes[event.type()]
            if event.type()!=QEvent.Type.TabletRelease: self.pressure=max(0,min(1,event.pressure()))
            mouse=QMouseEvent(kind,event.position(),event.globalPosition(),event.button(),event.buttons(),event.modifiers())
            handler(mouse)
            if event.type()==QEvent.Type.TabletRelease: self.pressure=1
            event.accept(); return True
        return super().viewportEvent(event)

    def resizeEvent(self,event):
        super().resizeEvent(event); self.update_view_chrome()

    def resetTransform(self):
        super().resetTransform(); self.update_view_chrome(); self.selection_overlay()

    def drawBackground(self,painter,rect):
        super().drawBackground(painter,rect)
        if self.ws.active:
            d=self.ws.document(); painter.fillRect(QRectF(0,0,d.width,d.height),self.checker)

    def refresh(self):
        if self.gesture and (self.ws.active!=self.gesture.document_id or self.ws.document().revision!=self.gesture.revision or self.ws.document().active!=self.gesture.layer_id):
            self.cancel_gesture('The document changed; the unfinished stroke was cancelled.')
        if not self.ws.active: self.art.setPixmap(QPixmap()); return
        d=self.ws.document(); changed=d.id!=self.document_id; self.document_id=d.id
        if changed: self.last_stroke=None
        self.art.setPixmap(pixmap(d.render())); self.scene().setSceneRect(QRectF(-120,-120,d.width+240,d.height+240)); self.selection_overlay()
        if changed: self.fit()

    def fit(self):
        if self.ws.active:
            d=self.ws.document(); self.fitInView(QRectF(-64,-64,d.width+128,d.height+128),Qt.AspectRatioMode.KeepAspectRatio); self.update_view_chrome(); self.selection_overlay()

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
            if self.window.tool=='move' and d.active and getattr(self.window,'show_transform',None) and self.window.show_transform.isChecked():
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
        if .01<zoom<64: self.scale(factor,factor); self.update_view_chrome(); self.selection_overlay()
        event.accept()

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self.start is not None:
            self.cancel_gesture('Stroke cancelled.'); event.accept(); return
        if event.key()==Qt.Key.Key_Space: self.space=True; self.setCursor(Qt.CursorShape.OpenHandCursor); event.accept(); return
        super().keyPressEvent(event)
    def keyReleaseEvent(self,event):
        if event.key()==Qt.Key.Key_Space: self.space=False; self.unsetCursor(); event.accept(); return
        super().keyReleaseEvent(event)

    def mousePressEvent(self,event):
        if not self.ws.active: return
        if event.button()==Qt.MouseButton.MiddleButton or self.space or self.window.tool=='hand':
            if self.start is not None: self.cancel_gesture()
            self.pan=True; self.pan_point=event.position(); self.setCursor(Qt.CursorShape.ClosedHandCursor); return
        if event.button()!=Qt.MouseButton.LeftButton: return
        point=self.mapToScene(event.position().toPoint()); self.start=point; self.end=point; self.points=[[point.x(),point.y(),self.pressure]]
        self.source_revision=self.ws.document().revision
        self.source_document_id=self.ws.active
        self.move_mode='translate'
        tool=self.window.tool
        if tool in ('brush','erase'):
            try:
                layer=self.ws.document().layer()
                if layer.locked: raise ValueError('Layer is locked')
                if layer.kind in ('group','adjustment') and not self.window.mask_target.isChecked(): raise ValueError('Choose a pixel layer or paint its mask')
                args={'size':self.window.brush_size.value(),'opacity':self.window.brush_opacity.value()/100,'hardness':self.window.hardness.value()/100,'color':self.window.color}
                if self.window.mask_target.isChecked(): args.update(target='mask',maskValue=0 if tool=='erase' else 255)
                self.gesture=EditPreview(self.ws.document(),tool,args); self.stroke_shift=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                self.ws.view['gesture']={'documentId':self.source_document_id,'sourceRevision':self.source_revision,'layerId':layer.id,'operation':tool,'status':'preview'}
                self.window.statusBar().showMessage('Painting · Esc to cancel'); self.render_preview()
            except Exception as error: self.cancel_gesture(str(error))
            return
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
        if self.gesture:
            self.points.append([point.x(),point.y(),self.pressure]); self.stroke_shift=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            if not self.preview_timer.isActive(): self.preview_timer.start()
            return
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
        if self.gesture:
            gesture=self.gesture; point=self.mapToScene(event.position().toPoint()); self.points.append([point.x(),point.y(),self.pressure])
            self.stroke_shift=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier); points=self.stroke_points()
            self.clear_preview(); self.start=None
            if self.ws.active!=gesture.document_id or self.ws.document().active!=gesture.layer_id:
                self.window.statusBar().showMessage('The active layer changed; the unfinished stroke was cancelled.'); return
            result=self.window.edit(gesture.operation,{**gesture.arguments,'points':points},expected=gesture.revision)
            if result: self.last_stroke=points[-1]; self.window.statusBar().clearMessage()
            self.selection_overlay(); return
        start=self.start; end=self.mapToScene(event.position().toPoint()); self.start=None; tool=self.window.tool
        if self.ws.active!=self.source_document_id:
            self.window.statusBar().showMessage('The active document changed during this gesture. Try again on the intended page.'); self.selection_overlay(); return
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

    def stroke_points(self):
        return [self.last_stroke,self.points[-1]] if self.stroke_shift and self.last_stroke else self.points

    def clear_preview(self):
        self.preview_timer.stop(); self.gesture=None; self.ws.view.pop('gesture',None)
        self.art.preview_canvas=None; self.preview_box=None; self.art.update()

    def cancel_gesture(self,message=None):
        self.clear_preview(); self.start=None; self.points=[]; self.selection_overlay()
        if message: self.window.statusBar().showMessage(message,6000)

    def render_preview(self):
        if not self.gesture: return
        try:
            result=self.gesture.render(self.stroke_points())
            if result is None:
                self.art.preview_canvas=None; self.preview_box=None; self.art.update(); return
            box,im=result
            if self.art.preview_canvas is None: self.art.preview_canvas=self.art.pixmap().copy()
            painter=QPainter(self.art.preview_canvas); painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            if self.preview_box is not None:
                x,y,right,bottom=self.preview_box; rect=QRectF(x,y,right-x,bottom-y)
                painter.drawPixmap(rect,self.art.pixmap(),rect)
            painter.drawPixmap(box[0],box[1],pixmap(im)); painter.end()
            self.preview_box=box; self.art.update()
        except Exception as error: self.cancel_gesture(str(error))

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
        configure_application(); self.menuBar().setFixedHeight(32)
        app_icon=Path(__file__).parent/'assets/app-icon-256.png'
        if not app_icon.exists(): app_icon=Path(__file__).resolve().parents[2]/'Compositor/Assets.xcassets/AppIcon.appiconset/app-icon-256.png'
        self.setWindowIcon(QIcon(str(app_icon)))
        self.setWindowTitle('Compositor'); self.resize(1600,1000); self.setMinimumSize(1000,720); self.setStyleSheet(STYLE)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks|QMainWindow.DockOption.AllowNestedDocks)
        self.zoom_label=QLabel('100%'); self.coords_label=QLabel(''); self.document_label=QLabel(); self.statusBar().addWidget(self.zoom_label); self.statusBar().addWidget(self.document_label); self.statusBar().addPermanentWidget(self.coords_label)
        self.canvas=Canvas(self); self.tabs=QTabBar(); self.tabs.setExpanding(False); self.tabs.setTabsClosable(True); self.tabs.currentChanged.connect(self.activate_tab); self.tabs.tabCloseRequested.connect(self.close_tab)
        central=QWidget(); layout=QVBoxLayout(central); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); layout.addWidget(self.tabs)
        frame=QWidget(); grid=QGridLayout(frame); grid.setContentsMargins(0,0,0,0); grid.setSpacing(0); self.rulers=[Ruler(self.canvas,True),Ruler(self.canvas,False)]
        corner=QLabel(); corner.setFixedSize(22,22); corner.setStyleSheet('background:#383838;'); grid.addWidget(corner,0,0); grid.addWidget(self.rulers[0],0,1); grid.addWidget(self.rulers[1],1,0); grid.addWidget(self.canvas,1,1); layout.addWidget(frame,1); self.setCentralWidget(central)
        self.build_menus(); self.build_tools(); self.build_layers(); self.build_generation(); self.build_chat(); self.build_production()
        for dock in (self.generation_dock,self.chat_dock,self.production_dock): dock.hide()
        self.resizeDocks([self.layer_dock],[300],Qt.Orientation.Horizontal)
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
        projects=self.menuBar().addMenu('&Projects'); self.action(projects,'Project library',lambda:self.show_panel(self.production_dock)); self.action(projects,'New artwork, comic or book…',lambda:self.production.create()); self.action(projects,'Open project…',lambda:self.production.open()); projects.addSeparator(); self.action(projects,'Open connected studio',self.open_studio); self.action(projects,'Bring connected project image into editor…',self.pull_project); self.action(projects,'Return artwork to connected project',self.push_project)
        help_menu=self.menuBar().addMenu('&Help'); self.action(help_menu,'About Compositor',lambda:QMessageBox.information(self,'Compositor','Compositor for Windows\nBased on Robbie Tilton’s MIT-licensed Compositor.\nWindows edition by the Compositor contributors.\n\nSpace-drag to pan; wheel to zoom.\nAlt-click sets a clone source.\nShift adds to selections; Alt subtracts.\n\nSave .compwin for editable layers.'))

    def build_tools(self):
        toolbar=QToolBar('Tools'); toolbar.setObjectName('toolRail'); toolbar.setMovable(False); toolbar.setOrientation(Qt.Orientation.Vertical); toolbar.setIconSize(QSize(20,20)); toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly); self.addToolBar(Qt.ToolBarArea.LeftToolBarArea,toolbar); self.tool_actions={}; group=QActionGroup(self); group.setExclusive(True)
        for label,key,shortcut in [('Move','move','V'),('Rectangular marquee','rectangle','M'),('Elliptical marquee','ellipse',None),('Lasso','lasso','L'),('Magic wand','wand','W'),('Crop','crop','C'),('Eyedropper','eyedropper','I'),('Healing brush','heal','J'),('Brush','brush','B'),('Clone stamp','clone','S'),('Eraser','erase','E'),('Gradient','gradient','G'),('Blur','blur_brush',None),('Type','text','T'),('Shape','shape','U'),('Hand','hand','H')]:
            a=QAction(icon(key),label,self); a.setCheckable(True); a.setToolTip(label+(f' ({shortcut})' if shortcut else '')); a.triggered.connect(lambda checked,key=key:self.set_tool(key)); group.addAction(a); toolbar.addAction(a); self.tool_actions[key]=a
            if shortcut: a.setShortcut(shortcut)
            toolbar.widgetForAction(a).setFixedSize(34,32); toolbar.widgetForAction(a).setAccessibleName(label)
        self.tool_actions['move'].setChecked(True)
        toolbar.addSeparator(); toolbar.addWidget(icon_button('zoom','Actual pixels (Ctrl+1)',self.canvas.resetTransform)); toolbar.addWidget(icon_button('fit','Fit canvas (Ctrl+0)',self.canvas.fit))
        toolbar.addSeparator()
        swatches=QWidget(); swatches.setFixedSize(34,64)
        self.background_button=QPushButton(swatches); self.background_button.setGeometry(2,30,32,32); self.background_button.setToolTip('Background color'); self.background_button.setAccessibleName('Background color'); self.background_button.clicked.connect(self.pick_background)
        self.color_button=QPushButton(swatches); self.color_button.setGeometry(0,0,32,32); self.color_button.setToolTip('Foreground color'); self.color_button.setAccessibleName('Foreground color'); self.color_button.clicked.connect(self.pick_color); toolbar.addWidget(swatches)
        swap=QAction('Swap foreground and background',self); swap.setShortcut('X'); swap.triggered.connect(self.swap_colors); self.addAction(swap)
        self.update_color()
        options=QToolBar('Tool options'); options.setMovable(False); options.setMinimumHeight(42); self.addToolBar(options)
        self.tool_caption=QLabel('Move'); self.tool_caption.setMinimumWidth(105); self.tool_caption.setContentsMargins(8,0,10,0); options.addWidget(self.tool_caption); options.addSeparator()
        self.option_widgets=[]
        def option(widget,tools):
            self.option_widgets.append((options.addWidget(widget),tools)); return widget
        paint={'brush','erase','heal','clone','blur_brush'}
        self.brush_size=QSpinBox(); self.brush_size.setRange(1,2048); self.brush_size.setValue(32); self.brush_size.setSuffix(' px'); self.brush_size.setFixedWidth(82); self.brush_size.setAccessibleName('Brush size'); option(QLabel(' Size '),paint); option(self.brush_size,paint)
        self.brush_opacity=QSpinBox(); self.brush_opacity.setRange(1,100); self.brush_opacity.setValue(100); self.brush_opacity.setSuffix('%'); self.brush_opacity.setFixedWidth(72); self.brush_opacity.setAccessibleName('Brush opacity'); option(QLabel(' Opacity '),paint); option(self.brush_opacity,paint)
        self.hardness=QSpinBox(); self.hardness.setRange(0,100); self.hardness.setValue(80); self.hardness.setSuffix('%'); self.hardness.setFixedWidth(72); self.hardness.setAccessibleName('Brush hardness'); option(QLabel(' Hardness '),paint); option(self.hardness,paint)
        self.mask_target=QCheckBox('Paint mask'); option(self.mask_target,paint)
        self.tolerance=QSpinBox(); self.tolerance.setRange(0,255); self.tolerance.setValue(32); self.tolerance.setAccessibleName('Magic wand tolerance'); option(QLabel(' Tolerance '),{'wand'}); option(self.tolerance,{'wand'})
        self.shape_kind=QComboBox(); self.shape_kind.addItems(['rectangle','ellipse','rounded','line']); option(self.shape_kind,{'shape'})
        self.radial=QCheckBox('Radial'); option(self.radial,{'gradient'})
        self.show_transform=QCheckBox('Transform controls'); self.show_transform.setChecked(True); self.show_transform.toggled.connect(self.canvas.selection_overlay); option(self.show_transform,{'move'})
        self.selection_hint=QLabel('Shift: add    Alt: subtract'); option(self.selection_hint,{'rectangle','ellipse','lasso','wand'})
        spacer=QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred); options.addWidget(spacer)
        for name,label,attribute in [('generate','Generate','generation_dock'),('chat','ChatGPT','chat_dock'),('book','Projects','production_dock')]:
            button=QToolButton(); button.setIcon(icon(name)); button.setIconSize(QSize(18,18)); button.setText(label); button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon); button.setMinimumWidth(96); button.setToolTip('Open '+label); button.clicked.connect(lambda checked=False,attribute=attribute:self.show_panel(getattr(self,attribute))); options.addWidget(button)
        self.update_tool_options()

    def show_panel(self,dock):
        for other in (self.generation_dock,self.chat_dock,self.production_dock):
            if other is not dock: other.hide()
        dock.show(); dock.raise_(); self.resizeDocks([dock,self.layer_dock],[360,300],Qt.Orientation.Horizontal)

    def dock(self,title,widget):
        dock=QDockWidget(title,self); dock.setWidget(widget); dock.setMinimumWidth(300); dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock)
        # Secondary workspaces open beside the permanent inspector, preserving Layers.
        self.splitDockWidget(self.layer_dock,dock,Qt.Orientation.Horizontal)
        header=QWidget(); row=QHBoxLayout(header); row.setContentsMargins(10,0,4,0); row.addWidget(QLabel(title)); row.addStretch(); row.addWidget(icon_button('close','Close '+title,dock.hide)); dock.setTitleBarWidget(header)
        return dock

    def build_layers(self):
        inspector=QWidget(); inspector.setObjectName('inspector'); outer=QVBoxLayout(inspector); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        stack=QSplitter(Qt.Orientation.Vertical); stack.setChildrenCollapsible(False); stack.setHandleWidth(4); outer.addWidget(stack)
        def section(title,widget):
            tabs=QTabWidget(); tabs.addTab(widget,title); stack.addWidget(tabs); return tabs
        self.color_panel=ColorPanel(self); section('Color',self.color_panel).setMinimumHeight(150); self.color_panel.sync()
        properties=QWidget(); prop=QVBoxLayout(properties); prop.setContentsMargins(12,8,12,8); prop.setSpacing(6)
        self.layer_caption=QLabel('No layer selected'); self.layer_caption.setWordWrap(True); prop.addWidget(self.layer_caption)
        label=QLabel('Transform'); label.setObjectName('sectionLabel'); prop.addWidget(label)
        fields=QGridLayout(); fields.setHorizontalSpacing(8); fields.setVerticalSpacing(4); self.transform_fields={}
        for key,label,r,c in [('sx','W',0,0),('sy','H',0,2),('x','X',1,0),('y','Y',1,2),('angle','Angle',2,0)]:
            spin=QDoubleSpinBox(); spin.setRange(-100000,100000); spin.setDecimals(1); spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons); spin.setMinimumWidth(60); spin.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed); spin.setSuffix(' px' if key!='angle' else '°'); spin.setSingleStep(1); spin.setAccessibleName({'sx':'Layer width','sy':'Layer height'}.get(key,label)); spin.editingFinished.connect(lambda key=key,spin=spin:self.transform_changed(key,spin.value())); self.transform_fields[key]=spin
            fields.addWidget(QLabel(label),r,c); fields.addWidget(spin,r,c+1)
        flips=QHBoxLayout(); flips.setSpacing(0); flips.addWidget(icon_button('flip_h','Flip horizontally',lambda:self.flip('sx'))); flips.addWidget(icon_button('flip_v','Flip vertically',lambda:self.flip('sy'))); fields.addLayout(flips,2,2,1,2); prop.addLayout(fields)
        self.parent_group=QComboBox(); self.parent_group.setAccessibleName('Parent group'); self.parent_group.currentIndexChanged.connect(self.change_group); prop.addWidget(self.parent_group)
        edit_content=QPushButton('Edit content…'); edit_content.clicked.connect(self.edit_layer_content); prop.addWidget(edit_content); prop.addStretch(); section('Properties',properties).setMinimumHeight(280)
        panel=QWidget(); layout=QVBoxLayout(panel); layout.setContentsMargins(0,6,0,0); layout.setSpacing(4)
        row=QHBoxLayout(); row.setContentsMargins(8,0,8,0); self.blend=QComboBox(); self.blend.addItems(pixels.BLENDS); self.blend.setAccessibleName('Layer blend mode'); self.blend.currentTextChanged.connect(lambda v:self.property_changed('blend',v)); row.addWidget(self.blend,1)
        row.addWidget(QLabel('Opacity')); self.opacity=QSpinBox(); self.opacity.setRange(0,100); self.opacity.setSuffix('%'); self.opacity.setFixedWidth(67); self.opacity.setAccessibleName('Layer opacity'); self.opacity.valueChanged.connect(lambda v:self.property_changed('opacity',v/100)); row.addWidget(self.opacity); layout.addLayout(row)
        row=QHBoxLayout(); row.setContentsMargins(8,0,8,0); self.locked=QCheckBox('Lock'); self.locked.toggled.connect(lambda v:self.property_changed('locked',v)); row.addWidget(self.locked)
        self.clipping=QCheckBox('Clip to layer below'); self.clipping.toggled.connect(lambda v:self.property_changed('clipping',v)); row.addWidget(self.clipping); row.addStretch(); layout.addLayout(row)
        self.layers=QListWidget(); self.layers.setIconSize(QSize(40,30)); self.layers.setItemDelegate(LayerDelegate(self.layers)); self.layers.itemClicked.connect(self.select_layer); self.layers.itemChanged.connect(self.layer_changed); self.layers.itemDoubleClicked.connect(lambda _:self.rename_layer()); layout.addWidget(self.layers,1)
        buttons=QHBoxLayout(); buttons.setContentsMargins(4,2,4,2); buttons.setSpacing(1); buttons.addStretch()
        for name,label,fn in [('effects','Layer effects',self.effects_dialog),('mask','Add layer mask',lambda:self.edit('mask',{'mode':'white'})),('group','New group',lambda:self.edit('add_layer',{'kind':'group','name':'Group'})),('plus','New layer',lambda:self.edit('add_layer')),('copy','Duplicate layer',lambda:self.edit('duplicate_layer')),('up','Raise layer',lambda:self.reorder(1)),('down','Lower layer',lambda:self.reorder(-1)),('delete','Delete layer',lambda:self.edit('delete_layer'))]: buttons.addWidget(icon_button(name,label,fn))
        layout.addLayout(buttons); section('Layers',panel).setMinimumHeight(200)
        stack.setSizes([210,280,370]); self.inspector_stack=stack
        self.layer_dock=QDockWidget('Inspector',self); self.layer_dock.setWidget(inspector); self.layer_dock.setMinimumWidth(300); self.layer_dock.setMaximumWidth(340); self.layer_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures); self.layer_dock.setTitleBarWidget(QWidget()); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.layer_dock)

    def build_generation(self):
        panel=QWidget(); layout=QVBoxLayout(panel); layout.setSpacing(10); self.prompt=QPlainTextEdit(); self.prompt.setPlaceholderText('Describe an image or the change you want…'); self.prompt.setFixedHeight(130); layout.addWidget(self.prompt)
        row=QHBoxLayout(); self.gen_kind=QComboBox(); self.gen_kind.addItem('New image','generate'); self.gen_kind.addItem('Edit whole image','edit'); self.gen_kind.addItem('Refine selected area','patch'); row.addWidget(self.gen_kind)
        self.gen_size=QComboBox(); self.gen_size.setEditable(True); self.gen_size.addItems(['1024x1024','1536x1024','1024x1536','2048x1152']); row.addWidget(self.gen_size); layout.addLayout(row)
        row=QHBoxLayout(); ref=QPushButton('References…'); ref.clicked.connect(self.choose_references); row.addWidget(ref); self.ref_label=QLabel('None'); row.addWidget(self.ref_label); layout.addLayout(row)
        self.gen_provider_label=QLabel(); self.gen_provider_label.setWordWrap(True); layout.addWidget(self.gen_provider_label)
        generate=QPushButton('Generate candidate'); generate.clicked.connect(self.generate); layout.addWidget(generate)
        self.jobs=QListWidget(); self.jobs.setIconSize(QSize(56,48)); layout.addWidget(self.jobs,1)
        row=QHBoxLayout()
        for title,fn in [('Inspect',self.inspect_job),('Apply',self.apply_job),('Place as layer',self.import_job)]:
            b=QPushButton(title); b.clicked.connect(fn); row.addWidget(b)
        layout.addLayout(row); self.generation_dock=self.dock('Generate',panel); self.generation_dock.hide()

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
        self.chat_dock=self.dock('ChatGPT',panel); self.chat_dock.hide(); self.chat=None

    def build_production(self):
        from .production_ui import ProductionPanel
        self.production=ProductionPanel(self); self.production_dock=self.dock('Projects',self.production); self.production_dock.hide()

    def run(self,action,args=None):
        try:
            result=self.ws.dispatch(action,args)
            if isinstance(result,dict) and result.get('conversionReport'): QMessageBox.information(self,'Import notes','\n'.join(result['conversionReport']))
            return result
        except Exception as e: self.statusBar().showMessage(str(e),18000); QMessageBox.warning(self,'Compositor',str(e)); return None
    def edit(self,operation,args=None,expected=None): return self.run('edit',{'operation':operation,'args':args or {},'expectedRevision':expected})
    def set_tool(self,key):
        if self.canvas.start is not None: self.canvas.cancel_gesture()
        self.tool=key; self.tool_actions[key].setChecked(True); self.update_tool_options(); self.canvas.selection_overlay(); self.statusBar().showMessage(self.tool_actions[key].toolTip(),3000)
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor if key=='hand' else Qt.CursorShape.ArrowCursor if key=='move' else Qt.CursorShape.CrossCursor)
    def update_tool_options(self):
        if not hasattr(self,'option_widgets'): return
        self.tool_caption.setText(self.tool_actions[self.tool].text())
        for action,tools in self.option_widgets: action.setVisible(self.tool in tools)
    def update_color(self):
        self.color_button.setStyleSheet(f'background:{self.color};border:2px solid #c8c8c8;padding:0;')
        self.background_button.setStyleSheet(f'background:{self.background_color};border:2px solid #888;padding:0;')
        if hasattr(self,'color_panel'): self.color_panel.sync()
    def swap_colors(self):
        self.color,self.background_color=self.background_color,self.color; self.update_color()
    def pick_background(self):
        color=QColorDialog.getColor(QColor(self.background_color),self,'Background color')
        if color.isValid(): self.background_color=color.name(); self.update_color()
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
                close=icon_button('close','Close '+d.title,lambda checked=False,doc_id=d.id:self.close_document_tab(doc_id)); self.tabs.setTabButton(i,QTabBar.ButtonPosition.RightSide,close)
                if d.id==self.ws.active: self.tabs.setCurrentIndex(i)
            self.tabs.blockSignals(False); self.layers.clear()
            if self.ws.active:
                d=self.ws.document(); self.setWindowTitle(d.title+' — Compositor'); self.document_label.setText(f'{d.width} × {d.height} px   ·   RGB / 8')
                for l in reversed(d.layers):
                    item=QListWidgetItem(('    ' if l.parent else '')+l.name+('  ◐' if l.mask else '')); item.setData(Qt.ItemDataRole.UserRole,l.id); item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked if l.visible else Qt.CheckState.Unchecked)
                    if l.kind not in ('group','adjustment'):
                        im=pixels.content(l).copy(); im.thumbnail((40,32)); item.setIcon(QIcon(pixmap(im)))
                    self.layers.addItem(item)
                    if l.id==d.active: self.layers.setCurrentItem(item)
                if d.active:
                    l=d.layer(); self.blend.setCurrentText(l.blend); self.opacity.setValue(round(l.opacity*100)); self.locked.setChecked(l.locked); self.clipping.setChecked(l.clipping)
                    self.layer_caption.setText(l.kind.title()+' layer · '+l.name)
                    content=pixels.content(l)
                    for k,spin in self.transform_fields.items(): spin.setValue(abs(l.sx)*content.width if k=='sx' else abs(l.sy)*content.height if k=='sy' else getattr(l,k))
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
    def close_document_tab(self,doc_id):
        for i in range(self.tabs.count()):
            if self.tabs.tabData(i)==doc_id: self.close_tab(i); return
    def close_tab(self,index):
        d=self.ws.document(self.tabs.tabData(index))
        if d.revision!=d.saved_revision and not self.ws.projects.for_document(d.id):
            answer=QMessageBox.question(self,'Close document','Save changes to '+d.title+'?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
            if answer==QMessageBox.StandardButton.Cancel: return
            if answer==QMessageBox.StandardButton.Save:
                self.run('activate',{'documentId':d.id})
                if not self.save(): return
        self.run('close',{'documentId':d.id,'discard':True})
    def property_changed(self,key,value):
        if not self.refreshing and self.ws.active and self.ws.document().active:
            if getattr(self.ws.document().layer(),key)!=value: self.edit('update_layer',{key:value})
    def transform_changed(self,key,value):
        if self.refreshing or not self.ws.active or not self.ws.document().active: return
        layer=self.ws.document().layer()
        if key in ('sx','sy'):
            content=pixels.content(layer); value=math.copysign(max(.01,value/(content.width if key=='sx' else content.height)),getattr(layer,key))
        self.property_changed(key,value)
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
            elif key in ('text','story','artDirection'): control=QPlainTextEdit(str(value)); control.setMinimumSize(320,120)
            else: control=QLineEdit(str(value))
            layout.addRow(key.replace('_',' ').title(),control); controls[key]=control
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); layout.addRow(buttons)
        if dialog.exec()!=QDialog.DialogCode.Accepted: return None
        return {k:c.isChecked() if isinstance(c,QCheckBox) else c.value() if isinstance(c,QDoubleSpinBox) else c.toPlainText() if isinstance(c,QPlainTextEdit) else c.text() for k,c in controls.items()}

    def new_document(self):
        a=self.form_dialog('New document',{'title':'Untitled','width':1536,'height':1024,'background':'#ffffff'})
        if a: self.run('new',a)
    def open_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Open image or document','','Images and documents (*.compwin *.compbook *.ora *.psd *.png *.jpg *.jpeg *.webp *.tif *.tiff *.heic *.bmp);;All files (*)')
        if path: self.run('open',{'path':path})
    def import_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Add image as layer','','Images (*.png *.jpg *.jpeg *.webp *.tif *.tiff *.heic *.bmp)')
        if path: self.edit('import_image',{'path':path})
    def save(self,as_copy=False):
        if not self.ws.active: return None
        linked=self.ws.projects.for_document(self.ws.active)
        if linked:
            self.ws.projects.active=linked[0]['id']; self.production.refresh(); return self.production.save()
        d=self.ws.document(); path=d.path
        if as_copy or not path: path,_=QFileDialog.getSaveFileName(self,'Save layered document',d.title+'.compwin','Compositor document (*.compwin);;OpenRaster (*.ora)')
        return self.run('save',{'path':path,'documentId':d.id}) if path else None
    def export(self):
        if not self.ws.active: return
        d=self.ws.document(); path,_=QFileDialog.getSaveFileName(self,'Export image',d.title+'.png','PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;TIFF (*.tif)')
        if path: self.run('export',{'path':path,'documentId':d.id})
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
        self.production.save_drafts(); self.ws.save_recovery()
        if self.chat: self.chat.shutdown()
        event.accept()
