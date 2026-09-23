"""Human-facing provider choices; credentials stay outside public settings."""
from PySide6.QtWidgets import QWidget,QFormLayout,QLabel,QLineEdit
from .chrome import EditorComboBox as QComboBox
from .providers import PROVIDERS,MODELS


class ImageProviderSettings(QWidget):
    def __init__(self,settings,parent=None):
        super().__init__(parent); self.settings=settings; self.drafts={}; self.current=None
        form=QFormLayout(self); form.setContentsMargins(0,0,0,0)
        self.provider=QComboBox(); self.provider.setAccessibleName('Image provider')
        for value,label in PROVIDERS.items(): self.provider.addItem(label,value)
        form.addRow('Image provider',self.provider)
        self.model=QComboBox(); self.model.setEditable(True); self.model.setAccessibleName('Image model'); self.model.setMinimumWidth(300); form.addRow('Image model',self.model)
        self.key=QLineEdit(); self.key.setEchoMode(QLineEdit.EchoMode.Password); self.key.setAccessibleName('API key'); form.addRow('API key',self.key)
        self.key_status=QLabel(); form.addRow(self.key_status)
        self.resolution=QComboBox(); self.resolution.addItems(['1K','2K','4K']); self.resolution.setCurrentText(settings.values.get('imageSize','2K')); self.resolution.setAccessibleName('Gemini resolution'); self.resolution_label=QLabel('Gemini resolution'); form.addRow(self.resolution_label,self.resolution)
        self.ratio=QComboBox(); self.ratio.addItem('Match canvas',''); self.ratio.setAccessibleName('Gemini aspect ratio')
        for ratio in ('1:1','2:3','3:2','3:4','4:3','4:5','5:4','9:16','16:9','21:9'): self.ratio.addItem(ratio,ratio)
        self.ratio.setCurrentIndex(max(0,self.ratio.findData(settings.values.get('aspectRatio','')))); self.ratio_label=QLabel('Gemini aspect ratio'); form.addRow(self.ratio_label,self.ratio)
        self.endpoint=QLineEdit(); self.endpoint.setAccessibleName('API endpoint'); form.addRow('API endpoint',self.endpoint)
        self.provider.setCurrentIndex(max(0,self.provider.findData(settings.values['provider'])))
        self.provider.currentIndexChanged.connect(self.switch); self.model.currentTextChanged.connect(self.model_changed); self.switch()

    def model_id(self):
        text=self.model.currentText().strip(); index=self.model.findText(text)
        return self.model.itemData(index) if index>=0 else text

    def remember(self):
        if self.current: self.drafts[self.current]={'model':self.model_id(),'key':self.key.text().strip(),'endpoint':self.endpoint.text().strip()}

    def switch(self,*args):
        self.remember(); self.current=self.provider.currentData(); s=self.settings
        values=self.drafts.get(self.current,{'model':s.model_for(self.current),'key':'','endpoint':s.values[self.current+'_url']})
        self.model.blockSignals(True); self.model.clear()
        for label,value in MODELS[self.current]:self.model.addItem(label,value)
        index=self.model.findData(values['model'])
        if index>=0:self.model.setCurrentIndex(index)
        else:self.model.setEditText(values['model'])
        self.model.blockSignals(False)
        self.key.setText(values['key']); self.endpoint.setText(values['endpoint'])
        available=bool(s.key(self.current)); self.key.setPlaceholderText('Leave blank to keep the saved key' if available else 'Paste your API key')
        self.key_status.setText('API key available' if available else 'No API key saved')
        for widget in (self.ratio,self.ratio_label,self.resolution,self.resolution_label):widget.setVisible(self.current=='gemini')
        self.model_changed()

    def model_changed(self,*args):
        self.resolution.setEnabled(not self.model_id().startswith('gemini-2.5-'))

    def values(self):
        self.remember()
        if not self.model_id():raise ValueError('Choose an image model.')
        result={'provider':self.current,'model':self.model_id(),'imageSize':self.resolution.currentText(),'aspectRatio':self.ratio.currentData()}
        for provider,draft in self.drafts.items():result[provider+'_url']=draft['endpoint']
        return result

    def save_keys(self):
        self.remember()
        for provider,draft in self.drafts.items():
            if draft['key']:self.settings.set_key(provider,draft['key'])
