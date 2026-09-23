import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { petsciiPalette, randomSource, type EffectInstance, type StudioLayer, type StudioRecipe, type UltimateSortRecipe, type Wizprocess } from "./studio";

type LivePreviewProps = { recipe: StudioRecipe; sourceDataUrl?: string; layerDataUrls?: Record<string, string>; showOriginal?: boolean; targetPreviewEffectId?: string; animate?: boolean };
export type LivePreviewHandle = { capture: () => { dataUrl: string; width: number; height: number } | null };

const packedCss = (packed: number, alpha = 1) => `rgba(${(packed >> 16) & 255},${(packed >> 8) & 255},${packed & 255},${alpha})`;
const param = (effect: EffectInstance, id: string, fallback: number) => effect.parameters[id] ?? fallback;

function fittedSource(image: HTMLImageElement | null, width: number, height: number, recipe: StudioRecipe) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d", { alpha: false })!;
  context.fillStyle = packedCss(recipe.palette[3]);
  context.fillRect(0, 0, width, height);
  if (image) {
    const scale = recipe.sourceFit === "contain"
      ? Math.min(width / image.naturalWidth, height / image.naturalHeight)
      : Math.max(width / image.naturalWidth, height / image.naturalHeight);
    const drawWidth = image.naturalWidth * scale;
    const drawHeight = image.naturalHeight * scale;
    context.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
  } else {
    const random = randomSource(recipe.seed);
    const gradient = context.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, packedCss(recipe.palette[3]));
    gradient.addColorStop(0.36, packedCss(recipe.palette[0]));
    gradient.addColorStop(0.7, packedCss(recipe.palette[1]));
    gradient.addColorStop(1, packedCss(recipe.palette[2]));
    context.fillStyle = gradient;
    context.fillRect(0, 0, width, height);
    context.globalCompositeOperation = "difference";
    for (let i = 0; i < 52; i += 1) {
      context.fillStyle = packedCss(recipe.palette[i % 3], 0.06 + random() * 0.24);
      context.fillRect((random() - 0.12) * width, random() * height, width * (0.03 + random() * 0.75), 1 + random() * height * 0.035);
    }
    context.globalCompositeOperation = "source-over";
  }
  return canvas;
}

function newSurface(width: number, height: number) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

function cloneSurface(input: HTMLCanvasElement) {
  const output = newSurface(input.width, input.height);
  output.getContext("2d")!.drawImage(input, 0, 0);
  return output;
}

function resolutionQuilt(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe) {
  const output = cloneSurface(input);
  const context = output.getContext("2d")!;
  const minChunk = Math.max(4, param(effect, "minChunk", 18));
  const maxChunk = Math.max(minChunk, param(effect, "maxChunk", 180));
  const drop = param(effect, "resolutionDrop", 0.64);
  const softness = param(effect, "softness", 0.32);
  const displacement = param(effect, "displacement", 0.18);
  const vacancy = param(effect, "vacancy", 0.08);
  const random = randomSource(recipe.seed + 19013);
  for (let y = 0; y < input.height;) {
    const rowHeight = Math.min(input.height - y, minChunk + random() * (maxChunk - minChunk));
    for (let x = 0; x < input.width;) {
      const chunkWidth = Math.min(input.width - x, minChunk + random() * (maxChunk - minChunk));
      if (random() < vacancy) {
        context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "rgba(0,0,0,.92)";
        context.fillRect(x, y, chunkWidth, rowHeight);
      } else {
        const level = Math.max(1, 2 ** Math.floor(random() * (1 + drop * 5)));
        const tiny = newSurface(Math.max(1, Math.round(chunkWidth / level)), Math.max(1, Math.round(rowHeight / level)));
        tiny.getContext("2d")!.drawImage(input, x, y, chunkWidth, rowHeight, 0, 0, tiny.width, tiny.height);
        context.imageSmoothingEnabled = softness > random();
        const travel = Math.min(input.width, input.height) * displacement;
        const dx = (random() * 2 - 1) * travel;
        const dy = (random() * 2 - 1) * travel;
        context.drawImage(tiny, x + dx, y + dy, chunkWidth, rowHeight);
      }
      x += chunkWidth;
    }
    y += rowHeight;
  }
  context.imageSmoothingEnabled = true;
  return output;
}

function shardField(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe) {
  const output = cloneSurface(input);
  const context = output.getContext("2d")!;
  const pieces = Math.round(param(effect, "pieces", 34));
  const minSpan = param(effect, "minSpan", 0.04);
  const maxSpan = Math.max(minSpan, param(effect, "maxSpan", 0.28));
  const travel = param(effect, "travel", 0.24);
  const rotation = param(effect, "rotation", 0.12);
  const repetition = param(effect, "repetition", 0.22);
  const absence = param(effect, "absence", 0.12);
  const random = randomSource(recipe.seed + 29027);
  for (let index = 0; index < pieces; index += 1) {
    const width = input.width * (minSpan + random() * (maxSpan - minSpan));
    const height = input.height * (minSpan + random() * (maxSpan - minSpan));
    const sx = random() * Math.max(1, input.width - width);
    const sy = random() * Math.max(1, input.height - height);
    if (random() < absence) {
      context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "rgba(0,0,0,.95)";
      context.fillRect(sx, sy, width, height);
      continue;
    }
    const copies = random() < repetition ? 2 + Math.floor(random() * 3) : 1;
    for (let copy = 0; copy < copies; copy += 1) {
      const dx = (random() * 2 - 1) * input.width * travel;
      const dy = (random() * 2 - 1) * input.height * travel;
      const angle = (random() * 2 - 1) * Math.PI * rotation;
      context.save();
      context.translate(sx + dx + width / 2, sy + dy + height / 2);
      context.rotate(angle);
      context.drawImage(input, sx, sy, width, height, -width / 2, -height / 2, width, height);
      context.restore();
    }
  }
  return output;
}

function cutRepeat(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe) {
  const output = cloneSurface(input);
  const context = output.getContext("2d")!;
  const selector = Math.round(param(effect, "selector", 3));
  const cuts = Math.round(param(effect, "cuts", 26));
  const span = param(effect, "span", 0.12);
  const stretch = param(effect, "stretch", 0.38);
  const repetitions = Math.round(param(effect, "repetition", 4));
  const drift = param(effect, "drift", 0.16);
  const absence = param(effect, "absence", 0.14);
  const random = randomSource(recipe.seed + 39041);
  const sample = input.getContext("2d", { willReadFrequently: true })!;
  for (let cut = 0; cut < cuts; cut += 1) {
    const vertical = random() > 0.5;
    const width = vertical ? Math.max(2, input.width * span * (0.3 + random())) : input.width;
    const height = vertical ? input.height : Math.max(2, input.height * span * (0.3 + random()));
    const sx = random() * Math.max(1, input.width - width);
    const sy = random() * Math.max(1, input.height - height);
    const pixel = sample.getImageData(Math.floor(sx + width / 2), Math.floor(sy + height / 2), 1, 1).data;
    const light = (pixel[0] + pixel[1] + pixel[2]) / 765;
    const eligible = selector === 3 || (selector === 0 && light > 0.58) || (selector === 1 && light < 0.42) || (selector === 2 && Math.abs(pixel[0] - pixel[2]) + Math.abs(pixel[1] - pixel[2]) > 72);
    if (!eligible) continue;
    if (random() < absence) {
      context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "rgba(0,0,0,.94)";
      context.fillRect(sx, sy, width, height);
      continue;
    }
    const stretchFactor = 1 + (random() * 2 - 0.5) * stretch * 3;
    for (let repeat = 0; repeat < repetitions; repeat += 1) {
      const dx = vertical ? repeat * input.width * drift / Math.max(1, repetitions) : 0;
      const dy = vertical ? 0 : repeat * input.height * drift / Math.max(1, repetitions);
      context.globalAlpha = 0.42 + 0.58 * (1 - repeat / Math.max(1, repetitions));
      context.drawImage(input, sx, sy, width, height, sx + dx, sy + dy, vertical ? width * stretchFactor : width, vertical ? height : height * stretchFactor);
    }
  }
  context.globalAlpha = 1;
  return output;
}

function maskedLayer(image: HTMLImageElement, layer: StudioLayer, width: number, height: number) {
  const canvas = newSurface(width, height);
  const context = canvas.getContext("2d", { willReadFrequently: true })!;
  const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight);
  const drawWidth = image.naturalWidth * scale, drawHeight = image.naturalHeight * scale;
  context.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
  if (layer.maskMode === "whole") return canvas;
  const mask = newSurface(width, height);
  const maskContext = mask.getContext("2d")!;
  const size = Math.max(2, layer.maskScale);
  maskContext.fillStyle = "white";
  if (layer.maskMode === "checker") {
    for (let y = 0; y < height; y += size) for (let x = 0; x < width; x += size) if ((Math.floor(x / size) + Math.floor(y / size)) % 2 === 0) maskContext.fillRect(x, y, size, size);
  } else if (layer.maskMode === "stripes") {
    for (let x = 0; x < width; x += size * 2) maskContext.fillRect(x, 0, size, height);
  } else if (layer.maskMode === "blocks") {
    const random = randomSource(layer.seed);
    for (let y = 0; y < height; y += size) for (let x = 0; x < width; x += size) if (random() > 0.48) maskContext.fillRect(x, y, size, size);
  } else {
    const pixels = context.getImageData(0, 0, width, height);
    const alpha = maskContext.createImageData(width, height);
    for (let offset = 0; offset < pixels.data.length; offset += 4) {
      const light = (pixels.data[offset] + pixels.data[offset + 1] + pixels.data[offset + 2]) / 765;
      const prior = offset >= 4 ? (pixels.data[offset - 4] + pixels.data[offset - 3] + pixels.data[offset - 2]) / 765 : light;
      const visible = layer.maskMode === "light" ? light > 0.56 : layer.maskMode === "dark" ? light < 0.44 : Math.abs(light - prior) > 0.1;
      alpha.data[offset] = alpha.data[offset + 1] = alpha.data[offset + 2] = 255;
      alpha.data[offset + 3] = visible ? 255 : 0;
    }
    maskContext.putImageData(alpha, 0, 0);
  }
  context.globalCompositeOperation = "destination-in";
  context.drawImage(mask, 0, 0);
  context.globalCompositeOperation = "source-over";
  return canvas;
}

function hardMix(base: HTMLCanvasElement, layer: HTMLCanvasElement, opacity: number) {
  const output = cloneSurface(base);
  const context = output.getContext("2d", { willReadFrequently: true })!;
  const basePixels = context.getImageData(0, 0, output.width, output.height);
  const layerPixels = layer.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, output.width, output.height);
  for (let offset = 0; offset < basePixels.data.length; offset += 4) {
    const alpha = layerPixels.data[offset + 3] / 255 * opacity;
    if (!alpha) continue;
    for (let channel = 0; channel < 3; channel += 1) {
      const mixed = basePixels.data[offset + channel] + 2 * layerPixels.data[offset + channel] >= 383 ? 255 : 0;
      basePixels.data[offset + channel] = Math.round(basePixels.data[offset + channel] * (1 - alpha) + mixed * alpha);
    }
  }
  context.putImageData(basePixels, 0, 0);
  return output;
}

function compositeLayers(base: HTMLCanvasElement, recipe: StudioRecipe, images: Record<string, HTMLImageElement>) {
  let output = cloneSurface(base);
  for (const layer of recipe.layers) {
    const image = images[layer.id];
    if (!layer.enabled || !image) continue;
    const prepared = maskedLayer(image, layer, output.width, output.height);
    if (layer.blendMode === "hard-mix") {
      output = hardMix(output, prepared, layer.opacity);
      continue;
    }
    const context = output.getContext("2d")!;
    context.save();
    context.globalAlpha = layer.opacity;
    context.globalCompositeOperation = ({
      normal: "source-over", difference: "difference", overlay: "overlay", screen: "screen",
      multiply: "multiply", lighten: "lighten", darken: "darken",
    } as Record<string, GlobalCompositeOperation>)[layer.blendMode] ?? "source-over";
    context.drawImage(prepared, 0, 0);
    context.restore();
  }
  return output;
}

function blendSource(processed: HTMLCanvasElement, source: HTMLCanvasElement, presence: number) {
  if (presence <= 0) return processed;
  const output = cloneSurface(processed);
  const context = output.getContext("2d")!;
  context.globalAlpha = Math.max(0, Math.min(1, presence));
  context.drawImage(source, 0, 0);
  context.globalAlpha = 1;
  return output;
}

function bandRupture(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const random = randomSource(recipe.seed + 1103);
  const rupture = param(effect, "rupture", 0.48);
  const count = Math.round(param(effect, "bands", 72));
  const scar = param(effect, "scar", 0.24);
  const memory = param(effect, "memory", 0.72);
  const height = input.height / count;
  context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "#000";
  context.fillRect(0, 0, input.width, input.height);
  context.globalAlpha = recipe.colorMode === "source" ? 1 : 0.18 + memory * 0.82;
  context.drawImage(input, 0, 0);
  context.globalAlpha = 1;
  for (let band = 0; band < count; band += 1) {
    const y = Math.floor(band * height);
    const h = Math.ceil(height + 1);
    const slip = (random() * 2 - 1) * input.width * rupture + Math.sin(band * 0.31 + phase) * input.width * rupture * 0.07;
    context.globalAlpha = 0.35 + memory * 0.65;
    context.drawImage(input, 0, y, input.width, h, slip, y, input.width, h);
    if (random() < scar) {
      context.globalAlpha = 0.45 + random() * 0.5;
      const scarX = random() * input.width;
      const scarWidth = 2 + random() * input.width * (0.04 + rupture * 0.24);
      const scarHeight = h * (0.4 + random() * 2.6);
      if (recipe.colorMode === "palette") {
        context.fillStyle = packedCss(random() < 0.68 ? recipe.palette[3] : recipe.palette[2]);
        context.fillRect(scarX, y, scarWidth, scarHeight);
      } else {
        const sampleX = random() * Math.max(1, input.width - scarWidth);
        const sampleY = random() * Math.max(1, input.height - scarHeight);
        context.drawImage(input, sampleX, sampleY, scarWidth, scarHeight, scarX, y, scarWidth, scarHeight);
      }
    }
  }
  context.globalAlpha = 1;
  return output;
}

function colorKey(data: Uint8ClampedArray, offset: number, channel: number) {
  const r = data[offset], g = data[offset + 1], b = data[offset + 2];
  if (channel < 3) return data[offset + channel];
  const max = Math.max(r, g, b), min = Math.min(r, g, b), delta = max - min;
  if (channel === 4) return max === 0 ? 0 : delta / max * 255;
  if (channel === 5) return max;
  if (delta === 0) return 0;
  const hue = max === r ? ((g - b) / delta) % 6 : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
  return ((hue * 42.5) + 255) % 255;
}

function wrongSort(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  context.drawImage(input, 0, 0);
  const image = context.getImageData(0, 0, input.width, input.height);
  const source = new Uint8ClampedArray(image.data);
  const random = randomSource(recipe.seed + 2207);
  const amount = param(effect, "amount", 0.42);
  const threshold = param(effect, "threshold", 0.32) * 255;
  const chunk = Math.round(param(effect, "chunk", 54));
  const direction = Math.round(param(effect, "direction", 0));
  const channel = Math.round(param(effect, "channel", 5));
  const vertical = direction >= 2;
  const reverse = direction === 1 || direction === 3;
  const lines = vertical ? input.width : input.height;
  const length = vertical ? input.height : input.width;
  const stride = Math.max(1, Math.round(1 + (1 - amount) * 7));
  for (let line = 0; line < lines; line += stride) {
    if (random() > amount) continue;
    for (let start = 0; start < length; start += chunk) {
      if (random() > amount * 1.3) continue;
      const end = Math.min(length, start + Math.max(4, Math.round(chunk * (0.45 + random()))));
      const pixels: { rgba: number[]; key: number }[] = [];
      for (let axis = start; axis < end; axis += 1) {
        const x = vertical ? line : axis;
        const y = vertical ? axis : line;
        const offset = (y * input.width + x) * 4;
        const key = colorKey(source, offset, channel);
        if (key >= threshold) pixels.push({ rgba: [source[offset], source[offset + 1], source[offset + 2], source[offset + 3]], key });
      }
      pixels.sort((a, b) => reverse ? b.key - a.key : a.key - b.key);
      let cursor = 0;
      for (let axis = start; axis < end && cursor < pixels.length; axis += 1) {
        const x = vertical ? line : axis;
        const y = vertical ? axis : line;
        const offset = (y * input.width + x) * 4;
        if (colorKey(source, offset, channel) < threshold) continue;
        image.data.set(pixels[cursor++].rgba, offset);
      }
    }
  }
  context.putImageData(image, 0, 0);
  return output;
}

function medianFilter(input: HTMLCanvasElement, effect: EffectInstance) {
  const width = input.width, height = input.height;
  if (width < 3 || height < 3) return cloneSurface(input);
  const position = Math.max(0, Math.min(8, Math.round(param(effect, "position", 3))));
  const channel = Math.max(0, Math.min(11, Math.round(param(effect, "channel", 11))));
  const iterations = Math.max(1, Math.min(24, Math.round(param(effect, "iterations", 6))));
  const original = input.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, width, height);
  let source = new Uint8ClampedArray(original.data);
  let target = new Uint8ClampedArray(source);
  const ranked = new Int32Array(9);
  const colors = new Uint32Array(9);

  const packedRank = (offset: number) => {
    const red = source[offset], green = source[offset + 1], blue = source[offset + 2];
    const hsb = channel % 6 >= 3 ? rgbToHsb255(red, green, blue) : null;
    const baseChannel = channel % 6;
    let value = baseChannel === 0 ? red : baseChannel === 1 ? green : baseChannel === 2 ? blue : hsb![baseChannel - 3];
    if (channel >= 6) value = 255 - value;
    const color = (red << 16) | (green << 8) | blue;
    return { packed: (value << 24) | color, color };
  };

  for (let pass = 0; pass < iterations; pass += 1) {
    target.set(source);
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        let cursor = 0;
        for (let oy = -1; oy <= 1; oy += 1) for (let ox = -1; ox <= 1; ox += 1) {
          const sample = packedRank(((y + oy) * width + x + ox) * 4);
          ranked[cursor] = sample.packed;
          colors[cursor] = sample.color;
          cursor += 1;
        }
        for (let index = 1; index < 9; index += 1) {
          const heldRank = ranked[index], heldColor = colors[index];
          let insert = index - 1;
          while (insert >= 0 && ranked[insert] > heldRank) {
            ranked[insert + 1] = ranked[insert];
            colors[insert + 1] = colors[insert];
            insert -= 1;
          }
          ranked[insert + 1] = heldRank;
          colors[insert + 1] = heldColor;
        }
        const chosen = colors[position], offset = (y * width + x) * 4;
        target[offset] = chosen >> 16 & 255;
        target[offset + 1] = chosen >> 8 & 255;
        target[offset + 2] = chosen & 255;
        target[offset + 3] = source[offset + 3];
      }
    }
    [source, target] = [target, source];
  }

  const output = newSurface(width, height);
  const result = output.getContext("2d")!.createImageData(width, height);
  result.data.set(source);
  output.getContext("2d")!.putImageData(result, 0, 0);
  const blendMode = Math.max(0, Math.min(6, Math.round(param(effect, "blendMode", 0))));
  if (blendMode > 0) {
    const context = output.getContext("2d")!;
    context.globalCompositeOperation = (["source-over", "overlay", "hard-light", "screen", "multiply", "lighter", "difference"] as GlobalCompositeOperation[])[blendMode];
    context.drawImage(input, 0, 0);
    context.globalCompositeOperation = "source-over";
  }
  return output;
}

type MotionPixel = { rgba: [number, number, number, number]; key: number };

function motionHash(seed: number, line: number, start: number, salt: number) {
  let value = (seed ^ Math.imul(line + salt, 374761393) ^ Math.imul(start - salt, 668265263)) | 0;
  value = Math.imul(value ^ (value >>> 13), 1274126177);
  return ((value ^ (value >>> 16)) & 0x7fffffff) / 2147483647;
}

function orderMotionFragment(pixels: MotionPixel[], method: number, progress: number, reverse: boolean, seed: number, line: number, start: number) {
  const orderedBefore = (a: MotionPixel, b: MotionPixel) => reverse ? a.key >= b.key : a.key <= b.key;
  const compare = (a: MotionPixel, b: MotionPixel) => reverse ? b.key - a.key : a.key - b.key;
  const count = pixels.length;
  if (count < 2 || progress <= 0) return;
  if (method === 0) {
    const passes = Math.round(progress * Math.min(count - 1, 32));
    for (let pass = 0; pass < passes; pass += 1) {
      for (let index = 1; index < count - pass; index += 1) {
        if (!orderedBefore(pixels[index - 1], pixels[index])) [pixels[index - 1], pixels[index]] = [pixels[index], pixels[index - 1]];
      }
    }
  } else if (method === 1) {
    const frontier = 1 + Math.round(progress * Math.min(count - 1, 72));
    for (let index = 1; index < frontier; index += 1) {
      const held = pixels[index];
      let cursor = index;
      while (cursor > 0 && !orderedBefore(pixels[cursor - 1], held)) { pixels[cursor] = pixels[cursor - 1]; cursor -= 1; }
      pixels[cursor] = held;
    }
  } else if (method === 2) {
    const positions = Math.round(progress * Math.min(count - 1, 40));
    for (let position = 0; position < positions; position += 1) {
      let chosen = position;
      for (let index = position + 1; index < count; index += 1) if (!orderedBefore(pixels[chosen], pixels[index])) chosen = index;
      if (chosen !== position) [pixels[position], pixels[chosen]] = [pixels[chosen], pixels[position]];
    }
  } else if (method === 3) {
    const levels = Math.max(1, Math.ceil(Math.log2(count)));
    const blockSize = Math.min(count, 2 ** Math.ceil(progress * levels));
    for (let block = 0; block < count; block += blockSize) {
      const sorted = pixels.slice(block, Math.min(count, block + blockSize)).sort(compare);
      for (let index = 0; index < sorted.length; index += 1) pixels[block + index] = sorted[index];
    }
  } else if (method === 4) {
    const swaps = Math.round(progress * (count - 1));
    for (let index = 1; index <= swaps; index += 1) {
      const target = Math.min(count - 1, index + Math.floor(motionHash(seed, line, start, index * 17) * (count - index)));
      [pixels[index - 1], pixels[target]] = [pixels[target], pixels[index - 1]];
    }
  } else {
    const offset = Math.round(progress * (count - 1));
    if (offset > 0) pixels.push(...pixels.splice(0, offset));
  }
}

function sortingMotion(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const output = cloneSurface(input);
  const context = output.getContext("2d")!;
  const image = context.getImageData(0, 0, input.width, input.height);
  const source = new Uint8ClampedArray(image.data);
  const method = Math.round(param(effect, "method", 0));
  const motion = 0.5 + 0.5 * Math.cos(phase);
  const progress = Math.max(0, Math.min(1, param(effect, "maximumOrder", 0.72) * motion));
  if (progress <= 0.000001) return output;
  const span = Math.max(8, Math.round(param(effect, "span", 72)));
  const channel = Math.round(param(effect, "channel", 5));
  const direction = Math.round(param(effect, "direction", 0));
  const reverse = param(effect, "reverse", 0) >= 0.5;
  const vertical = direction >= 2;
  const reverseTravel = direction === 1 || direction === 3;
  const lines = vertical ? input.width : input.height;
  const length = vertical ? input.height : input.width;
  const seed = recipe.seed + effect.where.seed + 4201;
  for (let line = 0; line < lines; line += 1) {
    for (let start = 0; start < length; start += span) {
      const end = Math.min(length, start + span);
      const pixels: MotionPixel[] = [];
      for (let axis = start; axis < end; axis += 1) {
        const x = vertical ? line : axis, y = vertical ? axis : line;
        const offset = (y * input.width + x) * 4;
        pixels.push({ rgba: [source[offset], source[offset + 1], source[offset + 2], source[offset + 3]], key: colorKey(source, offset, channel) });
      }
      orderMotionFragment(pixels, method, progress, reverse, seed, line, start);
      for (let axis = start; axis < end; axis += 1) {
        const x = vertical ? line : axis, y = vertical ? axis : line;
        const offset = (y * input.width + x) * 4;
        const index = reverseTravel ? pixels.length - 1 - (axis - start) : axis - start;
        image.data.set(pixels[index].rgba, offset);
      }
    }
  }
  context.putImageData(image, 0, 0);
  return output;
}

const ultimateMethods: UltimateSortRecipe["method"][] = ["bubble", "insertion", "selection", "merge", "permute", "roll"];
const ultimateSignals: UltimateSortRecipe["signal"][] = ["red", "green", "blue", "hue", "saturation", "brightness"];

function ultimateTerritoryMask(data: Uint8ClampedArray, width: number, height: number, recipe: UltimateSortRecipe) {
  const mask = new Uint8Array(width * height);
  const hueCenters: Partial<Record<UltimateSortRecipe["territory"], number>> = {
    red: 0, orange: 28, yellow: 58, green: 120, cyan: 185, blue: 235, pink: 325,
  };
  const brightnessAt = (x: number, y: number) => {
    const at = (Math.max(0, Math.min(height - 1, y)) * width + Math.max(0, Math.min(width - 1, x))) * 4;
    return (data[at] + data[at + 1] + data[at + 2]) / 3;
  };
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const index = y * width + x;
    const offset = index * 4;
    const light = brightnessAt(x, y);
    if (recipe.territory === "whole") mask[index] = 1;
    else if (recipe.territory === "light") mask[index] = light >= Math.min(255, recipe.gate) ? 1 : 0;
    else if (recipe.territory === "dark") mask[index] = light <= Math.min(255, recipe.gate) ? 1 : 0;
    else if (recipe.territory === "edges") {
      const gx = -brightnessAt(x - 1, y - 1) - 2 * brightnessAt(x - 1, y) - brightnessAt(x - 1, y + 1)
        + brightnessAt(x + 1, y - 1) + 2 * brightnessAt(x + 1, y) + brightnessAt(x + 1, y + 1);
      const gy = -brightnessAt(x - 1, y - 1) - 2 * brightnessAt(x, y - 1) - brightnessAt(x + 1, y - 1)
        + brightnessAt(x - 1, y + 1) + 2 * brightnessAt(x, y + 1) + brightnessAt(x + 1, y + 1);
      mask[index] = Math.hypot(gx, gy) >= recipe.gate ? 1 : 0;
    } else {
      const signal = hueAndSaturation(data[offset], data[offset + 1], data[offset + 2]);
      const center = hueCenters[recipe.territory] ?? 0;
      const distance = Math.abs(((signal.hue - center + 540) % 360) - 180);
      mask[index] = signal.saturation >= 0.12 && distance <= 28 ? 1 : 0;
    }
  }
  return mask;
}

function applyUltimateResolution(
  incoming: Uint8ClampedArray,
  sorted: Uint8ClampedArray,
  mask: Uint8Array,
  width: number,
  height: number,
  recipe: UltimateSortRecipe,
) {
  if (recipe.resolution === "pixel" || recipe.maxBlock <= 1) return sorted;
  const resolved = new Uint8ClampedArray(sorted);
  const grid = Math.max(2, recipe.maxBlock);
  for (let cellY = 0; cellY < height; cellY += grid) for (let cellX = 0; cellX < width; cellX += grid) {
    const x1 = Math.min(width, cellX + grid), y1 = Math.min(height, cellY + grid);
    let difference = 0, selected = 0, sampleX = -1, sampleY = -1;
    for (let y = cellY; y < y1; y += 1) for (let x = cellX; x < x1; x += 1) {
      const pixel = y * width + x;
      if (!mask[pixel]) continue;
      const offset = pixel * 4;
      difference += Math.abs(sorted[offset] - incoming[offset]) + Math.abs(sorted[offset + 1] - incoming[offset + 1]) + Math.abs(sorted[offset + 2] - incoming[offset + 2]);
      selected += 1;
      if (sampleX < 0) { sampleX = x; sampleY = y; }
    }
    if (!selected) continue;
    const change = recipe.resolution === "fixed" ? 1 : Math.min(1, difference / (selected * 255 * 1.4));
    const size = Math.max(1, Math.round(recipe.minBlock + (recipe.maxBlock - recipe.minBlock) * change));
    if (size <= 1) continue;
    const sampleOffset = (sampleY * width + sampleX) * 4;
    const centerX = Math.round((cellX + x1 - 1) / 2), centerY = Math.round((cellY + y1 - 1) / 2);
    const left = centerX - Math.floor(size / 2), top = centerY - Math.floor(size / 2);
    for (let y = top; y < top + size; y += 1) for (let x = left; x < left + size; x += 1) {
      if (x < 0 || y < 0 || x >= width || y >= height || !mask[y * width + x]) continue;
      resolved.set(sorted.subarray(sampleOffset, sampleOffset + 4), (y * width + x) * 4);
    }
  }
  return resolved;
}

function ultimateSort(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  let output = cloneSurface(input);
  const recipes = effect.ultimateSort?.recipes ?? [];
  const motion = 0.5 + 0.5 * Math.cos(phase);
  recipes.forEach((sortRecipe, recipeIndex) => {
    if (!sortRecipe.enabled) return;
    const context = output.getContext("2d")!;
    const image = context.getImageData(0, 0, output.width, output.height);
    const incoming = new Uint8ClampedArray(image.data);
    const mask = ultimateTerritoryMask(incoming, output.width, output.height, sortRecipe);
    if (sortRecipe.action !== "wand") {
      const vertical = sortRecipe.direction === "up" || sortRecipe.direction === "down";
      const reverseTravel = sortRecipe.direction === "right" || sortRecipe.direction === "down";
      const lines = vertical ? output.width : output.height;
      const length = vertical ? output.height : output.width;
      const method = Math.max(0, ultimateMethods.indexOf(sortRecipe.method));
      const channel = Math.max(0, ultimateSignals.indexOf(sortRecipe.signal));
      const progress = Math.max(0, Math.min(1, sortRecipe.amount * motion));
      const seed = recipe.seed + effect.where.seed + recipeIndex * 10007 + 8801;
      for (let line = 0; line < lines; line += 1) {
        const positions: number[] = [];
        const pixels: MotionPixel[] = [];
        for (let axis = 0; axis < length; axis += 1) {
          const x = vertical ? line : axis, y = vertical ? axis : line;
          const pixel = y * output.width + x;
          if (!mask[pixel]) continue;
          const offset = pixel * 4;
          positions.push(pixel);
          pixels.push({ rgba: [incoming[offset], incoming[offset + 1], incoming[offset + 2], incoming[offset + 3]], key: colorKey(incoming, offset, channel) });
        }
        orderMotionFragment(pixels, method, progress, false, seed, line, 0);
        positions.forEach((pixel, index) => image.data.set(pixels[reverseTravel ? pixels.length - 1 - index : index].rgba, pixel * 4));
      }
      image.data.set(applyUltimateResolution(incoming, image.data, mask, output.width, output.height, sortRecipe));
    }
    if (sortRecipe.action !== "sort") {
      const march = Math.floor((phase / (Math.PI * 2)) * 8 * sortRecipe.selectionSpeed);
      for (let y = 0; y < output.height; y += 1) for (let x = 0; x < output.width; x += 1) {
        const pixel = y * output.width + x;
        if (!mask[pixel]) continue;
        const boundary = x === 0 || y === 0 || x === output.width - 1 || y === output.height - 1
          || !mask[pixel - 1] || !mask[pixel + 1] || !mask[pixel - output.width] || !mask[pixel + output.width];
        if (!boundary) continue;
        const value = ((x + y + march) % 8) < 4 ? 245 : 20;
        image.data.set([value, value, value, 255], pixel * 4);
      }
    }
    context.putImageData(image, 0, 0);
  });
  return output;
}

function wizPixelOrder(width: number, height: number, path: Wizprocess["path"]) {
  const order = new Int32Array(width * height);
  let cursor = 0;
  if (path === "columns") {
    for (let x = 0; x < width; x += 1) for (let y = 0; y < height; y += 1) order[cursor++] = y * width + x;
  } else if (path === "snake") {
    for (let y = 0; y < height; y += 1) {
      for (let step = 0; step < width; step += 1) {
        const x = (y & 1) === 0 ? step : width - 1 - step;
        order[cursor++] = y * width + x;
      }
    }
  } else if (path === "clustered") {
    const tile = 32;
    for (let tileY = 0; tileY < height; tileY += tile) for (let tileX = 0; tileX < width; tileX += tile) {
      for (let morton = 0; morton < tile * tile; morton += 1) {
        let localX = 0, localY = 0;
        for (let bit = 0; bit < 5; bit += 1) {
          localX |= ((morton >> (bit * 2)) & 1) << bit;
          localY |= ((morton >> (bit * 2 + 1)) & 1) << bit;
        }
        const x = tileX + localX, y = tileY + localY;
        if (x < width && y < height) order[cursor++] = y * width + x;
      }
    }
  } else {
    for (let index = 0; index < order.length; index += 1) order[index] = index;
  }
  return order;
}

function rgbToHsb255(red: number, green: number, blue: number): [number, number, number] {
  const r = red / 255, g = green / 255, b = blue / 255;
  const high = Math.max(r, g, b), low = Math.min(r, g, b), delta = high - low;
  let hue = 0;
  if (delta > 0) {
    hue = high === r ? ((g - b) / delta) % 6 : high === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
    hue = ((hue * 60) + 360) % 360;
  }
  return [hue / 360 * 255, high <= 0 ? 0 : delta / high * 255, high * 255];
}

function hsbToRgb255(hue: number, saturation: number, brightness: number): [number, number, number] {
  const h = (hue / 255 * 360) % 360, s = saturation / 255, v = brightness / 255;
  const chroma = v * s, section = h / 60, middle = chroma * (1 - Math.abs((section % 2) - 1));
  const [r1, g1, b1] = section < 1 ? [chroma, middle, 0] : section < 2 ? [middle, chroma, 0]
    : section < 3 ? [0, chroma, middle] : section < 4 ? [0, middle, chroma]
      : section < 5 ? [middle, 0, chroma] : [chroma, 0, middle];
  const match = v - chroma;
  return [(r1 + match) * 255, (g1 + match) * 255, (b1 + match) * 255];
}

function wizRecover(value: number, mode: Wizprocess["reconstruction"]) {
  if (mode === "clip") return Math.max(0, Math.min(255, value));
  if (mode === "wrap") return ((value % 256) + 256) % 256;
  if (mode === "reflect") {
    const reflected = ((value % 510) + 510) % 510;
    return reflected <= 255 ? reflected : 510 - reflected;
  }
  return Math.abs(value < 0 ? 256 + value : value) % 256;
}

function wizScaleWeight(span: number, process: Wizprocess, phase: number) {
  const tide = process.tide;
  const mass = process.mass * (1 - tide * 0.9 * Math.sin(phase * 0.5) ** 2);
  const structure = process.structure * (1 - tide * 0.9 * Math.sin(phase) ** 2);
  const grain = process.grain * (1 - tide * 0.9 * Math.sin(phase * 1.5) ** 2);
  return span <= 8 ? grain : span <= 128 ? structure : mass;
}

function transformWizSignal(signal: Float32Array, process: Wizprocess, phase: number) {
  const maximumBlock = 16384;
  const sqrtHalf = Math.SQRT1_2;
  let offset = 0;
  while (offset < signal.length) {
    const remaining = signal.length - offset;
    const length = 2 ** Math.floor(Math.log2(Math.min(maximumBlock, remaining)));
    if (length < 2) {
      const mass = process.mass * (1 - process.tide * 0.9 * Math.sin(phase * 0.5) ** 2);
      signal[offset] = Math.trunc(signal[offset] * mass / process.compression) * process.expansion;
      break;
    }
    const temporary = new Float32Array(length);
    let active = length, span = 2;
    while (active >= 2) {
      const half = active / 2;
      const survival = wizScaleWeight(span, process, phase);
      for (let index = 0; index < half; index += 1) {
        const a = signal[offset + index * 2], b = signal[offset + index * 2 + 1];
        temporary[index] = (a + b) * sqrtHalf;
        temporary[half + index] = (a - b) * sqrtHalf * survival;
      }
      signal.set(temporary.subarray(0, active), offset);
      active = half;
      span *= 2;
    }
    signal[offset] *= wizScaleWeight(length * 2, process, phase);
    for (let index = 0; index < length; index += 1) signal[offset + index] = Math.trunc(signal[offset + index] / process.compression);
    active = 1;
    while (active < length) {
      for (let index = 0; index < active; index += 1) {
        const average = signal[offset + index], detail = signal[offset + active + index];
        temporary[index * 2] = (average + detail) * sqrtHalf;
        temporary[index * 2 + 1] = (average - detail) * sqrtHalf;
      }
      signal.set(temporary.subarray(0, active * 2), offset);
      active *= 2;
    }
    for (let index = 0; index < length; index += 1) signal[offset + index] *= process.expansion;
    offset += length;
  }
  return signal;
}

function wizprocess(input: HTMLCanvasElement, effect: EffectInstance, phase: number) {
  const process = effect.wizprocess;
  if (!process) return cloneSurface(input);
  const output = cloneSurface(input), context = output.getContext("2d")!;
  const image = context.getImageData(0, 0, output.width, output.height);
  const source = new Uint8ClampedArray(image.data);
  const order = wizPixelOrder(output.width, output.height, process.path);
  const evidence = new Float32Array(order.length * 3);
  for (let position = 0; position < order.length; position += 1) {
    const offset = order[position] * 4;
    const values = process.colorSpace === "hsb" ? rgbToHsb255(source[offset], source[offset + 1], source[offset + 2]) : [source[offset], source[offset + 1], source[offset + 2]] as [number, number, number];
    for (let channel = 0; channel < 3; channel += 1) evidence[position * 3 + channel] = values[channel] > 127 ? values[channel] - 256 : values[channel];
  }
  const reconstructed = new Float32Array(evidence.length);
  if (process.channels === "together") {
    transformWizSignal(evidence, process, phase);
    const shift = process.channelPhase;
    let offset = 0;
    while (offset < evidence.length) {
      const length = 2 ** Math.floor(Math.log2(Math.min(16384, evidence.length - offset)));
      for (let local = 0; local < length; local += 1) reconstructed[offset + local] = evidence[offset + ((local + shift + length) % length)];
      offset += length;
    }
  } else {
    for (let channel = 0; channel < 3; channel += 1) {
      const separated = new Float32Array(order.length);
      for (let position = 0; position < order.length; position += 1) separated[position] = evidence[position * 3 + channel];
      transformWizSignal(separated, process, phase);
      for (let position = 0; position < order.length; position += 1) reconstructed[position * 3 + channel] = separated[position];
    }
  }
  for (let position = 0; position < order.length; position += 1) {
    const offset = order[position] * 4;
    const recovered = [0, 1, 2].map((channel) => wizRecover(reconstructed[position * 3 + channel], process.reconstruction)) as [number, number, number];
    const rgb = process.colorSpace === "hsb" ? hsbToRgb255(...recovered) : recovered;
    image.data[offset] = rgb[0]; image.data[offset + 1] = rgb[1]; image.data[offset + 2] = rgb[2]; image.data[offset + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  return output;
}

function pixelDrift(input: HTMLCanvasElement, effect: EffectInstance) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  context.drawImage(input, 0, 0);
  let image = context.getImageData(0, 0, input.width, input.height);
  const distance = Math.round(param(effect, "distance", 9));
  const iterations = Math.round(param(effect, "iterations", 4));
  const hueMemory = param(effect, "hueMemory", 0.82);
  const lightMemory = param(effect, "lightMemory", 0.38);
  const direction = Math.round(param(effect, "direction", 0));
  const dx = direction === 0 ? -distance : direction === 1 ? distance : 0;
  const dy = direction === 2 ? -distance : direction === 3 ? distance : 0;
  for (let pass = 0; pass < iterations; pass += 1) {
    const prior = new Uint8ClampedArray(image.data);
    for (let y = 0; y < input.height; y += 1) {
      for (let x = 0; x < input.width; x += 1) {
        const sx = Math.max(0, Math.min(input.width - 1, x + dx));
        const sy = Math.max(0, Math.min(input.height - 1, y + dy));
        const offset = (y * input.width + x) * 4;
        const sourceOffset = (sy * input.width + sx) * 4;
        const sourceLight = (prior[sourceOffset] + prior[sourceOffset + 1] + prior[sourceOffset + 2]) / 3;
        const localLight = (prior[offset] + prior[offset + 1] + prior[offset + 2]) / 3;
        const lightMix = sourceLight > localLight ? 1 - lightMemory : (1 - lightMemory) * 0.38;
        for (let c = 0; c < 3; c += 1) {
          const mix = c === 1 ? (1 - hueMemory) * 0.7 + lightMix * 0.3 : lightMix;
          image.data[offset + c] = prior[offset + c] * (1 - mix) + prior[sourceOffset + c] * mix;
        }
      }
    }
  }
  context.putImageData(image, 0, 0);
  return output;
}

function signalEcho(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const separation = param(effect, "separation", 13);
  const bleed = param(effect, "bleed", 0.54);
  const scan = param(effect, "scan", 0.28);
  const ghost = param(effect, "ghost", 0.46);
  context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "#000";
  context.fillRect(0, 0, input.width, input.height);
  context.globalAlpha = 0.86;
  context.drawImage(input, 0, 0);
  context.globalCompositeOperation = "screen";
  context.globalAlpha = 0.18 + bleed * 0.34;
  context.drawImage(input, separation * (1 + Math.sin(phase) * 0.2), 0);
  if (recipe.colorMode === "palette") {
    context.fillStyle = packedCss(recipe.palette[0], 0.22 + bleed * 0.25);
    context.fillRect(separation, 0, input.width, input.height);
  }
  context.drawImage(input, -separation * 0.72, 0);
  if (recipe.colorMode === "palette") {
    context.fillStyle = packedCss(recipe.palette[1], 0.14 + bleed * 0.22);
    context.fillRect(-separation, 0, input.width, input.height);
  }
  context.globalCompositeOperation = "source-over";
  context.globalAlpha = ghost * 0.42;
  context.drawImage(input, separation * 3.2, Math.sin(phase) * 4);
  context.globalAlpha = 0.12 + scan * 0.6;
  context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "rgba(0,0,0,.85)";
  const spacing = Math.max(2, Math.round(8 - scan * 6));
  for (let y = 0; y < input.height; y += spacing) context.fillRect(0, y, input.width, Math.max(1, scan * 2));
  context.globalAlpha = 1;
  return output;
}

function ditherField(input: HTMLCanvasElement, effect: EffectInstance) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  context.drawImage(input, 0, 0);
  const image = context.getImageData(0, 0, input.width, input.height);
  const levels = Math.round(param(effect, "levels", 4));
  const grain = Math.round(param(effect, "grain", 2));
  const pressure = param(effect, "pressure", 0.68);
  const offset = Math.round(param(effect, "channelOffset", 2));
  const matrix = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  const step = 255 / Math.max(1, levels - 1);
  const prior = new Uint8ClampedArray(image.data);
  for (let y = 0; y < input.height; y += 1) {
    for (let x = 0; x < input.width; x += 1) {
      const target = (y * input.width + x) * 4;
      for (let channel = 0; channel < 3; channel += 1) {
        const shiftedX = Math.max(0, Math.min(input.width - 1, x + (channel - 1) * offset));
        const source = (y * input.width + shiftedX) * 4 + channel;
        const threshold = (matrix[((Math.floor(y / grain) & 3) * 4) + (Math.floor(x / grain) & 3)] / 15 - 0.5) * step * pressure;
        image.data[target + channel] = Math.max(0, Math.min(255, Math.round((prior[source] + threshold) / step) * step));
      }
    }
  }
  context.putImageData(image, 0, 0);
  return output;
}

function lensWarp(input: HTMLCanvasElement, effect: EffectInstance, phase: number) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const sourceContext = input.getContext("2d")!;
  const source = sourceContext.getImageData(0, 0, input.width, input.height);
  const image = context.createImageData(input.width, input.height);
  const bendX = param(effect, "bendX", 0.22);
  const bendY = param(effect, "bendY", 0.14);
  const frequency = param(effect, "frequency", 3.4);
  const mode = Math.round(param(effect, "mode", 1));
  for (let y = 0; y < input.height; y += 1) {
    const ny = y / input.height - 0.5;
    for (let x = 0; x < input.width; x += 1) {
      const nx = x / input.width - 0.5;
      const at = (y * input.width + x) * 4;
      const light = (source.data[at] + source.data[at + 1] + source.data[at + 2]) / 765 - 0.5;
      let ox = light * input.width * bendX;
      let oy = light * input.height * bendY;
      if (mode === 1) {
        ox += Math.sin((ny * frequency + phase * 0.1) * Math.PI * 2) * input.width * bendX * 0.34;
        oy += Math.cos((nx * frequency - phase * 0.1) * Math.PI * 2) * input.height * bendY * 0.34;
      } else if (mode === 2) {
        const angle = Math.atan2(ny, nx) + light * bendX * 3;
        const radius = Math.sqrt(nx * nx + ny * ny) * (1 + light * bendY * 2);
        ox += (Math.cos(angle) * radius - nx) * input.width;
        oy += (Math.sin(angle) * radius - ny) * input.height;
      }
      const sx = ((Math.round(x + ox) % input.width) + input.width) % input.width;
      const sy = ((Math.round(y + oy) % input.height) + input.height) % input.height;
      const sourceAt = (sy * input.width + sx) * 4;
      image.data[at] = source.data[sourceAt];
      image.data[at + 1] = source.data[sourceAt + 1];
      image.data[at + 2] = source.data[sourceAt + 2];
      image.data[at + 3] = 255;
    }
  }
  context.putImageData(image, 0, 0);
  return output;
}

function mirrorCut(input: HTMLCanvasElement, effect: EffectInstance) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const mode = Math.round(param(effect, "mode", 2));
  const offset = param(effect, "offset", 0.16);
  const mix = param(effect, "mix", 0.74);
  context.drawImage(input, 0, 0);
  context.globalAlpha = mix;
  if (mode === 0 || mode === 1) {
    context.save();
    context.translate(mode === 0 ? input.width : 0, offset * input.height);
    context.scale(-1, 1);
    context.drawImage(input, mode === 0 ? 0 : -input.width, 0);
    context.restore();
  } else if (mode === 2 || mode === 3) {
    context.save();
    context.translate(offset * input.width, mode === 2 ? input.height : 0);
    context.scale(1, -1);
    context.drawImage(input, 0, mode === 2 ? 0 : -input.height);
    context.restore();
  } else if (mode === 4) {
    context.save();
    context.translate(input.width * (0.5 + offset * 0.2), input.height * 0.5);
    context.rotate(Math.PI / 2);
    context.scale(-1, 1);
    context.drawImage(input, -input.width / 2, -input.height / 2);
    context.restore();
  } else {
    context.save();
    context.translate(input.width * offset, input.height * -offset);
    context.scale(-1, 1);
    context.drawImage(input, -input.width, 0);
    context.restore();
  }
  context.globalAlpha = 1;
  return output;
}

function motionLeak(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const block = Math.max(4, Math.round(param(effect, "block", 16)));
  const vector = param(effect, "vector", 28);
  const leak = param(effect, "leak", 0.58);
  const residual = param(effect, "residual", 0.34);
  const coherence = param(effect, "coherence", 0.67);
  const random = randomSource(recipe.seed + 8849 + Math.round(phase * 100));
  context.drawImage(input, 0, 0);
  for (let y = 0; y < input.height; y += block) {
    for (let x = 0; x < input.width; x += block) {
      if (random() > leak) continue;
      const waveX = Math.sin(y * 0.018 * coherence + phase) * vector;
      const waveY = Math.cos(x * 0.014 * coherence - phase * 0.7) * vector * 0.55;
      const chaos = 1 - coherence;
      const dx = waveX + (random() * 2 - 1) * vector * chaos;
      const dy = waveY + (random() * 2 - 1) * vector * chaos;
      const sourceX = Math.max(0, Math.min(input.width - block, x + dx));
      const sourceY = Math.max(0, Math.min(input.height - block, y + dy));
      context.globalAlpha = 0.5 + leak * 0.5;
      context.drawImage(input, sourceX, sourceY, block, block, x, y, block + 1, block + 1);
      if (residual > 0) {
        context.globalCompositeOperation = "screen";
        context.globalAlpha = residual * 0.56;
        context.drawImage(input, x, y, block, block, x + dx * 0.12, y + dy * 0.12, block, block);
        context.globalCompositeOperation = "source-over";
      }
    }
  }
  context.globalAlpha = 1;
  return output;
}

function asciiHash(seed: number, column: number, row: number, salt = 0) {
  let value = (seed ^ Math.imul(column + salt, 374761393) ^ Math.imul(row - salt, 668265263)) | 0;
  value = Math.imul(value ^ (value >>> 13), 1274126177);
  return ((value ^ (value >>> 16)) >>> 0) / 4294967295;
}

function asciiField(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const field = effect.characterField;
  const composition = field?.composition ?? "field";
  const glyphLogic = field?.glyphLogic ?? "mass";
  const output = composition === "inlay" ? cloneSurface(input) : newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const source = input.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, input.width, input.height);
  const glyphs = field?.glyphs?.length ? field.glyphs : [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"];
  const scale = Math.min(input.width, input.height) / 760;
  const cell = Math.max(5, Math.round(param(effect, "cellSize", 15) * scale));
  const columns = Math.ceil(input.width / cell);
  const rows = Math.ceil(input.height / cell);
  const coverage = param(effect, "coverage", 1);
  const loyalty = param(effect, "imageLoyalty", 0.88);
  const edgeVoice = param(effect, "edgeVoice", 0.32);
  const instability = param(effect, "instability", 0.1);
  const vacancy = param(effect, "vacancy", 0.03);
  const damage = param(effect, "gridDamage", 0.04);
  const inverted = param(effect, "invertDensity", 0) >= 0.5;
  const seed = recipe.seed + effect.where.seed + Math.round(phase * 1000);
  const territoryScale = Math.max(cell, effect.where.scale * scale);
  const lumaAt = (x: number, y: number) => {
    const sx = Math.max(0, Math.min(input.width - 1, Math.round(x)));
    const sy = Math.max(0, Math.min(input.height - 1, Math.round(y)));
    const at = (sy * input.width + sx) * 4;
    return (source.data[at] * 0.2126 + source.data[at + 1] * 0.7152 + source.data[at + 2] * 0.0722) / 255;
  };
  if (composition === "field") {
    context.fillStyle = packedCss(field?.groundColor ?? recipe.palette[3]);
    context.fillRect(0, 0, input.width, input.height);
  }
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.font = `700 ${Math.max(5, cell * 0.9)}px Consolas, "Segoe UI Symbol", "Segoe UI Emoji", monospace`;
  for (let row = 0; row < rows; row += 1) {
    const rowSlip = (asciiHash(seed, 0, row, 11) * 2 - 1) * cell * damage * 2.4;
    for (let column = 0; column < columns; column += 1) {
      const columnSlip = (asciiHash(seed, column, 0, 23) * 2 - 1) * cell * damage * 1.5;
      const x = column * cell + cell * 0.5 + rowSlip;
      const y = row * cell + cell * 0.5 + columnSlip;
      const light = lumaAt(x, y);
      const edgeX = lumaAt(x + cell * 0.45, y) - lumaAt(x - cell * 0.45, y);
      const edgeY = lumaAt(x, y + cell * 0.45) - lumaAt(x, y - cell * 0.45);
      const edge = Math.min(1, Math.hypot(edgeX, edgeY) * 2.2);
      const sampleX = Math.max(0, Math.min(input.width - 1, Math.round(x)));
      const sampleY = Math.max(0, Math.min(input.height - 1, Math.round(y)));
      const at = (sampleY * input.width + sampleX) * 4;
      const signal = hueAndSaturation(source.data[at], source.data[at + 1], source.data[at + 2]);
      const feather = composition === "inlay" ? 0.001 : Math.max(0.001, effect.where.softness);
      const territoryColumn = Math.floor(x / territoryScale);
      const territoryRow = Math.floor(y / territoryScale);
      let territory = 1;
      if (effect.where.mode === "light") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
      else if (effect.where.mode === "dark") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
      else if (effect.where.mode === "edges") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, edge);
      else if (effect.where.mode === "saturated") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
      else if (effect.where.mode === "muted") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
      else if (effect.where.mode === "hue") {
        const distance = Math.abs(((signal.hue - effect.where.hue + 540) % 360) - 180);
        territory = (1 - smoothstep(effect.where.hueWidth, Math.min(180, effect.where.hueWidth + feather * 180), distance)) * smoothstep(0.01, 0.08, signal.saturation);
      } else if (effect.where.mode === "checker") territory = (territoryColumn + territoryRow) % 2 === 0 ? 1 : 0;
      else if (effect.where.mode === "stripes") territory = territoryColumn % 2 === 0 ? 1 : 0;
      else if (effect.where.mode === "blocks") territory = asciiHash(effect.where.seed, territoryColumn, territoryRow, 71) >= effect.where.threshold ? 1 : 0;
      else if (effect.where.mode === "random") territory = asciiHash(effect.where.seed, territoryColumn, territoryRow, 73) < effect.where.threshold ? 1 : 0;
      if (effect.where.invert) territory = 1 - territory;
      if (asciiHash(seed, column, row, 79) >= territory) continue;
      if (composition === "inlay") {
        context.fillStyle = packedCss(field?.groundColor ?? recipe.palette[3]);
        context.fillRect(column * cell, row * cell, cell + 1, cell + 1);
      }
      if (asciiHash(seed, column, row, 83) >= coverage) continue;
      if (asciiHash(seed, column, row, 17) < vacancy) continue;
      const noise = asciiHash(seed, column, row, 31);
      let density = inverted ? light : 1 - light;
      density = density * loyalty + noise * (1 - loyalty);
      let index = glyphLogic === "repeat"
        ? (column + row) % glyphs.length
        : Math.max(0, Math.min(glyphs.length - 1, Math.round(density * (glyphs.length - 1))));
      if (asciiHash(seed, column, row, 43) < instability) {
        const reach = Math.max(1, Math.round(instability * glyphs.length * 0.6));
        index = Math.max(0, Math.min(glyphs.length - 1, index + Math.round((asciiHash(seed, column, row, 47) * 2 - 1) * reach)));
      }
      let glyph = glyphs[index] ?? " ";
      if (edge * edgeVoice > asciiHash(seed, column, row, 53) * 0.35) {
        glyph = Math.abs(edgeX) > Math.abs(edgeY) * 2
          ? "|"
          : Math.abs(edgeY) > Math.abs(edgeX) * 2
            ? "-"
            : edgeX * edgeY > 0 ? "/" : "\\";
      }
      if (field?.inkMode === "source") context.fillStyle = `rgb(${source.data[at]},${source.data[at + 1]},${source.data[at + 2]})`;
      else if (field?.inkMode === "chosen") context.fillStyle = packedCss(field.inkColor);
      else context.fillStyle = packedCss(recipe.palette[Math.max(0, Math.min(2, Math.round(density * 2)))]);
      context.fillText(glyph, x, y + cell * 0.04);
    }
  }
  return output;
}

function zhuyinWeave(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number) {
  const field = effect.zhuyinField;
  const composition = field?.composition ?? "inlay";
  const output = composition === "inlay" ? cloneSurface(input) : newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const source = input.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, input.width, input.height);
  const glyphs = field?.glyphs?.length ? field.glyphs : Array.from("ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ");
  const scale = Math.min(input.width, input.height) / 760;
  const cell = Math.max(6, Math.round(param(effect, "cellSize", 22) * scale));
  const columns = Math.ceil(input.width / cell) + 2;
  const rows = Math.ceil(input.height / cell) + 2;
  const coverage = param(effect, "coverage", 0.82);
  const voices = Math.max(1, Math.min(4, Math.round(param(effect, "voices", 2))));
  const misregistration = param(effect, "misregistration", 0.22);
  const rowDrift = param(effect, "rowDrift", 0.42);
  const imageRhythm = param(effect, "imageRhythm", 0.38);
  const motion = param(effect, "motion", 0.32);
  const seed = recipe.seed + effect.where.seed;
  const loopAngle = phase * Math.PI * 2;
  const territoryScale = Math.max(cell, effect.where.scale * scale);
  const sampleAt = (x: number, y: number) => {
    const sx = Math.max(0, Math.min(input.width - 1, Math.round(x)));
    const sy = Math.max(0, Math.min(input.height - 1, Math.round(y)));
    const at = (sy * input.width + sx) * 4;
    const light = (source.data[at] * 0.2126 + source.data[at + 1] * 0.7152 + source.data[at + 2] * 0.0722) / 255;
    return { at, light };
  };
  if (composition === "field") {
    context.fillStyle = packedCss(field?.groundColor ?? recipe.palette[3]);
    context.fillRect(0, 0, input.width, input.height);
  }
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.font = `600 ${Math.max(6, cell * 0.86)}px "Microsoft JhengHei", "Noto Sans TC", MingLiU, sans-serif`;
  for (let row = -1; row < rows; row += 1) {
    const stagger = row * cell * rowDrift * 0.72;
    for (let column = -1; column < columns; column += 1) {
      const baseX = column * cell + cell * 0.5 + stagger;
      const baseY = row * cell + cell * 0.5;
      const { at, light } = sampleAt(baseX, baseY);
      const right = sampleAt(baseX + cell * 0.45, baseY).light;
      const left = sampleAt(baseX - cell * 0.45, baseY).light;
      const below = sampleAt(baseX, baseY + cell * 0.45).light;
      const above = sampleAt(baseX, baseY - cell * 0.45).light;
      const edge = Math.min(1, Math.hypot(right - left, below - above) * 2.2);
      const signal = hueAndSaturation(source.data[at], source.data[at + 1], source.data[at + 2]);
      const feather = composition === "inlay" ? 0.001 : Math.max(0.001, effect.where.softness);
      const territoryColumn = Math.floor(baseX / territoryScale);
      const territoryRow = Math.floor(baseY / territoryScale);
      let territory = 1;
      if (effect.where.mode === "light") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
      else if (effect.where.mode === "dark") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
      else if (effect.where.mode === "edges") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, edge);
      else if (effect.where.mode === "saturated") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
      else if (effect.where.mode === "muted") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
      else if (effect.where.mode === "hue") {
        const distance = Math.abs(((signal.hue - effect.where.hue + 540) % 360) - 180);
        territory = (1 - smoothstep(effect.where.hueWidth, Math.min(180, effect.where.hueWidth + feather * 180), distance)) * smoothstep(0.01, 0.08, signal.saturation);
      } else if (effect.where.mode === "checker") territory = (territoryColumn + territoryRow) % 2 === 0 ? 1 : 0;
      else if (effect.where.mode === "stripes") territory = territoryColumn % 2 === 0 ? 1 : 0;
      else if (effect.where.mode === "blocks") territory = asciiHash(effect.where.seed, territoryColumn, territoryRow, 71) >= effect.where.threshold ? 1 : 0;
      else if (effect.where.mode === "random") territory = asciiHash(effect.where.seed, territoryColumn, territoryRow, 73) < effect.where.threshold ? 1 : 0;
      if (effect.where.invert) territory = 1 - territory;
      if (asciiHash(seed, column, row, 101) >= territory || asciiHash(seed, column, row, 103) >= coverage) continue;
      if (composition === "inlay") {
        context.fillStyle = packedCss(field?.groundColor ?? recipe.palette[3]);
        context.fillRect(baseX - cell * 0.55, baseY - cell * 0.55, cell * 1.1, cell * 1.1);
      }
      const imageOffset = Math.round(light * imageRhythm * Math.max(1, glyphs.length - 1));
      const motionOffset = Math.round(Math.sin(loopAngle + row * 0.19) * motion * glyphs.length * 0.18);
      for (let voice = 0; voice < voices; voice += 1) {
        const voiceAngle = loopAngle + voice * Math.PI * 2 / voices;
        const distance = cell * misregistration * (voice / Math.max(1, voices - 1));
        const x = baseX + Math.cos(voiceAngle) * distance * (0.35 + motion * 0.65);
        const y = baseY + Math.sin(voiceAngle) * distance * (0.35 + motion * 0.65);
        const glyphIndex = ((column + Math.round(row * (1 + rowDrift * 4)) + voice * 7 + imageOffset + motionOffset) % glyphs.length + glyphs.length) % glyphs.length;
        if (field?.inkMode === "source") context.fillStyle = `rgb(${source.data[at]},${source.data[at + 1]},${source.data[at + 2]})`;
        else if (field?.inkMode === "chosen") context.fillStyle = packedCss(field.inkColor);
        else context.fillStyle = packedCss(recipe.palette[voice % 4]);
        context.globalAlpha = voices === 1 ? 1 : Math.max(0.48, 0.86 - voice * 0.1);
        context.fillText(glyphs[glyphIndex], x, y + cell * 0.03);
      }
    }
  }
  context.globalAlpha = 1;
  return output;
}

function petsciiStudy(input: HTMLCanvasElement, effect: EffectInstance) {
  const output = newSurface(input.width, input.height);
  const context = output.getContext("2d")!;
  const source = input.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, input.width, input.height);
  const foreground = effect.tileField?.foregroundColor ?? petsciiPalette[14];
  const background = effect.tileField?.backgroundColor ?? petsciiPalette[0];
  const threshold = param(effect, "threshold", 0.48);
  const imagePull = param(effect, "imagePull", 0.78);
  const reverseMass = param(effect, "reverseMass", 0) >= 0.5;
  const sample = (x: number, y: number) => {
    const sx = Math.max(0, Math.min(input.width - 1, Math.round(x)));
    const sy = Math.max(0, Math.min(input.height - 1, Math.round(y)));
    const at = (sy * input.width + sx) * 4;
    return { r: source.data[at], g: source.data[at + 1], b: source.data[at + 2] };
  };
  const nearestPalette = (r: number, g: number, b: number) => {
    let nearest: number = petsciiPalette[0], distance = Number.POSITIVE_INFINITY;
    for (const packed of petsciiPalette) {
      const pr = (packed >> 16) & 255, pg = (packed >> 8) & 255, pb = packed & 255;
      const next = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2;
      if (next < distance) { nearest = packed; distance = next; }
    }
    return nearest;
  };
  const mixedInk = (sampled: number) => {
    const red = Math.round(((foreground >> 16) & 255) * (1 - imagePull) + ((sampled >> 16) & 255) * imagePull);
    const green = Math.round(((foreground >> 8) & 255) * (1 - imagePull) + ((sampled >> 8) & 255) * imagePull);
    const blue = Math.round((foreground & 255) * (1 - imagePull) + (sampled & 255) * imagePull);
    return (red << 16) | (green << 8) | blue;
  };
  context.fillStyle = packedCss(background);
  context.fillRect(0, 0, input.width, input.height);
  for (let row = 0; row < 25; row += 1) {
    const y0 = Math.round(row * input.height / 25), y1 = Math.round((row + 1) * input.height / 25);
    const middleY = Math.round((y0 + y1) / 2);
    for (let column = 0; column < 40; column += 1) {
      const x0 = Math.round(column * input.width / 40), x1 = Math.round((column + 1) * input.width / 40);
      const middleX = Math.round((x0 + x1) / 2);
      const points = [
        sample((x0 + middleX) / 2, (y0 + middleY) / 2),
        sample((middleX + x1) / 2, (y0 + middleY) / 2),
        sample((x0 + middleX) / 2, (middleY + y1) / 2),
        sample((middleX + x1) / 2, (middleY + y1) / 2),
      ];
      const active = points.map(({ r, g, b }) => {
        const light = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 255;
        return reverseMass ? light >= threshold : light <= threshold;
      });
      const colorPoints = points.filter((_, index) => active[index]);
      const evidence = colorPoints.length ? colorPoints : points;
      const average = evidence.reduce((held, color) => ({ r: held.r + color.r, g: held.g + color.g, b: held.b + color.b }), { r: 0, g: 0, b: 0 });
      const quantized = nearestPalette(average.r / evidence.length, average.g / evidence.length, average.b / evidence.length);
      context.fillStyle = packedCss(mixedInk(quantized));
      const regions = [
        [x0, y0, middleX - x0, middleY - y0],
        [middleX, y0, x1 - middleX, middleY - y0],
        [x0, middleY, middleX - x0, y1 - middleY],
        [middleX, middleY, x1 - middleX, y1 - middleY],
      ];
      active.forEach((visible, index) => { if (visible) context.fillRect(...regions[index] as [number, number, number, number]); });
    }
  }
  return output;
}

function transformEffect(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number, animated = false) {
  if (!effect.enabled) return input;
  switch (effect.type) {
    case "band-rupture": return bandRupture(input, effect, recipe, phase);
    case "wrong-sort": return wrongSort(input, effect, recipe);
    case "median-filter": return medianFilter(input, effect);
    case "sorting-motion": return sortingMotion(input, effect, recipe, phase);
    case "ultimate-sort": return ultimateSort(input, effect, recipe, phase);
    case "wizprocess": return wizprocess(input, effect, animated ? phase : 0);
    case "pixel-drift": return pixelDrift(input, effect);
    case "signal-echo": return signalEcho(input, effect, recipe, phase);
    case "dither-field": return ditherField(input, effect);
    case "lens-warp": return lensWarp(input, effect, phase);
    case "mirror-cut": return mirrorCut(input, effect);
    case "motion-leak": return motionLeak(input, effect, recipe, phase);
    case "resolution-quilt": return resolutionQuilt(input, effect, recipe);
    case "shard-field": return shardField(input, effect, recipe);
    case "cut-repeat": return cutRepeat(input, effect, recipe);
    case "ascii-field": return asciiField(input, effect, recipe, phase);
    case "zhuyin-weave": return zhuyinWeave(input, effect, recipe, phase);
    case "petscii-study": return petsciiStudy(input, effect);
  }
}

const smoothstep = (low: number, high: number, value: number) => {
  if (high <= low) return value >= high ? 1 : 0;
  const t = Math.max(0, Math.min(1, (value - low) / (high - low)));
  return t * t * (3 - 2 * t);
};

function hueAndSaturation(r: number, g: number, b: number) {
  const red = r / 255, green = g / 255, blue = b / 255;
  const maximum = Math.max(red, green, blue), minimum = Math.min(red, green, blue);
  const delta = maximum - minimum;
  let hue = 0;
  if (delta > 0) {
    if (maximum === red) hue = ((green - blue) / delta) % 6;
    else if (maximum === green) hue = (blue - red) / delta + 2;
    else hue = (red - green) / delta + 4;
    hue = ((hue * 60) + 360) % 360;
  }
  return { hue, saturation: maximum === 0 ? 0 : delta / maximum };
}

function whereWeights(input: HTMLCanvasElement, effect: EffectInstance) {
  const context = input.getContext("2d", { willReadFrequently: true })!;
  const image = context.getImageData(0, 0, input.width, input.height);
  const pixels = image.data;
  const weights = new Float32Array(input.width * input.height);
  const where = effect.where;
  const luminance = new Float32Array(weights.length);
  for (let index = 0; index < weights.length; index += 1) {
    const offset = index * 4;
    luminance[index] = (pixels[offset] * 0.2126 + pixels[offset + 1] * 0.7152 + pixels[offset + 2] * 0.0722) / 255;
  }
  const feather = Math.max(0.001, where.softness);
  const blockValue = (column: number, row: number) => {
    let hash = (where.seed ^ Math.imul(column, 374761393) ^ Math.imul(row, 668265263)) | 0;
    hash = Math.imul(hash ^ (hash >>> 13), 1274126177);
    return ((hash ^ (hash >>> 16)) >>> 0) / 4294967295;
  };
  for (let y = 0; y < input.height; y += 1) {
    for (let x = 0; x < input.width; x += 1) {
      const index = y * input.width + x;
      const offset = index * 4;
      const light = luminance[index];
      let weight = 1;
      if (where.mode === "light") weight = smoothstep(where.threshold - feather, where.threshold + feather, light);
      else if (where.mode === "dark") weight = 1 - smoothstep(where.threshold - feather, where.threshold + feather, light);
      else if (where.mode === "edges") {
        const left = luminance[y * input.width + Math.max(0, x - 1)];
        const right = luminance[y * input.width + Math.min(input.width - 1, x + 1)];
        const above = luminance[Math.max(0, y - 1) * input.width + x];
        const below = luminance[Math.min(input.height - 1, y + 1) * input.width + x];
        const edge = Math.min(1, Math.hypot(right - left, below - above) * 2.4);
        weight = smoothstep(where.threshold - feather, where.threshold + feather, edge);
      } else if (where.mode === "saturated" || where.mode === "muted" || where.mode === "hue") {
        const signal = hueAndSaturation(pixels[offset], pixels[offset + 1], pixels[offset + 2]);
        if (where.mode === "saturated") weight = smoothstep(where.threshold - feather, where.threshold + feather, signal.saturation);
        else if (where.mode === "muted") weight = 1 - smoothstep(where.threshold - feather, where.threshold + feather, signal.saturation);
        else {
          const distance = Math.abs(((signal.hue - where.hue + 540) % 360) - 180);
          weight = 1 - smoothstep(where.hueWidth, Math.min(180, where.hueWidth + feather * 180), distance);
          weight *= smoothstep(0.01, 0.08, signal.saturation);
        }
      } else if (where.mode === "checker") {
        weight = (Math.floor(x / where.scale) + Math.floor(y / where.scale)) % 2 === 0 ? 1 : 0;
      } else if (where.mode === "stripes") {
        weight = Math.floor(x / where.scale) % 2 === 0 ? 1 : 0;
      } else if (where.mode === "blocks") {
        weight = blockValue(Math.floor(x / where.scale), Math.floor(y / where.scale)) >= where.threshold ? 1 : 0;
      } else if (where.mode === "random") {
        weight = blockValue(Math.floor(x / where.scale), Math.floor(y / where.scale)) >= 0.5 ? 1 : 0;
      }
      weights[index] = where.invert ? 1 - weight : weight;
    }
  }
  return weights;
}

function applyEffect(input: HTMLCanvasElement, effect: EffectInstance, recipe: StudioRecipe, phase: number, animated = false) {
  if (!effect.enabled) return input;
  const transformed = transformEffect(input, effect, recipe, phase, animated);
  if (effect.type === "ascii-field" || effect.type === "zhuyin-weave" || effect.type === "petscii-study") return transformed;
  if (effect.where.mode === "whole" && !effect.where.invert) return transformed;
  const output = cloneSurface(input);
  const inputData = input.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, input.width, input.height);
  const transformedData = transformed.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, input.width, input.height);
  const outputContext = output.getContext("2d")!;
  const result = outputContext.createImageData(input.width, input.height);
  const weights = whereWeights(input, effect);
  for (let index = 0; index < weights.length; index += 1) {
    const amount = weights[index];
    const offset = index * 4;
    for (let channel = 0; channel < 4; channel += 1) result.data[offset + channel] = Math.round(inputData.data[offset + channel] * (1 - amount) + transformedData.data[offset + channel] * amount);
  }
  outputContext.putImageData(result, 0, 0);
  return output;
}

function targetSurface(input: HTMLCanvasElement, effect: EffectInstance) {
  const output = document.createElement("canvas");
  output.width = input.width; output.height = input.height;
  const context = output.getContext("2d")!;
  const image = context.createImageData(output.width, output.height);
  const weights = whereWeights(input, effect);
  for (let index = 0; index < weights.length; index += 1) {
    const value = Math.round(weights[index] * 255);
    const offset = index * 4;
    image.data[offset] = value; image.data[offset + 1] = value; image.data[offset + 2] = value; image.data[offset + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  return output;
}

export const LivePreview = forwardRef<LivePreviewHandle, LivePreviewProps>(function LivePreview({ recipe, sourceDataUrl, layerDataUrls = {}, showOriginal = false, targetPreviewEffectId, animate = false }, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sourceRef = useRef<HTMLImageElement | null>(null);
  const layerRefs = useRef<Record<string, HTMLImageElement>>({});
  const [sourceRevision, setSourceRevision] = useState(0);

  useEffect(() => {
    sourceRef.current = null;
    if (!sourceDataUrl) return;
    const image = new Image();
    image.src = sourceDataUrl;
    image.onload = () => { sourceRef.current = image; setSourceRevision((current) => current + 1); };
  }, [sourceDataUrl]);

  useEffect(() => {
    layerRefs.current = {};
    for (const [id, dataUrl] of Object.entries(layerDataUrls)) {
      const image = new Image();
      image.src = dataUrl;
      image.onload = () => { layerRefs.current[id] = image; setSourceRevision((current) => current + 1); };
    }
  }, [layerDataUrls]);

  useImperativeHandle(ref, () => ({
    capture: () => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      return { dataUrl: canvas.toDataURL("image/png"), width: canvas.width, height: canvas.height };
    },
  }), []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { alpha: false });
    if (!canvas || !context) return;
    const paint = (animatedPhase?: number) => {
      const aspect = Math.max(1 / 12, Math.min(12, recipe.renderWidth / Math.max(1, recipe.renderHeight)));
      const normalDimension = recipe.effects.some((effect) => effect.enabled && ["wrong-sort", "sorting-motion", "ultimate-sort", "wizprocess", "pixel-drift", "lens-warp", "dither-field"].includes(effect.type)) ? 560 : 760;
      const maxDimension = animate ? Math.min(420, normalDimension) : normalDimension;
      const width = aspect >= 1 ? maxDimension : Math.round(maxDimension * aspect);
      const height = aspect >= 1 ? Math.round(maxDimension / aspect) : maxDimension;
      if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
      const heldRecipe = { ...recipe, seed: recipe.seed + recipe.iteration * 104729 };
      let surface = fittedSource(sourceRef.current, width, height, heldRecipe);
      surface = compositeLayers(surface, heldRecipe, layerRefs.current);
      const original = cloneSurface(surface);
      const phase = animatedPhase ?? (recipe.iteration % recipe.loopFrames) / recipe.loopFrames * Math.PI * 2;
      if (!showOriginal) {
        let sourceBlended = false;
        for (const effect of heldRecipe.effects) {
          if (effect.enabled && (effect.type === "ascii-field" || effect.type === "zhuyin-weave" || effect.type === "petscii-study") && !sourceBlended && heldRecipe.sourcePresence > 0) {
            surface = blendSource(surface, original, heldRecipe.sourcePresence);
            sourceBlended = true;
          }
          if (targetPreviewEffectId === effect.id) { surface = targetSurface(surface, effect); break; }
          surface = applyEffect(surface, effect, heldRecipe, phase, animate);
        }
        if (!targetPreviewEffectId && !sourceBlended) surface = blendSource(surface, original, heldRecipe.sourcePresence);
      } else surface = original;
      context.drawImage(surface, 0, 0, width, height);
    };
    if (!animate) {
      paint();
      return;
    }
    let animationFrame = 0;
    let lastPaint = -Infinity;
    const startedAt = performance.now();
    const duration = recipe.loopFrames / recipe.loopFps * 1000;
    const tick = (now: number) => {
      if (now - lastPaint >= 1000 / recipe.loopFps) {
        const phase = ((now - startedAt) % duration) / duration * Math.PI * 2;
        paint(phase);
        lastPaint = now;
      }
      animationFrame = requestAnimationFrame(tick);
    };
    animationFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrame);
  }, [recipe, sourceDataUrl, sourceRevision, layerDataUrls, showOriginal, targetPreviewEffectId, animate]);

  return <canvas className="live-preview" ref={canvasRef} aria-label={animate ? "Animated loop audition of the current Glitch Temple recipe" : "Live preview of the current Glitch Temple recipe"} />;
});
