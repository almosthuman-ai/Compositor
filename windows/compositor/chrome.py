"""Editor chrome: original vector icons, document rulers and direct color controls."""
import math
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QSize, Signal, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QIcon, QLinearGradient, QPalette
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QWidget, QToolButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QStyledItemDelegate, QStyle, QComboBox

def configure_application():
    app=QApplication.instance(); app.setStyle('Fusion')
    palette=QPalette()
    for role,color in [('Window','#454545'),('WindowText','#dedede'),('Base','#383838'),('AlternateBase','#444444'),('Text','#dedede'),('Button','#454545'),('ButtonText','#dedede'),('Highlight','#626262'),('HighlightedText','#ffffff'),('Light','#727272'),('Mid','#555555'),('Dark','#282828')]:
        palette.setColor(getattr(QPalette.ColorRole,role),QColor(color))
    app.setPalette(palette)

# Original 24-unit paths. No platform symbol fonts or external icon downloads.
PATHS = {
    'move':'<path d="M12 3v18M3 12h18M9 6l3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3"/>',
    'rectangle':'<rect x="4" y="5" width="16" height="14" stroke-dasharray="3 3"/>',
    'ellipse':'<ellipse cx="12" cy="12" rx="8" ry="7" stroke-dasharray="3 3"/>',
    'lasso':'<path d="M8 17C0 13 3 5 12 5s12 9 3 12c-7 2-10-1-8-3s7 0 5 5c-1 2-3 3-5 2"/>',
    'wand':'<path d="m5 20 13-13 2 2L7 22zM5 3v5M2.5 5.5h5M16 1v4M14 3h4M21 15v4M19 17h4"/>',
    'crop':'<path d="M7 2v15h15M2 7h15v15M10 7h7v7"/>',
    'brush':'<path d="M9 15 18 3c2-2 4 0 2 2L12 17zM9 15c-5 0-2 5-6 5 4 3 9 0 9-3"/>',
    'erase':'<path d="m3 14 10-11 8 7-9 10H9zM8 9l9 8M12 20h10"/>',
    'heal':'<path d="m4 13 9-9c5-5 11 1 6 6l-9 9c-5 5-11-1-6-6zM8 9l7 7M10 8l7 7"/><path d="m9 13 .1 .1m3-3 .1 .1m0 6 .1 .1m3-3 .1 .1"/>',
    'clone':'<path d="M5 18h14v3H5zM4 18v-4h5v-3c-4-7 10-7 6 0v3h5v4"/>',
    'blur_brush':'<path d="M12 2C10 7 5 11 5 15a7 7 0 0 0 14 0c0-4-5-8-7-13zM8 15c0 2 1 3 3 3"/>',
    'text':'<path d="M4 7V4h16v3M12 4v17M8 21h8"/>',
    'shape':'<rect x="4" y="4" width="16" height="16" rx="1"/>',
    'gradient':'<defs><linearGradient id="g"><stop stop-color="#ddd"/><stop offset="1" stop-color="#333"/></linearGradient></defs><rect x="3" y="5" width="18" height="14" fill="url(#g)"/>',
    'eyedropper':'<path d="m15 4 5 5M14 6 4 16v4h4L18 10M14 6l4-4 4 4-4 4"/>',
    'hand':'<path d="M7 12V6c0-3 3-3 3 0V4c0-3 3-3 3 0v2c0-3 3-3 3 0v2c0-3 3-3 3 0v8c0 7-10 8-13 3l-4-6c-1-3 2-3 5 0z"/>',
    'zoom':'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6M7 10h6M10 7v6"/>',
    'fit':'<path d="M9 3H3v6M15 3h6v6M3 15v6h6M21 15v6h-6"/><rect x="7" y="7" width="10" height="10"/>',
    'plus':'<path d="M12 5v14M5 12h14"/>',
    'copy':'<rect x="8" y="8" width="13" height="13" rx="1"/><path d="M16 5V3H3v13h2"/>',
    'up':'<path d="m6 14 6-6 6 6"/>',
    'down':'<path d="m6 10 6 6 6-6"/>',
    'delete':'<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7"/>',
    'group':'<path d="M3 6h7l2 3h9v11H3z"/>',
    'mask':'<rect x="3" y="5" width="18" height="14"/><circle cx="12" cy="12" r="4"/>',
    'effects':'<path d="M15 3c-4-2-6 0-6 4L7 20c0 3-3 3-4 1M5 9h9M15 13l6 8M21 13l-6 8"/>',
    'eye':'<path d="M2 12c5-9 15-9 20 0-5 9-15 9-20 0z"/><circle cx="12" cy="12" r="3"/>',
    'lock':'<rect x="5" y="10" width="14" height="11" rx="1"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
    'generate':'<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3zM20 1v4M18 3h4"/>',
    'chat':'<path d="M4 3h16v14H9l-5 4zM8 8h8M8 12h5"/>',
    'book':'<path d="M12 5C8 2 4 3 2 4v16c3-2 7-2 10 0 3-2 7-2 10 0V4c-2-1-6-2-10 1v15"/>',
    'swap':'<path d="M4 8h16l-4-4M20 16H4l4 4"/>',
    'flip_h':'<path d="M12 2v20M8 6 3 18h5zM16 6l5 12h-5z"/>',
    'flip_v':'<path d="M2 12h20M6 8l12-5v5zM6 16l12 5v-5z"/>',
    'close':'<path d="m6 6 12 12M6 18 18 6"/>',
    'save':'<path d="M4 3h13l4 4v14H3V3zM7 3v7h10V3M7 21v-7h10v7"/>',
}

def icon(name, color='#d2d2d2'):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</g></svg>'
    renderer=QSvgRenderer(svg.encode()); pm=QPixmap(48,48); pm.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pm); renderer.render(painter); painter.end(); pm.setDevicePixelRatio(2)
    return QIcon(pm)

def icon_button(name, label, callback, parent=None):
    b=QToolButton(parent); b.setIcon(icon(name)); b.setIconSize(QSize(18,18)); b.setFixedSize(32,32)
    b.setToolTip(label); b.setAccessibleName(label); b.clicked.connect(callback); return b

class EditorComboBox(QComboBox):
    def paintEvent(self,event):
        super().paintEvent(event)
        painter=QPainter(self); icon('down').paint(painter,self.width()-21,(self.height()-16)//2,16,16)

class Ruler(QWidget):
    def __init__(self,canvas,horizontal):
        super().__init__(); self.canvas=canvas; self.horizontal=horizontal
        if horizontal: self.setFixedHeight(22)
        else: self.setFixedWidth(22)
        self.setAccessibleName('Horizontal pixel ruler' if horizontal else 'Vertical pixel ruler')
    def paintEvent(self,event):
        p=QPainter(self); p.fillRect(self.rect(),QColor('#383838')); p.setPen(QColor('#818181'))
        font=p.font(); font.setPixelSize(9); p.setFont(font)
        zoom=self.canvas.transform().m11()
        if zoom<=0: return
        point=self.canvas.mapToScene(0,0); origin=point.x() if self.horizontal else point.y()
        raw=70/zoom; power=10**math.floor(math.log10(raw)); step=next(v*power for v in (1,2,5,10) if v*power>=raw)
        length=self.width() if self.horizontal else self.height(); minor=step/5; first=math.floor(origin/minor)
        for i in range(first,first+int(length/zoom/minor)+3):
            position=round((i*minor-origin)*zoom); major=i%5==0
            if self.horizontal:
                p.drawLine(position,22,position,14 if major else 18)
                if major: p.drawText(position+3,10,str(round(i*minor)))
            else:
                p.drawLine(22,position,14 if major else 18,position)
                if major:
                    p.save(); p.translate(10,position+3); p.rotate(-90); p.drawText(0,0,str(round(i*minor))); p.restore()

class ColorPlane(QWidget):
    changed=Signal(QColor)
    def __init__(self,hue=False):
        super().__init__(); self.hue_strip=hue; self.color=QColor('#efab70'); self.hue=self.color.hsvHueF()
        self.setMinimumSize(32,32); self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAccessibleName('Hue' if hue else 'Saturation and brightness')
        if hue: self.setFixedWidth(32)
    def paintEvent(self,event):
        p=QPainter(self); r=self.rect().adjusted(1,1,-1,-1)
        if self.hue_strip:
            gradient=QLinearGradient(0,0,0,self.height())
            for i in range(7): gradient.setColorAt(i/6,QColor.fromHsvF(i/6,1,1))
            p.fillRect(r,gradient); y=max(2,min(self.height()-3,self.hue*self.height()))
            p.setPen(QPen(QColor('white'),2)); p.drawRect(QRectF(1,y-2,self.width()-3,4))
        else:
            p.fillRect(r,QColor.fromHsvF(self.hue,1,1)); g=QLinearGradient(0,0,self.width(),0); g.setColorAt(0,QColor('white')); g.setColorAt(1,QColor(255,255,255,0)); p.fillRect(r,g)
            g=QLinearGradient(0,0,0,self.height()); g.setColorAt(0,QColor(0,0,0,0)); g.setColorAt(1,QColor('black')); p.fillRect(r,g)
            x=self.color.hsvSaturationF()*(self.width()-2)+1; y=(1-self.color.valueF())*(self.height()-2)+1
            p.setPen(QPen(QColor('#151515'),3)); p.drawEllipse(QPointF(x,y),4,4); p.setPen(QPen(QColor('white'),1)); p.drawEllipse(QPointF(x,y),4,4)
    def choose(self,event):
        x=max(0,min(1,event.position().x()/max(1,self.width()-1))); y=max(0,min(1,event.position().y()/max(1,self.height()-1)))
        if self.hue_strip: self.hue=min(.9999,y); color=QColor.fromHsvF(self.hue,self.color.hsvSaturationF(),self.color.valueF())
        else: color=QColor.fromHsvF(self.hue,x,1-y)
        self.changed.emit(color)
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton: self.choose(event)
    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton: self.choose(event)

class ColorPanel(QWidget):
    def __init__(self,editor):
        super().__init__(); self.editor=editor; layout=QVBoxLayout(self); layout.setContentsMargins(12,10,12,10); layout.setSpacing(8)
        row=QHBoxLayout(); row.setSpacing(10); self.plane=ColorPlane(); self.hue=ColorPlane(True); row.addWidget(self.plane,1); row.addWidget(self.hue); layout.addLayout(row,1)
        bottom=QHBoxLayout(); self.sample=QLabel(); self.sample.setFixedSize(24,24); bottom.addWidget(self.sample)
        self.hex=QLineEdit(); self.hex.setAccessibleName('Foreground color hex'); self.hex.setMaxLength(7); self.hex.setMaximumWidth(100); self.hex.editingFinished.connect(self.from_hex)
        bottom.addWidget(self.hex); bottom.addStretch(); bottom.addWidget(icon_button('swap','Swap foreground and background (X)',editor.swap_colors)); layout.addLayout(bottom)
        self.plane.changed.connect(self.set_color); self.hue.changed.connect(self.set_color)
    def set_color(self,color):
        if color.hsvHueF()>=0: self.plane.hue=self.hue.hue=color.hsvHueF()
        self.editor.color=color.name(); self.editor.update_color()
    def from_hex(self):
        color=QColor(self.hex.text())
        if color.isValid(): self.set_color(color)
        else: self.sync()
    def sync(self):
        color=QColor(self.editor.color); self.hex.setText(color.name()); self.sample.setStyleSheet(f'background:{color.name()};border:1px solid #777;')
        hue=color.hsvHueF()
        for field in (self.plane,self.hue):
            field.color=color
            if hue>=0: field.hue=hue
            field.update()

class LayerDelegate(QStyledItemDelegate):
    """Keep native selection/checkbox semantics, draw an eye in its 32 px hit region."""
    def paint(self,painter,option,index):
        self.initStyleOption(option,index); checked=index.data(Qt.ItemDataRole.CheckStateRole)==Qt.CheckState.Checked.value
        full=QRect(option.rect); painter.save(); painter.fillRect(full,QColor('#626262' if option.state & QStyle.StateFlag.State_Selected else '#454545'))
        if checked: icon('eye').paint(painter,full.x()+7,full.center().y()-9,18,18)
        thumb=QRect(full.x()+34,full.center().y()-15,40,30)
        for y in range(0,30,5):
            for x in range(0,40,5): painter.fillRect(thumb.x()+x,thumb.y()+y,5,5,QColor('#777' if (x+y)%10 else '#aaa'))
        if not option.icon.isNull(): option.icon.paint(painter,thumb)
        painter.setPen(QColor('#2d2d2d')); painter.drawRect(thumb)
        painter.setPen(QColor('#eee')); painter.setFont(option.font); text_rect=full.adjusted(82,0,-6,0)
        painter.drawText(text_rect,Qt.AlignmentFlag.AlignVCenter,option.fontMetrics.elidedText(option.text,Qt.TextElideMode.ElideRight,text_rect.width())); painter.restore()
    def editorEvent(self,event,model,option,index):
        if event.type()==QEvent.Type.MouseButtonRelease and event.button()==Qt.MouseButton.LeftButton and event.position().x()<option.rect.x()+32:
            value=index.data(Qt.ItemDataRole.CheckStateRole)
            model.setData(index,Qt.CheckState.Unchecked if value==Qt.CheckState.Checked.value else Qt.CheckState.Checked,Qt.ItemDataRole.CheckStateRole); return True
        return super().editorEvent(event,model,option,index)
