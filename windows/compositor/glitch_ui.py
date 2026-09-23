"""Native, shared-document controls for Tai Mei's Glitch Temple engine."""
import copy,json,re,uuid
from pathlib import Path
from PIL import Image
from shiboken6 import isValid
from PySide6.QtCore import Qt,QTimer,QSize,QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QWidget,QLabel,QPushButton,QComboBox,
    QSpinBox,QDoubleSpinBox,QCheckBox,QLineEdit,QListWidget,QListWidgetItem,QSplitter,QScrollArea,QTabWidget,
    QGraphicsView,QGraphicsScene,QGraphicsPixmapItem,QColorDialog,QFileDialog)

CHOICES={
 'composition':['field','inlay'],'glyphLogic':['mass','repeat'],'inkMode':['source','palette','chosen'],
 'mutationMode':['held','drift','fracture'],'colorSpace':['rgb','hsb'],'channels':['together','separate'],
 'path':['rows','columns','snake','clustered'],'reconstruction':['fold','wrap','clip','reflect'],
 'method':['bubble','insertion','selection','merge','permute','roll'],'action':['sort','sort-outline','wand'],
 'direction':['left','right','up','down'],'signal':['red','green','blue','hue','saturation','brightness'],
 'territory':['whole','light','dark','edges','red','orange','yellow','green','cyan','blue','pink'],
 'resolution':['pixel','fixed','wake'],'colorMode':['source','palette'],
}
RANGES={'mass':(0,1,.01),'structure':(0,1,.01),'grain':(0,1,.01),'compression':(1,1200,1),
 'expansion':(0,1200,1),'channelPhase':(-48,48,1),'tide':(0,1,.01),'amount':(0,1,.0001),
 'gate':(0,1200,1),'minBlock':(1,32,1),'maxBlock':(1,32,1),'selectionSpeed':(0,12,1),
 'threshold':(0,1,.01),'softness':(0,.5,.01),'hue':(0,359,1),'hueWidth':(1,180,1),'scale':(2,240,1),
 'seed':(0,2000000000,1),'colorSeed':(0,2000000000,1),'iteration':(0,100000,1),'sourcePresence':(0,1,.01),
 'hueSpread':(0,180,1),'saturation':(0,100,1),'saturationRange':(0,100,1),
 'lightnessFloor':(0,100,1),'lightnessCeiling':(0,100,1),'loopFrames':(2,240,1),'loopFps':(1,30,1)}
LABELS={'sourcePresence':'Source presence','seed':'Structure seed','colorSeed':'Color seed','glyphs':'Character sequence',
 'newStructureScale':'Vary scale anatomy','newStructureWhere':'Vary territory','newColors':'Vary color behavior',
 'inkMode':'Ink','glyphLogic':'Character logic','composition':'Canvas','loopFrames':'Frames','loopFps':'Frames per second'}


class GlitchDialog(QDialog):
    def __init__(self,editor):
        super().__init__(editor); self.editor=editor; self.ws=editor.ws; self.document=self.ws.document()
        self.recipe=None; self.catalog=None; self.job_id=None; self.loop_id=None; self.local_revision=0; self.render_revision=None; self.updating=False
        self.export_options={'scale':1} if self.document.pixel_art else {'maxDimension':960}
        self.setWindowTitle('Glitch Temple'); self.resize(1200,850); self.setMinimumSize(960,680)
        layout=QVBoxLayout(self); top=QHBoxLayout(); layout.addLayout(top)
        title=QLabel('Glitch Temple'); title.setStyleSheet('font-size:20px;font-weight:600;'); top.addWidget(title)
        credit=QLabel('By Tai Mei'); credit.setStyleSheet('color:#a4a4aa;'); top.addWidget(credit); top.addStretch()
        self.source=QComboBox(); self.source.addItem('Selected layer','layer'); self.source.addItem('Complete composition','composite'); self.source.addItem('Generated field','generated')
        layer=self.document.layer() if self.document.layers else None
        self.layer_id=layer.id if layer else None
        if layer and layer.effect_source is not None: self.source.addItem('Original source','treatment'); self.source.setCurrentIndex(3)
        if not layer:self.source.setCurrentIndex(2)
        self.source.setMinimumHeight(32);top.addWidget(self.source); self.source.currentIndexChanged.connect(self.dirty)
        preview_options=QHBoxLayout();layout.addLayout(preview_options)
        self.original=QCheckBox('Original'); self.original.toggled.connect(self.show_image); preview_options.addWidget(self.original)
        self.composition=QCheckBox('Composition');self.composition.setChecked(True);self.composition.toggled.connect(self.show_image);preview_options.addWidget(self.composition)
        self.preserve=QCheckBox('Preserve transparency'); self.preserve.setChecked(layer.provenance.get('glitchTemple',{}).get('preserveAlpha',True) if layer else True); self.preserve.toggled.connect(self.dirty); preview_options.addWidget(self.preserve)
        for widget in (self.original,self.composition,self.preserve):widget.setMinimumHeight(32)
        preview_options.addStretch()
        split=QSplitter(); layout.addWidget(split,1)
        self.scene=QGraphicsScene(); self.view=QGraphicsView(self.scene); self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.image=QGraphicsPixmapItem(); self.scene.addItem(self.image); split.addWidget(self.view)
        self.zoom=QComboBox();self.zoom.addItems(['Fit','100%','200%','400%','800%']);self.zoom.setMinimumHeight(32);self.zoom.setAccessibleName('Preview zoom');preview_options.addWidget(self.zoom);self.zoom.currentTextChanged.connect(self.set_zoom)
        self.fit_timer=QTimer(self);self.fit_timer.setSingleShot(True);self.fit_timer.timeout.connect(self.set_zoom);self.view.viewport().installEventFilter(self)
        controls=QWidget(); controls.setMinimumWidth(390); controls.setMaximumWidth(470); side=QVBoxLayout(controls); split.addWidget(controls); split.setSizes([740,420])
        addrow=QHBoxLayout(); self.library=QComboBox(); addrow.addWidget(self.library,1)
        add=self.button('Add effect',self.add_effect); addrow.addWidget(add); side.addLayout(addrow)
        self.chain=QListWidget(); self.chain.setMaximumHeight(150); self.chain.currentRowChanged.connect(self.effect_controls); self.chain.itemChanged.connect(self.toggle); side.addWidget(self.chain)
        row=QHBoxLayout(); side.addLayout(row)
        for label,fn in [('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Remove',self.remove_effect)]: row.addWidget(self.button(label,fn))
        self.tabs=QTabWidget(); side.addWidget(self.tabs,1)
        self.effect_page,self.effect_form=self.form_tab('Effect')
        self.where_page,self.where_form=self.form_tab('Where')
        self.color_page,self.color_form=self.form_tab('Color')
        self.settings_page,self.settings_form=self.form_tab('Recipe')
        row=QHBoxLayout(); side.addLayout(row)
        row.addWidget(self.button('New structure',lambda:self.vary('structure'))); row.addWidget(self.button('New colors',lambda:self.vary('colors')))
        row=QHBoxLayout(); side.addLayout(row)
        row.addWidget(self.button('Load recipe…',self.load_recipe)); row.addWidget(self.button('Save recipe…',self.save_recipe))
        self.status=QLabel('Starting Glitch Temple…'); self.status.setWordWrap(True); layout.addWidget(self.status)
        bottom=QHBoxLayout(); layout.addLayout(bottom)
        self.render_button=self.button('Render preview',self.render);self.render_button.setEnabled(False); bottom.addWidget(self.render_button)
        self.cancel_button=self.button('Stop',self.cancel); self.cancel_button.setEnabled(False); bottom.addWidget(self.cancel_button)
        bottom.addStretch(); self.apply_button=self.button('Apply treatment',self.apply); self.apply_button.setEnabled(False); bottom.addWidget(self.apply_button)
        self.gif_button=self.button('Export GIF…',lambda:self.export_loop('gif')); bottom.addWidget(self.gif_button)
        self.mp4_button=self.button('Export MP4…',lambda:self.export_loop('mp4')); bottom.addWidget(self.mp4_button)
        self.mp4_button.setToolTip('MP4 compresses colors and has no transparency. Use PNG for exact colors, or GIF for palette-limited animation.')
        self.gif_button.setEnabled(False);self.mp4_button.setEnabled(False)
        bottom.addWidget(self.button('Close',self.close))
        self.ws.dispatch('glitch',{'operation':'catalog'}); self.engine=self.ws.glitch; self.engine.changed.connect(self.refresh_job)
        self.ws.changed.connect(self.refresh_job)
        self.saved_recipe=copy.deepcopy(layer.params.get('glitchRecipe')) if layer and layer.effect_source is not None else None
        QTimer.singleShot(0,self.refresh_job)
        QTimer.singleShot(0,self.show_image)

    def button(self,label,fn):
        button=QPushButton(label); button.setMinimumSize(32,32); button.clicked.connect(fn); return button

    def form_tab(self,name):
        page=QWidget(); form=QFormLayout(page); form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        area=QScrollArea(); area.setWidgetResizable(True); area.setWidget(page); self.tabs.addTab(area,name); return page,form

    def clear(self,form):
        while form.rowCount():form.removeRow(0)

    def control(self,form,data,key,label=None,definition=None,choices=None,affects_render=True):
        value=data[key]; label=label or LABELS.get(key,re.sub(r'([a-z])([A-Z])',r'\1 \2',key).capitalize())
        definition=definition or {}; choices=choices or CHOICES.get(key)
        def changed(value):
            data[key]=value
            if affects_render:self.dirty()
            else:self.export_availability()
        if key.lower().endswith('color') and isinstance(value,int):
            widget=self.button(f'#{value:06x}',lambda:self.choose_color(widget,data,key))
            widget.setStyleSheet(f'border-left:18px solid #{value:06x};')
        elif isinstance(value,bool):
            widget=QCheckBox(); widget.setChecked(value); widget.toggled.connect(changed)
        elif choices:
            widget=QComboBox()
            for option in choices:
                if isinstance(option,tuple): text,stored=option
                else: text,stored=str(option).replace('-',' ').capitalize(),option
                widget.addItem(text,stored)
            widget.setCurrentIndex(max(0,widget.findData(value))); widget.currentIndexChanged.connect(lambda _:changed(widget.currentData()))
        elif isinstance(value,(int,float)):
            low,high,step=RANGES.get(key,(0,100,1))
            low,high,step=definition.get('min',low),definition.get('max',high),definition.get('step',step)
            widget=QDoubleSpinBox() if step<1 else QSpinBox()
            if step<1:widget.setDecimals(4 if step<.001 else 3 if step<.01 else 2)
            widget.setRange(low,high); widget.setSingleStep(step); widget.setValue(value)
            widget.valueChanged.connect(changed)
        else:
            widget=QLineEdit(''.join(value) if isinstance(value,list) else str(value))
            widget.editingFinished.connect(lambda:changed(list(widget.text()) if isinstance(value,list) else widget.text()))
        widget.setMinimumHeight(32); widget.setAccessibleName(label); widget.setToolTip(definition.get('description','')); form.addRow(label,widget); return widget

    def choose_color(self,widget,data,key):
        color=QColorDialog.getColor(QColor(f'#{data[key]:06x}'),self)
        if color.isValid():
            data[key]=int(color.name()[1:],16); widget.setText(color.name()); widget.setStyleSheet('border-left:18px solid '+color.name()+';'); self.dirty()

    def dirty(self,*_):
        if self.updating:return
        self.local_revision+=1; self.apply_button.setEnabled(False)
        self.status.setText('Settings changed. Render to see this treatment.')
        if hasattr(self,'engine'):self.export_availability()

    def export_availability(self):
        layer=next((l for l in self.document.layers if l.id==self.layer_id),None)
        loop=self.engine.jobs.get(self.loop_id,{})
        keys=('effects','palette','paletteSettings','colorMode','sourcePresence','seed','colorSeed','iteration','compositor')
        matches=bool(layer and layer.effect_source is not None and self.recipe and
                     all(self.recipe.get(k)==layer.params.get('glitchRecipe',{}).get(k) for k in keys))
        available=matches and loop.get('status') not in ('queued','running','encoding','stopping')
        for button in (self.gif_button,self.mp4_button):
            button.setEnabled(available);button.setToolTip('Export the applied treatment within the composition' if matches else 'Apply the current treatment before exporting a loop')
        if matches:self.mp4_button.setToolTip('MP4 compresses colors and has no transparency. Use PNG for exact colors, or GIF for palette-limited animation.')

    def populate(self):
        self.updating=True; index=self.chain.currentRow(); self.chain.clear()
        for effect in self.recipe['effects']:
            name=next(d['name'] for d in self.catalog['definitions'] if d['type']==effect['type'])
            item=QListWidgetItem(name); item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked if effect['enabled'] else Qt.CheckState.Unchecked); item.setSizeHint(item.sizeHint().expandedTo(QSize(32,32))); self.chain.addItem(item)
        self.chain.setCurrentRow(max(0,min(index,len(self.recipe['effects'])-1)))
        self.clear(self.color_form); self.control(self.color_form,self.recipe,'colorMode'); self.control(self.color_form,self.recipe,'sourcePresence')
        if self.document.pixel_art or self.recipe.get('compositor',{}).get('pixelFinish'):
            finish=self.recipe.setdefault('compositor',{}).setdefault('pixelFinish',{'paletteMode':'document' if self.document.pixel_art.get('palette') else 'effect','hardAlpha':True,'dither':False})
            palette_mode=self.control(self.color_form,finish,'paletteMode','Pixel colors',choices=[('Document palette','document'),('Effect colors','effect')])
            self.control(self.color_form,finish,'hardAlpha','Hard transparency edges')
            dither=self.control(self.color_form,finish,'dither','Dither to palette')
            dither.setEnabled(finish['paletteMode']=='document')
            palette_mode.currentIndexChanged.connect(lambda _:dither.setEnabled(finish['paletteMode']=='document'))
        for i in range(4):
            data={'color':self.recipe['palette'][i]}; button=self.button(f'#{data["color"]:06x}',lambda checked=False,i=i:self.palette_color(i)); self.color_form.addRow(f'Palette {i+1}',button)
        for key in self.recipe['paletteSettings']:
            choices=[(p['label'],p['value']) for p in self.catalog['paletteStructures']] if key=='structure' else None
            self.control(self.color_form,self.recipe['paletteSettings'],key,choices=choices)
        self.color_form.addRow(self.button('Build palette from settings',self.build_palette))
        self.clear(self.settings_form)
        for key in ('seed','colorSeed','iteration','loopFrames','loopFps'):
            self.control(self.settings_form,self.recipe,key,affects_render=key not in ('loopFrames','loopFps'))
        size_control=QSpinBox();size_control.setMinimumHeight(32)
        key='scale' if self.document.pixel_art else 'maxDimension'
        size_control.setRange(1 if self.document.pixel_art else 32,min(16,max(1,3840//max(self.document.width,self.document.height))) if self.document.pixel_art else 3840)
        size_control.setSuffix('×' if self.document.pixel_art else ' px');size_control.setValue(self.export_options[key])
        label='Pixel enlargement' if self.document.pixel_art else 'Fit within'
        size_control.setAccessibleName(label);self.settings_form.addRow(label,size_control)
        output_label=QLabel();self.settings_form.addRow('Output size',output_label)
        def output_size(value):
            from .glitch import export_dimensions
            self.export_options[key]=value
            try:output_label.setText(' × '.join(map(str,export_dimensions(self.document,self.export_options)))+' px')
            except ValueError as error:output_label.setText(str(error))
        size_control.valueChanged.connect(output_size);output_size(size_control.value())
        note=QLabel('Loops animate the applied layer within the complete composition. Pixel enlargement uses solid blocks with no smoothing.' if self.document.pixel_art else 'Loops animate the applied layer within the complete composition. Other layers remain in place.');note.setWordWrap(True);self.settings_form.addRow(note)
        self.updating=False; self.effect_controls()

    def effect_controls(self,*_):
        self.clear(self.effect_form); self.clear(self.where_form)
        index=self.chain.currentRow()
        if not self.recipe or not 0<=index<len(self.recipe['effects']):return
        effect=self.recipe['effects'][index]; definition=next(d for d in self.catalog['definitions'] if d['type']==effect['type'])
        description=QLabel(definition['description']);description.setWordWrap(True);self.effect_form.addRow(description)
        for parameter in definition['parameters']:
            choices=[(str(v),i) for i,v in enumerate(parameter['choices'])] if parameter.get('choices') else None
            self.control(self.effect_form,effect['parameters'],parameter['id'],parameter['label'],parameter,choices)
        for key in ('characterField','zhuyinField','tileField','wizprocess'):
            data=effect.get(key)
            if not data:continue
            for field in data:
                if field=='kind':continue
                options=None
                if field=='bank':
                    banks=self.catalog['asciiBanks' if key=='characterField' else 'zhuyinBanks']; options=[(b['label'],b['id']) for b in banks]
                widget=self.control(self.effect_form,data,field,choices=options)
                if field=='bank':widget.currentIndexChanged.connect(lambda _,data=data,banks=banks:self.bank_changed(data,banks))
        if effect.get('ultimateSort'):self.sort_controls(effect['ultimateSort'])
        for field in effect['where']:
            choices=[(m['label'],m['value']) for m in self.catalog['whereModes']] if field=='mode' else None
            self.control(self.where_form,effect['where'],field,choices=choices)

    def sort_controls(self,stack):
        selector=QComboBox()
        for i,row in enumerate(stack['recipes']):selector.addItem(f'{i+1}. {row["method"].title()} · {row["action"]}')
        self.effect_form.addRow('Recipe step',selector)
        panel=QWidget(); form=QFormLayout(panel); self.effect_form.addRow(panel)
        def show(index):
            self.clear(form)
            for key in stack['recipes'][index]:
                if key!='id':self.control(form,stack['recipes'][index],key)
        selector.currentIndexChanged.connect(show);show(0)
        row=QWidget(); buttons=QHBoxLayout(row);buttons.setContentsMargins(0,0,0,0)
        def mutate(kind):
            index=selector.currentIndex()
            if kind=='add':
                recipe=copy.deepcopy(self.catalog['sortRecipe']); recipe['id']=str(uuid.uuid4());stack['recipes'].insert(index+1,recipe)
            elif kind=='remove' and len(stack['recipes'])>1:stack['recipes'].pop(index)
            elif kind=='up' and index>0:stack['recipes'][index-1],stack['recipes'][index]=stack['recipes'][index],stack['recipes'][index-1]
            self.dirty();self.effect_controls()
        for label,kind in [('Add step','add'),('Remove step','remove'),('Move up','up')]:buttons.addWidget(self.button(label,lambda _,kind=kind:mutate(kind)))
        self.effect_form.addRow(row)

    def bank_changed(self,data,banks):
        data['glyphs']=copy.deepcopy(next(b['glyphs'] for b in banks if b['id']==data['bank']));self.dirty();QTimer.singleShot(0,self.effect_controls)

    def palette_color(self,index):
        color=QColorDialog.getColor(QColor(f'#{self.recipe["palette"][index]:06x}'),self)
        if color.isValid():self.recipe['palette'][index]=int(color.name()[1:],16);self.recipe['paletteSettings']['structure']='custom';self.dirty();self.populate()

    def add_effect(self):
        if not self.recipe:return
        effect=copy.deepcopy(self.catalog['templates'][self.library.currentData()]);effect['id']=str(uuid.uuid4())
        self.recipe['effects'].append(effect);self.dirty();self.populate();self.chain.setCurrentRow(len(self.recipe['effects'])-1)

    def remove_effect(self):
        index=self.chain.currentRow()
        if index>=0:self.recipe['effects'].pop(index);self.dirty();self.populate()

    def move(self,delta):
        index=self.chain.currentRow(); target=index+delta
        if 0<=target<len(self.recipe['effects']):
            effects=self.recipe['effects'];effects[index],effects[target]=effects[target],effects[index];self.dirty();self.populate();self.chain.setCurrentRow(target)

    def toggle(self,item):
        if self.updating:return
        self.recipe['effects'][self.chain.row(item)]['enabled']=item.checkState()==Qt.CheckState.Checked;self.dirty()

    def vary(self,kind):
        if not self.recipe:return
        revision=self.local_revision
        def done(message):
            if not isValid(self):return
            if message.get('error'):self.status.setText(message['error'])
            elif revision==self.local_revision:self.recipe=message['result'];self.dirty();self.populate()
        self.engine.vary(copy.deepcopy(self.recipe),kind,done)

    def build_palette(self):
        if self.recipe['paletteSettings']['structure']=='source':
            try:
                from . import pixels
                mode=self.source.currentData()
                layer=self.document.layer(self.layer_id) if mode in ('layer','treatment') else None
                source=layer.effect_source if mode=='treatment' else pixels.content(layer) if layer else self.document.render()
                palette=source.convert('RGB').quantize(colors=4,method=Image.Quantize.MEDIANCUT).getpalette()[:12]
                self.recipe['palette']=[(palette[i]<<16)|(palette[i+1]<<8)|palette[i+2] for i in range(0,12,3)]
                self.dirty();self.populate()
            except Exception as error:self.status.setText(str(error))
            return
        revision=self.local_revision
        def done(message):
            if not isValid(self):return
            if message.get('error'):self.status.setText(message['error'])
            elif revision==self.local_revision:self.recipe=message['result'];self.dirty();self.populate()
        self.engine.transform(copy.deepcopy(self.recipe),'palette',done)

    def render(self):
        try:
            self.loop_id=None
            layer=next((l for l in self.document.layers if l.id==self.layer_id),None)
            name=layer.name if layer and self.source.currentData()=='treatment' else (layer.name+' · Glitch Temple') if layer else 'Glitch Temple treatment'
            job=self.engine.submit(self.document,{'source':self.source.currentData(),'layerId':self.layer_id,'recipe':self.recipe,'name':name,'preserveAlpha':self.preserve.isChecked() and self.source.currentData()!='generated'})
            self.job_id=job['id'];self.render_revision=self.local_revision;self.apply_button.setEnabled(False);self.refresh_job()
        except Exception as error:self.status.setText(str(error))

    def refresh_job(self):
        if not self.catalog and self.engine.catalog:
            self.catalog=self.engine.catalog;self.recipe=self.saved_recipe or copy.deepcopy(self.catalog['defaults'])
            if not self.saved_recipe:self.recipe.update(effects=[],colorMode='source')
            for definition in self.catalog['definitions']:self.library.addItem(definition['name'],definition['type'])
            self.populate();self.status.setText('Saved treatment. Adjust settings and render to revise it, or export a loop.' if self.saved_recipe else 'Choose an effect, then render the treatment. Original artwork is retained.')
            self.render_button.setEnabled(True)
        loop=self.engine.jobs.get(self.loop_id,{})
        looping=loop.get('status') in ('queued','running','encoding','stopping')
        self.export_availability()
        if looping:
            self.status.setText(f'Exporting loop · {loop["framesRendered"]} / {loop["frames"]} frames'+(' · Encoding…' if loop['status']=='encoding' else ''))
            self.cancel_button.setEnabled(True);return
        if loop:
            self.status.setText('Saved '+loop['exportPath'] if loop['status']=='complete' else loop.get('error','Loop cancelled.'))
            self.cancel_button.setEnabled(False)
            return
        if not self.job_id:return
        job=self.engine.jobs[self.job_id];busy=job['status'] in ('queued','running','stopping')
        self.render_button.setEnabled(not busy);self.cancel_button.setEnabled(busy)
        current=self.local_revision==self.render_revision
        source_current=self.document.id in self.ws.documents and self.document.state_id==job['sourceStateId']
        self.apply_button.setEnabled(job['status']=='complete' and current and source_current and not job.get('applied'))
        if job['status']=='complete' and not loop:
            self.show_image();self.status.setText(f'{job["size"][0]} × {job["size"][1]} · '+('Treatment applied. Use Undo to restore the previous artwork.' if job.get('applied') else 'The artwork changed. Render again before applying.' if not source_current else 'Ready to apply.' if current else 'Previous render. Settings have changed.'))
        elif job['status']=='failed':self.status.setText(job.get('error','Rendering failed'))
        else:self.status.setText({'queued':'Waiting for the renderer…','running':'Rendering the full-resolution treatment…','stopping':'Stopping after the current render…','cancelled':'Render cancelled.'}.get(job['status'],job['status']))

    def show_image(self,*_):
        from .ui import pixmap
        if self.job_id:
            job=self.engine.jobs[self.job_id]
            if self.composition.isChecked():path=job.get('originalComposition') if self.original.isChecked() else job.get('compositionResult',job.get('result'))
            else:path=self.engine.root/job['id']/'source.png' if self.original.isChecked() else job.get('result')
            if not path:return
            with Image.open(path) as image:im=image.convert('RGBA')
        else:
            from . import pixels
            layer=next((l for l in self.document.layers if l.id==self.layer_id),None)
            if self.composition.isChecked():
                from .document import Document
                preview=Document();preview.restore(self.document.snapshot())
                if layer and layer.effect_source is not None and self.original.isChecked():preview.layer(layer.id).image=layer.effect_source
                im=preview.render()
            else:im=layer.effect_source if layer and layer.effect_source is not None and self.original.isChecked() else pixels.content(layer) if layer and layer.kind not in ('group','adjustment') else self.document.render()
        self.image.setPixmap(pixmap(im));self.image.setTransformationMode(Qt.TransformationMode.FastTransformation if self.document.pixel_art else Qt.TransformationMode.SmoothTransformation)
        self.scene.setSceneRect(self.image.boundingRect());self.set_zoom()

    def set_zoom(self,*_):
        self.view.resetTransform()
        fit=self.zoom.currentText()=='Fit'
        policy=Qt.ScrollBarPolicy.ScrollBarAlwaysOff if fit else Qt.ScrollBarPolicy.ScrollBarAsNeeded
        self.view.setHorizontalScrollBarPolicy(policy);self.view.setVerticalScrollBarPolicy(policy)
        if fit:self.view.fitInView(self.image.boundingRect(),Qt.AspectRatioMode.KeepAspectRatio)
        else:
            scale=float(self.zoom.currentText().strip('%'))/100;self.view.scale(scale,scale)

    def eventFilter(self,watched,event):
        if watched is self.view.viewport() and event.type()==QEvent.Type.Resize and self.zoom.currentText()=='Fit':self.fit_timer.start(0)
        return super().eventFilter(watched,event)

    def cancel(self):
        active=self.loop_id if self.loop_id and self.engine.jobs[self.loop_id]['status'] in ('queued','running','encoding','stopping') else self.job_id
        if active:self.engine.dispatch({'operation':'cancel','jobId':active})

    def export_loop(self,extension):
        path,_=QFileDialog.getSaveFileName(self,'Export Glitch Temple loop',self.ws.settings.file_dialog_path('export',self.document.title+'.'+extension,self.document.path),f'{extension.upper()} (*.{extension})')
        if not path:return
        if not Path(path).suffix:path+='.'+extension
        try:
            job=self.engine.dispatch({'operation':'export','documentId':self.document.id,'layerId':self.layer_id,'path':path,
                                      'frames':self.recipe['loopFrames'],'fps':self.recipe['loopFps'],**self.export_options})
            self.ws.settings.remember_file_dialog('export',path)
            self.loop_id=job['id'];self.refresh_job()
        except Exception as error:self.status.setText(str(error))

    def apply(self):
        try:
            result=self.engine.apply(self.job_id);self.layer_id=result['activeLayer']
            self.recipe=copy.deepcopy(self.engine.jobs[self.job_id]['recipe']);self.populate()
            if self.source.findData('treatment')<0:self.source.addItem('Original source','treatment')
            self.updating=True;self.source.setCurrentIndex(self.source.findData('treatment'));self.updating=False;self.refresh_job()
        except Exception as error:self.status.setText(str(error))

    def save_recipe(self):
        if not self.recipe:return
        path,_=QFileDialog.getSaveFileName(self,'Save Glitch Temple recipe','','Glitch recipe (*.json)')
        if path:Path(path).write_text(json.dumps(self.recipe,ensure_ascii=False,indent=2),encoding='utf-8')

    def load_recipe(self):
        path,_=QFileDialog.getOpenFileName(self,'Load Glitch Temple recipe','','Glitch recipe (*.json)')
        if not path:return
        try:
            recipe=json.loads(Path(path).read_text(encoding='utf-8'))
            if recipe.get('schemaVersion')!=1 or not isinstance(recipe.get('effects'),list):raise ValueError('Choose a Glitch Temple recipe')
            known={d['type'] for d in self.catalog['definitions']}
            if any(e.get('type') not in known for e in recipe['effects']):raise ValueError('This recipe uses an effect not available in this build')
            revision=self.local_revision
            def done(message):
                if not isValid(self):return
                if message.get('error'):self.status.setText(message['error'])
                elif revision==self.local_revision:self.recipe=message['result'];self.dirty();self.populate()
            self.engine.transform(recipe,'normalize',done)
        except Exception as error:self.status.setText(str(error))
