"""Reading copies preserve composed pages and typeset additional page prose."""
import base64, html, io


def export_reading(project, pages, target):
    """pages yields (page metadata, rendered PIL image) from the document owner."""
    if target.suffix.lower()=='.pdf':
        return export_pdf(project,pages,target)
    sections=[]
    for page,image in pages:
        data=io.BytesIO(); image.save(data,'PNG')
        title=html.escape(page['title'])
        heading='<h2>'+title+'</h2>' if project['kind']=='book' else ''
        prose=''.join('<p>'+html.escape(p)+'</p>' for p in page['text'].split('\n') if p.strip())
        sections.append('<section aria-label="'+html.escape(page['title'],quote=True)+'">'+heading+
            '<img alt="'+html.escape(page['title'],quote=True)+'" width="'+str(image.width)+'" height="'+str(image.height)+'" src="data:image/png;base64,'+
            base64.b64encode(data.getvalue()).decode()+'">'+('<div class="prose">'+prose+'</div>' if prose else '')+'</section>')
    title=html.escape(project['title'])
    target.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
        '<title>'+title+'</title><style>body{margin:0;background:#202024;color:#242424;font:20px/1.6 Georgia,serif}'+
        'header{max-width:960px;margin:32px auto;padding:0 24px;color:#eee}h1{font:600 24px/1.3 system-ui,sans-serif}'+
        'main{max-width:1024px;margin:auto}section{background:white;margin:0 0 32px;break-after:page}'+
        'img{display:block;width:100%;height:auto}h2{font:600 22px system-ui,sans-serif;margin:0;padding:24px 32px}'+
        '.prose{padding:16px 32px 24px}p{margin:0 0 .75em;white-space:pre-wrap}p:last-child{margin-bottom:0}'+
        '@media print{body{background:white}header{display:none}section{margin:0}main{max-width:none}}'+
        '</style></head><body><header><h1>'+title+'</h1></header><main>'+''.join(sections)+'</main></body></html>',encoding='utf-8')


def export_pdf(project,pages,target):
    from PySide6.QtCore import QMarginsF,QRectF,QSizeF
    from PySide6.QtGui import QFont,QImage,QPainter,QPageLayout,QPageSize,QPdfWriter,QTextDocument
    writer=QPdfWriter(str(target)); writer.setResolution(96)
    writer.setTitle(project['title']); writer.setCreator('Compositor')
    painter=QPainter()
    try:
        for index,(page,image) in enumerate(pages):
            width,height=image.size
            # One authored page remains one reading page, at its own aspect ratio.
            # Prose outside the canvas gets real, readable space below the artwork.
            padding=width*.035; prose=None; prose_height=0
            if page['text'].strip() or project['kind']=='book':
                prose=QTextDocument(); font=QFont('Georgia'); font.setPixelSize(max(12,round(width*.026)))
                prose.setDefaultFont(font); prose.setDocumentMargin(0)
                if project['kind']=='book':
                    prose.setHtml('<h2>'+html.escape(page['title'])+'</h2>'+''.join('<p>'+html.escape(p)+'</p>' for p in page['text'].split('\n') if p.strip()))
                else: prose.setPlainText(page['text'])
                prose.setTextWidth(width-2*padding)
                prose_height=prose.size().height()+2*padding
            total_height=height+prose_height
            size=QPageSize(QSizeF(width*.75,total_height*.75),QPageSize.Unit.Point,'',QPageSize.SizeMatchPolicy.ExactMatch)
            layout=QPageLayout(size,QPageLayout.Orientation.Portrait,QMarginsF(0,0,0,0),QPageLayout.Unit.Point)
            layout.setMode(QPageLayout.Mode.FullPageMode)
            if not writer.setPageLayout(layout): raise RuntimeError('Could not set the PDF page size')
            if index:
                if not writer.newPage(): raise RuntimeError('Could not add a PDF page')
            elif not painter.begin(writer): raise RuntimeError('Could not create the PDF')
            painter.save(); painter.scale(writer.width()/width,writer.height()/total_height)
            painter.fillRect(QRectF(0,0,width,total_height),'white')
            rgba=image.convert('RGBA'); raw=rgba.tobytes()
            raster=QImage(raw,width,height,width*4,QImage.Format.Format_RGBA8888)
            painter.drawImage(QRectF(0,0,width,height),raster)
            if prose:
                painter.translate(padding,height+padding); prose.drawContents(painter)
            painter.restore()
    finally:
        if painter.isActive(): painter.end()
    if not target.exists() or target.stat().st_size<100: raise RuntimeError('PDF export produced no document')
