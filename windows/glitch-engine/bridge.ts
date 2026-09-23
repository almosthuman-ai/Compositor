import * as studio from './studio';
import {fittedSource,cloneSurface,blendSource,applyEffect,targetSurface} from './effects';

export function catalog() {
  return {definitions:studio.effectDefinitions, defaults:studio.defaultRecipe(),
    templates:Object.fromEntries(studio.effectDefinitions.map(d=>[d.type,studio.createEffect(d.type,886)])),
    whereModes:studio.whereModes,asciiBanks:studio.asciiBanks,zhuyinBanks:studio.zhuyinBanks,
    paletteStructures:studio.paletteStructures,petsciiPalette:studio.petsciiPalette,
    sortRecipe:studio.defaultUltimateSortRecipe(886)};
}

export function normalize(value:any) {
  if(!value || value.schemaVersion!==1 || !Array.isArray(value.effects)) throw new Error('Choose a Glitch Temple recipe');
  if(value.effects.some((e:any)=>!e || !studio.effectDefinitions.some(d=>d.type===e.type) && e.type!=='wavelet-chamber')) throw new Error('This recipe uses an unavailable effect');
  const recipe=studio.normalizeRecipe(value);
  for(const key of ['renderWidth','renderHeight'] as const) if(value[key]!=null) recipe[key]=Math.max(1,Math.min(3840,Math.round(value[key])));
  recipe.renderSize=Math.max(recipe.renderWidth,recipe.renderHeight);
  for(const effect of recipe.effects) {
    const definition=studio.definitionFor(effect.type);
    for(const p of definition.parameters) {
      const number=Number(effect.parameters[p.id]);
      if(!Number.isFinite(number)) throw new Error('Invalid value for '+p.label);
      effect.parameters[p.id]=Math.max(p.min,Math.min(p.max,number));
    }
  }
  return recipe;
}

export function palette(value:any) { return studio.applyPaletteSettings(normalize(value),{}); }

export function vary(value:any,kind:string) {
  const recipe=normalize(value);
  if(kind==='structure') return studio.nextStructure(recipe);
  if(kind==='colors') return studio.nextColors(recipe);
  if(kind==='iteration') return studio.nextZhuyinIteration(recipe);
  throw new Error('Unknown variation');
}

export async function render(request:any) {
  const recipe=normalize(request.recipe);
  const width=request.width,height=request.height;
  recipe.renderWidth=width;recipe.renderHeight=height;recipe.renderSize=Math.max(width,height);
  const image:HTMLImageElement|null=request.source ? await new Promise((resolve,reject)=>{
    const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error('Could not read the source image'));im.src=request.source;
  }):null;
  await document.fonts.ready;
  const held={...recipe,seed:recipe.seed+recipe.iteration*104729};
  let surface=fittedSource(image,width,height,held);
  const original=cloneSurface(surface);
  const phase=request.phase ?? (recipe.iteration%recipe.loopFrames)/recipe.loopFrames*Math.PI*2;
  let sourceBlended=false;
  for(const effect of held.effects) {
    if(effect.enabled && ['ascii-field','zhuyin-weave','petscii-study'].includes(effect.type) && !sourceBlended && held.sourcePresence>0) {
      surface=blendSource(surface,original,held.sourcePresence);sourceBlended=true;
    }
    if(request.targetEffectId===effect.id) {surface=targetSurface(surface,effect);break;}
    surface=applyEffect(surface,effect,held,phase,Boolean(request.animated));
  }
  if(!request.targetEffectId && !sourceBlended) surface=blendSource(surface,original,held.sourcePresence);
  return {image:surface.toDataURL('image/png'),recipe,width,height};
}
