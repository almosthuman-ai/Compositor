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
    """Edit the canonical document with undo. Read first; pass expectedRevision to reject stale edits. Layer kinds: raster/text/shape/gradient/adjustment/group. update_layer takes layerId plus name, visible, locked, opacity 0–1, blend, x/y, sx/sy, angle, parent, clipping, params or effects. Brush points are [x,y,pressure?], with size/color/hardness/opacity. Selection kinds: rectangle/ellipse/polygon/wand/all/none/invert/expand/contract/feather/layer_alpha; mode replace/add/subtract/intersect. Regions use x/y/width/height. Filter kind: exposure/levels/curves/hue_saturation/invert/gaussian_blur/sharpen/noise/motion_blur/gradient_map/grayscale/auto_levels. Text params: text/font/size/color/spacing/align. Shape params: shape rectangle/ellipse/rounded/line, width/height/color/stroke/strokeWidth. Every successful operation returns the new revision and layers."""
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
def compositor_prepare_generation(kind:Literal['edit','patch']='edit',documentId:str|None=None,box:dict|None=None) -> dict:
    """Capture an immutable full composition or exact selected crop for native subscription image generation. Returns sourcePath to pass as a reference image to the image-generation tool. The embedded chat retains source revision and region so the returned candidate can be placed correctly."""
    return call('prepare_generation',locals())

@server.tool()
def compositor_generate(prompt:str,kind:Literal['generate','edit','patch']='generate',documentId:str|None=None,provider:str|None=None,model:str|None=None,box:dict|None=None,references:list|None=None,size:str='1024x1024',autoApply:bool=False) -> dict:
    """Start API-key image generation using configured provider. edit sends current composite; patch sends ONLY selected region plus explicit references. Returns durable job. Sources and native candidates are retained. Auto-apply rejects changed documents. Subscription-native generation is available through the embedded ChatGPT conversation when its account supports it."""
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

if __name__=='__main__': server.run()
