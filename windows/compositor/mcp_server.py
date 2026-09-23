"""Public stdio MCP interface. Every edit reaches the same open native editor."""
import base64, json, urllib.request, urllib.error
from typing import Literal
from mcp.server.mcpserver import MCPServer, Image
from .settings import Settings

server=MCPServer('Compositor')

def call(action,args=None):
    settings=Settings(); req=urllib.request.Request(f'http://127.0.0.1:{settings.values["port"]}/action',data=json.dumps({'action':action,'args':args or {}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+settings.token})
    try:
        with urllib.request.urlopen(req,timeout=190) as response: return json.load(response)
    except urllib.error.HTTPError as e: raise ValueError(json.load(e).get('error','Editor request failed')) from None
    except urllib.error.URLError: raise ValueError('Open Compositor before using its editor tools') from None

@server.tool()
def compositor_get_workspace() -> dict:
    """Read open documents, exact layers, revisions, current selection, jobs and provider readiness. No credentials are returned."""
    return call('state')

@server.tool()
def compositor_list_fonts() -> dict:
    """List installed font families and styles available to text layers. Use fontFamily, fontStyle and size in text params; no font file path is required."""
    return call('fonts')

@server.tool()
def compositor_new_document(width:int=1536,height:int=1024,title:str='Untitled',background:str='#ffffff') -> dict:
    """Create and show a new layered document. Existing documents remain open."""
    return call('new',locals())

@server.tool()
def compositor_open_document(path:str) -> dict:
    """Open a .compwin, OpenRaster, PSD, upstream Compositor package or ordinary image. Returns conversion notes when present."""
    return call('open',locals())

@server.tool()
def compositor_activate_document(documentId:str) -> dict:
    """Show the named open document in the human's editor."""
    return call('activate',locals())

@server.tool()
def compositor_edit(operation:Literal['add_layer','import_image','select_layer','update_layer','duplicate_layer','delete_layer','reorder_layer','rasterize','merge_down','flatten','selection','mask','brush','erase','clone','heal','blur_brush','fill','clear','content_fill','filter','copy_selection','cut_selection','crop','canvas_size','image_size','guides','rename','undo','redo'],args:dict,documentId:str|None=None,expectedRevision:int|None=None) -> dict:
    """Edit the canonical document with undo. Read first; pass expectedRevision to reject stale edits. Layer kinds: raster/text/shape/gradient/adjustment/group. update_layer takes layerId plus name, visible, locked, opacity 0–1, blend, x/y, sx/sy, angle, parent, clipping, params or effects. Brush points are [x,y,pressure?], with size/color/hardness/opacity. Selection kinds: rectangle/ellipse/polygon/wand/all/none/invert/expand/contract/feather/layer_alpha; mode replace/add/subtract/intersect. Regions use x/y/width/height. Filter kind: exposure/levels/curves/hue_saturation/invert/gaussian_blur/sharpen/noise/motion_blur/gradient_map/grayscale/auto_levels. Text params: text/fontFamily/fontStyle/size/color/spacing/align. compositor_list_fonts supplies available families and styles; legacy font paths remain supported. Shape params: shape rectangle/ellipse/rounded/line, width/height/color/stroke/strokeWidth. Every successful operation returns the new revision and layers."""
    return call('edit',locals())

@server.tool()
def compositor_view_image(documentId:str|None=None,region:dict|None=None,maxDimension:int|None=None) -> Image:
    """Inspect the exact rendered composition or original-coordinate region x/y/width/height. Default preserves pixel dimensions; optional maxDimension is an explicit overview thumbnail."""
    result=call('capture',locals()); return Image(data=base64.b64decode(result['data']),format='jpeg')

@server.tool()
def compositor_save_document(path:str,documentId:str|None=None) -> dict:
    """Save an atomic layered .compwin or .ora project. Originals are preserved. Returns exact path and bytes."""
    return call('save',locals())

@server.tool()
def compositor_export(path:str,documentId:str|None=None,quality:int=95) -> dict:
    """Export current composite to PNG/JPEG/WebP/TIFF/BMP without replacing imported originals."""
    return call('export',locals())

@server.tool()
def compositor_styles(operation:Literal['list','save']='list',args:dict|None=None) -> dict:
    """List reusable style profiles or save a custom style: name/prefix/suffix and optional references [{path,label}]. To update a custom style, pass its id. Built-in styles are customized as new copies. Project styles are snapshots changed through compositor_production."""
    return call('styles' if operation=='list' else 'save_style',args)

@server.tool()
def compositor_preview_generation(prompt:str,kind:Literal['generate','edit','patch']='generate',documentId:str|None=None,styleId:str|None=None,references:list|None=None) -> dict:
    """Inspect the exact assembled prompt, selected cast, style and ordered references without generating or charging. Project pages automatically use their own style and selected character references. Standalone documents accept styleId."""
    return call('preview_generation',{k:v for k,v in locals().items() if v is not None})

@server.tool()
def compositor_prepare_generation(kind:Literal['generate','edit','patch']='edit',documentId:str|None=None,box:dict|None=None,prompt:str='',styleId:str|None=None,purpose:Literal['image','character']='image',characterId:str|None=None) -> dict:
    """Prepare subscription-native image generation. Pass the user's prompt. Returns the assembled prompt and immutable inputs in provider order, including source composition/crop for edits, project style references and selected characters. Pass ALL inputs to the native image tool, using the returned prompt. purpose character plus characterId prepares a reference sheet for explicit acceptance via compositor_production. The embedded chat links results to source revision, region and creative context."""
    return call('prepare_generation',{k:v for k,v in locals().items() if v is not None})

@server.tool()
def compositor_generate(prompt:str,kind:Literal['generate','edit','patch']='generate',documentId:str|None=None,provider:str|None=None,model:str|None=None,box:dict|None=None,references:list|None=None,size:str='1024x1024',autoApply:bool=False,styleId:str|None=None) -> dict:
    """Start API-key image generation using configured provider. Project pages automatically include their style, direction and selected characters. Standalone documents accept styleId. edit sends current composite; patch sends ONLY selected region plus references. Returns durable job with assembled prompt and creative context. Sources and candidates are retained. Auto-apply rejects changed documents. Subscription-native generation is available through embedded ChatGPT when its account supports it."""
    return call('generate',{k:v for k,v in locals().items() if v is not None})

@server.tool()
def compositor_generation_job(jobId:str) -> dict:
    """Read saved source, candidate path, actual dimensions, provider error and application status."""
    return call('job',locals())

@server.tool()
def compositor_apply_generation(jobId:str,documentId:str|None=None) -> dict:
    """Apply a reviewed candidate as an editable layer only if its exact source document is unchanged."""
    return call('apply_generation',locals())

@server.tool()
def compositor_project_list() -> list:
    """List projects through the configured optional production connector."""
    return call('connector_projects')

@server.tool()
def compositor_project_pull(projectId:str,role:Literal['background','page']='background',page:int=1) -> dict:
    """Bring a selected project image into the editor, preserving source asset identity."""
    return call('connector_pull',locals())

@server.tool()
def compositor_project_push(projectId:str,role:Literal['background','page','reference']='background',page:int=1,documentId:str|None=None) -> dict:
    """Return the edited composition as a new project image through the configured connector."""
    return call('connector_push',locals())

@server.tool()
def compositor_project_action(action:str,args:dict) -> dict:
    """Operate optional production connector: create_lesson, update_lesson, generate, enhance_page, add_page, set_reference_role, set_view, select_page, select_background, set_history, export_comic, export_scene, export_reading. Connector owns its validation and project truth."""
    return call('connector_action',locals())

@server.tool()
def compositor_production(operation:Literal['list','new','get','select','update','add_page','update_page','reorder_page','remove_page','add_reference','remove_reference','save','open','export','generate','present','close_presentation','set_style','update_style','add_character','update_character','remove_character','generate_character','accept_character_reference'],args:dict) -> dict:
    """Use standalone artwork, comic and book projects, without a Studio service. new: title, kind artwork/comic/book, pageCount, width, height. Other actions use projectId and optional pageId. update: title/story/artDirection. update_page: title/text/prompt/splitY (optional comic panel split) and characterIds for the page cast. set_style: styleId (null clears); snapshots a library style and reference images. update_style: name/prefix/suffix on the project snapshot. add_character: name/description. update_character/remove_character: characterId. add_reference with characterId assigns an image to that character. generate_character: characterId and optional prompt creates a retained sheet candidate. accept_character_reference: characterId/jobId copies a reviewed sheet into the project. add_page can attach documentId or create blank. reorder_page takes index. add_reference: path/label/role character/style/composition. remove_reference: referenceId. save/open use a .compbook path; export uses a .html or .pdf path. generate combines project direction/story, page prompt and labeled references, with generationKind generate/edit/patch and optional provider/model/size/box. Results remain reviewable candidates. All pages use the same canonical editor documents and operations."""
    return call('production',locals())

if __name__=='__main__': server.run()
