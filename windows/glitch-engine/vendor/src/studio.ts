export type EffectType =
  | "band-rupture"
  | "wrong-sort"
  | "median-filter"
  | "sorting-motion"
  | "ultimate-sort"
  | "wizprocess"
  | "pixel-drift"
  | "signal-echo"
  | "dither-field"
  | "lens-warp"
  | "mirror-cut"
  | "motion-leak"
  | "resolution-quilt"
  | "shard-field"
  | "cut-repeat"
  | "ascii-field"
  | "zhuyin-weave"
  | "petscii-study";

export type EffectParameter = {
  id: string;
  label: string;
  description: string;
  min: number;
  max: number;
  step: number;
  default: number;
  choices?: string[];
  suggestions?: ParameterSuggestion[];
};

export type ParameterSuggestion = { value: number; label: string };

export type EffectDefinition = {
  type: EffectType;
  name: string;
  category: "Order" | "Decay" | "Signal" | "Spatial" | "Quantize" | "Fold" | "Temporal" | "Character";
  description: string;
  parameters: EffectParameter[];
};

export type EffectInstance = {
  id: string;
  type: EffectType;
  enabled: boolean;
  where: EffectWhere;
  parameters: Record<string, number>;
  characterField?: CharacterField;
  zhuyinField?: ZhuyinField;
  tileField?: TileField;
  ultimateSort?: UltimateSortStack;
  wizprocess?: Wizprocess;
};

export type Wizprocess = {
  kind: "wizprocess";
  mass: number;
  structure: number;
  grain: number;
  compression: number;
  expansion: number;
  colorSpace: "rgb" | "hsb";
  channels: "together" | "separate";
  channelPhase: number;
  path: "rows" | "columns" | "snake" | "clustered";
  reconstruction: "fold" | "wrap" | "clip" | "reflect";
  tide: number;
  newStructureScale: boolean;
  newStructureWhere: boolean;
  newColors: boolean;
};

export const defaultWizprocess = (): Wizprocess => ({
  kind: "wizprocess",
  mass: 0.82,
  structure: 0.68,
  grain: 0.42,
  compression: 36,
  expansion: 42,
  colorSpace: "hsb",
  channels: "separate",
  channelPhase: 0,
  path: "rows",
  reconstruction: "fold",
  tide: 0.46,
  newStructureScale: true,
  newStructureWhere: true,
  newColors: true,
});

export type UltimateSortRecipe = {
  id: string;
  enabled: boolean;
  method: "bubble" | "insertion" | "selection" | "merge" | "permute" | "roll";
  amount: number;
  action: "sort" | "sort-outline" | "wand";
  direction: "left" | "right" | "up" | "down";
  signal: "red" | "green" | "blue" | "hue" | "saturation" | "brightness";
  territory: "whole" | "light" | "dark" | "edges" | "red" | "orange" | "yellow" | "green" | "cyan" | "blue" | "pink";
  gate: number;
  resolution: "pixel" | "fixed" | "wake";
  minBlock: number;
  maxBlock: number;
  selectionSpeed: number;
};

export type UltimateSortStack = {
  kind: "ultimate-sort";
  recipes: UltimateSortRecipe[];
};

let ultimateRecipeCounter = 0;
export const defaultUltimateSortRecipe = (seed = Date.now()): UltimateSortRecipe => ({
  id: `sort-recipe-${Math.abs(Math.round(seed + ultimateRecipeCounter++ * 7919)).toString(36)}`,
  enabled: true,
  method: "permute",
  amount: 0.1,
  action: "sort",
  direction: "left",
  signal: "hue",
  territory: "green",
  gate: 280,
  resolution: "wake",
  minBlock: 1,
  maxBlock: 18,
  selectionSpeed: 3,
});

export const defaultUltimateSortStack = (): UltimateSortStack => ({
  kind: "ultimate-sort",
  recipes: [
    {
      ...defaultUltimateSortRecipe(280),
      id: "selection-ghost",
      amount: 0.0001,
      action: "wand",
      signal: "brightness",
      territory: "edges",
      resolution: "pixel",
      maxBlock: 1,
    },
    {
      ...defaultUltimateSortRecipe(281),
      id: "green-resolution-wake",
    },
  ],
});

export type CharacterField = {
  kind: "ascii";
  bank: "density" | "punctuation" | "symbols" | "tiles" | "custom";
  glyphs: string[];
  composition: "field" | "inlay";
  glyphLogic: "mass" | "repeat";
  inkMode: "source" | "palette" | "chosen";
  inkColor: number;
  groundColor: number;
};

export const asciiBanks: { id: CharacterField["bank"]; label: string; description: string; glyphs: string[] }[] = [
  { id: "density", label: "ASCII", description: "A classic light-to-dark density ramp.", glyphs: [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"] },
  { id: "punctuation", label: "Punctuation", description: "Nervous language fragments and small cuts.", glyphs: [" ", ".", ",", ":", ";", "!", "?", "'", "\"", "/", "\\", "|", "_", "~"] },
  { id: "symbols", label: "Symbols", description: "Stars, hearts, moons, circles, and signs.", glyphs: [" ", "·", "○", "●", "◇", "◆", "△", "▲", "♥", "☾", "☼", "✦", "✕"] },
  { id: "tiles", label: "Tiles", description: "Block elements that rebuild the image as masonry.", glyphs: [" ", "░", "▒", "▓", "█", "▀", "▄", "▌", "▐", "■", "□", "◆"] },
  { id: "custom", label: "Custom", description: "Your own ordered character vocabulary.", glyphs: [" ", ".", ":", "*", "#", "@"] },
];

export const defaultCharacterField = (): CharacterField => ({
  kind: "ascii",
  bank: "punctuation",
  glyphs: [...asciiBanks[1].glyphs],
  composition: "inlay",
  glyphLogic: "repeat",
  inkMode: "chosen",
  inkColor: 0xf2eee7,
  groundColor: 0x151319,
});

export type ZhuyinField = {
  kind: "zhuyin";
  bank: "full" | "initials" | "finals" | "tones" | "custom";
  glyphs: string[];
  mutationMode: "held" | "drift" | "fracture";
  composition: "field" | "inlay";
  inkMode: "source" | "palette" | "chosen";
  inkColor: number;
  groundColor: number;
};

const zhuyinInitials = Array.from("ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ");
const zhuyinFinals = Array.from("ㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ");
const zhuyinTones = Array.from("ˉˊˇˋ˙");

export const zhuyinBanks: { id: ZhuyinField["bank"]; label: string; description: string; glyphs: string[] }[] = [
  { id: "full", label: "Full system", description: "Initials and finals in their standard Zhuyin order.", glyphs: [...zhuyinInitials, ...zhuyinFinals] },
  { id: "initials", label: "Initials", description: "The sharper consonant-bearing signs.", glyphs: [...zhuyinInitials] },
  { id: "finals", label: "Finals", description: "The rounder vowel and ending signs.", glyphs: [...zhuyinFinals] },
  { id: "tones", label: "Tone marks", description: "Five small directional accents.", glyphs: [...zhuyinTones] },
  { id: "custom", label: "Custom sequence", description: "A deliberate Zhuyin phrase, fragment, or reordered vocabulary.", glyphs: Array.from("ㄅㄆㄇㄈˊˇˋ˙") },
];

export const defaultZhuyinField = (): ZhuyinField => ({
  kind: "zhuyin",
  bank: "full",
  glyphs: [...zhuyinBanks[0].glyphs],
  mutationMode: "held",
  composition: "inlay",
  inkMode: "palette",
  inkColor: 0xf2eee7,
  groundColor: 0x151319,
});

export type TileField = {
  kind: "petscii-study";
  foregroundColor: number;
  backgroundColor: number;
};

export const petsciiPalette = [
  0x000000, 0xffffff, 0x813338, 0x75cec8,
  0x8e3c97, 0x56ac4d, 0x2e2c9b, 0xedf171,
  0x8e5029, 0x553800, 0xc46c71, 0x4a4a4a,
  0x7b7b7b, 0xa9ff9f, 0x706deb, 0xb2b2b2,
] as const;

export const defaultTileField = (): TileField => ({
  kind: "petscii-study",
  foregroundColor: petsciiPalette[14],
  backgroundColor: petsciiPalette[0],
});

export type EffectWhereMode = "whole" | "light" | "dark" | "edges" | "saturated" | "muted" | "hue" | "random" | "checker" | "stripes" | "blocks";
export type EffectWhere = {
  mode: EffectWhereMode;
  threshold: number;
  softness: number;
  hue: number;
  hueWidth: number;
  scale: number;
  invert: boolean;
  seed: number;
};

export const whereModes: { value: EffectWhereMode; label: string; description: string }[] = [
  { value: "whole", label: "Whole image", description: "" },
  { value: "light", label: "Light regions", description: "Protect shadows and enter brighter territory." },
  { value: "dark", label: "Dark regions", description: "Protect highlights and enter darker territory." },
  { value: "edges", label: "Outline / edges", description: "Follow contours and abrupt changes in image structure." },
  { value: "saturated", label: "Saturated regions", description: "Enter territories carrying stronger color." },
  { value: "muted", label: "Muted regions", description: "Enter colorless and restrained territories." },
  { value: "hue", label: "Hue family", description: "Gather one neighborhood of the color wheel." },
  { value: "random", label: "Random territory", description: "Choose recoverable scattered cells or clustered islands." },
  { value: "checker", label: "Checker", description: "Alternate protected and affected squares." },
  { value: "stripes", label: "Stripes", description: "Permit the process through alternating bands." },
  { value: "blocks", label: "Blocks", description: "Use a deterministic broken field of territories." },
];

export type LayerBlendMode = "normal" | "difference" | "overlay" | "hard-mix" | "screen" | "multiply" | "lighten" | "darken";
export type LayerMaskMode = "whole" | "checker" | "stripes" | "blocks" | "light" | "dark" | "edges";
export type StudioLayer = {
  id: string;
  label: string;
  filePath: string;
  enabled: boolean;
  opacity: number;
  blendMode: LayerBlendMode;
  maskMode: LayerMaskMode;
  maskScale: number;
  seed: number;
};

export type PaletteStructure =
  | "monochrome"
  | "duotone"
  | "analogous"
  | "complementary"
  | "split-complementary"
  | "triadic"
  | "source"
  | "custom";

export type PaletteSettings = {
  structure: PaletteStructure;
  hue: number;
  hueSpread: number;
  saturation: number;
  saturationRange: number;
  lightnessFloor: number;
  lightnessCeiling: number;
};

export const paletteStructures: { value: PaletteStructure; label: string; description: string }[] = [
  { value: "monochrome", label: "Monochrome", description: "One hue carried through a tonal ladder." },
  { value: "duotone", label: "Duotone", description: "Two hue families arguing across the image." },
  { value: "analogous", label: "Analogous", description: "Neighboring hues held inside a narrow weather system." },
  { value: "complementary", label: "Complementary", description: "A direct opposition across the color wheel." },
  { value: "split-complementary", label: "Split complementary", description: "One anchor facing two uneven opponents." },
  { value: "triadic", label: "Triadic", description: "Three equidistant signals with controlled intensity." },
  { value: "source", label: "Extracted from image", description: "Four colors sampled from the current source material." },
  { value: "custom", label: "Restricted custom", description: "The four swatches stay exactly as you set them." },
];

export type StudioRecipe = {
  schemaVersion: 1;
  revision: number;
  seed: number;
  colorSeed: number;
  iteration: number;
  renderSize: number;
  renderWidth: number;
  renderHeight: number;
  gifWidth: number;
  gifHeight: number;
  loopFrames: number;
  loopFps: number;
  aspectLocked: boolean;
  gifAspectLocked: boolean;
  sourceImage?: string;
  sourceFit: "cover" | "contain";
  colorMode: "source" | "palette";
  sourcePresence: number;
  paletteSettings: PaletteSettings;
  palette: [number, number, number, number];
  layers: StudioLayer[];
  effects: EffectInstance[];
};

export const effectDefinitions: EffectDefinition[] = [
  {
    type: "band-rupture", name: "Band Rupture", category: "Order",
    description: "Break horizontal memory into displaced bands and hard scars.",
    parameters: [
      { id: "rupture", label: "Rupture", description: "How far bands abandon alignment.", min: 0, max: 1, step: 0.01, default: 0.48 },
      { id: "bands", label: "Band Count", description: "Fewer creates slabs; more creates nervous strata.", min: 8, max: 160, step: 1, default: 72 },
      { id: "scar", label: "Scar Chance", description: "How often an interruption refuses the image.", min: 0, max: 1, step: 0.01, default: 0.24 },
      { id: "memory", label: "Retained Memory", description: "How strongly the source survives inside displaced bands.", min: 0, max: 1, step: 0.01, default: 0.72 },
    ],
  },
  {
    type: "wrong-sort", name: "Wrong Sort", category: "Order",
    description: "Sort only fragments, then deliberately abandon the rest.",
    parameters: [
      { id: "amount", label: "Completion", description: "How much of the image is allowed to become ordered.", min: 0, max: 1, step: 0.01, default: 0.42 },
      { id: "threshold", label: "Value Gate", description: "Which brightness territory is eligible to move.", min: 0, max: 1, step: 0.01, default: 0.32 },
      { id: "chunk", label: "Chunk", description: "The length of each local argument about order.", min: 4, max: 180, step: 1, default: 54 },
      { id: "direction", label: "Direction", description: "Horizontal or vertical sorting, forward or reversed.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] },
      { id: "channel", label: "Signal", description: "The channel whose value decides the order.", min: 0, max: 5, step: 1, default: 5, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness"] },
    ],
  },
  {
    type: "median-filter", name: "Median Filter", category: "Order",
    description: "Order every 3 × 3 neighborhood by one color signal: the median heals noise, while off-center ranks grow painterly smears.",
    parameters: [
      { id: "position", label: "Neighborhood Rank", description: "Choose which of the nine locally ordered pixels replaces the center. Four is the true median.", min: 0, max: 8, step: 1, default: 3, choices: ["Lowest", "Low 2", "Low 3", "Near-median low", "True median", "Near-median high", "High 3", "High 2", "Highest"] },
      { id: "channel", label: "Ordering Signal", description: "The color evidence used to order each neighborhood; inverted signals reverse its pressure.", min: 0, max: 11, step: 1, default: 11, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness", "Inverted red", "Inverted green", "Inverted blue", "Inverted hue", "Inverted saturation", "Inverted brightness"] },
      { id: "iterations", label: "Filter Passes", description: "Repeated passes let a subtle local choice spread into a larger liquid or brushed territory.", min: 1, max: 24, step: 1, default: 6 },
      { id: "blendMode", label: "Original Blend", description: "Optionally recombine the original image with the filtered result using the source sketch's blend logic.", min: 0, max: 6, step: 1, default: 0, choices: ["Filter only", "Overlay", "Hard light", "Screen", "Multiply", "Add", "Difference"] },
    ],
  },
  {
    type: "sorting-motion", name: "Sorting Motion", category: "Temporal",
    description: "Let a partial sorting method reach maximum order, release to the incoming image, and return in a seamless loop.",
    parameters: [
      { id: "method", label: "Method", description: "The temporal handwriting used to reorganize each fragment.", min: 0, max: 5, step: 1, default: 0, choices: ["Bubble", "Insertion", "Selection", "Merge", "Permute", "Roll"] },
      { id: "maximumOrder", label: "Maximum Order", description: "The strongest partial ordering reached at the loop boundary.", min: 0, max: 1, step: 0.01, default: 0.72 },
      { id: "span", label: "Fragment Span", description: "Length of each local interval allowed to negotiate a new order.", min: 8, max: 240, step: 1, default: 72 },
      { id: "channel", label: "Signal", description: "The color evidence that decides the order.", min: 0, max: 5, step: 1, default: 5, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness"] },
      { id: "direction", label: "Travel", description: "The spatial direction receiving the reorganized fragments.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] },
      { id: "reverse", label: "Order Direction", description: "Choose whether low or high signal values lead each fragment.", min: 0, max: 1, step: 1, default: 0, choices: ["Low leads", "High leads"] },
    ],
  },
  {
    type: "ultimate-sort", name: "Ultimate Sort", category: "Order",
    description: "Stack independent sorting, selection-wand, and resolution recipes so different territories obey different rules.",
    parameters: [],
  },
  {
    type: "wizprocess", name: "Wizprocess", category: "Signal",
    description: "",
    parameters: [],
  },
  {
    type: "pixel-drift", name: "Pixel Drift", category: "Decay",
    description: "Let neighboring pixels pull the image into directional spectral erosion.",
    parameters: [
      { id: "distance", label: "Drift Distance", description: "How far each iteration reaches for its neighbor.", min: 1, max: 42, step: 1, default: 9 },
      { id: "iterations", label: "Decay Passes", description: "How many times the image forgets its prior boundary.", min: 1, max: 18, step: 1, default: 4 },
      { id: "hueMemory", label: "Hue Memory", description: "How stubbornly hue resists the drift.", min: 0, max: 1, step: 0.01, default: 0.82 },
      { id: "lightMemory", label: "Light Memory", description: "How stubbornly brightness resists the drift.", min: 0, max: 1, step: 0.01, default: 0.38 },
      { id: "direction", label: "Direction", description: "The direction of the erosion current.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] },
    ],
  },
  {
    type: "signal-echo", name: "Signal Echo", category: "Signal",
    description: "Misregister color signal, scan phase, and remembered transmissions.",
    parameters: [
      { id: "separation", label: "Channel Separation", description: "Distance between the color ghosts.", min: 0, max: 64, step: 1, default: 13 },
      { id: "bleed", label: "Chroma Bleed", description: "How far color spills outside form.", min: 0, max: 1, step: 0.01, default: 0.54 },
      { id: "scan", label: "Scan Pressure", description: "Visibility and violence of scanning structure.", min: 0, max: 1, step: 0.01, default: 0.28 },
      { id: "ghost", label: "Ghost Memory", description: "Strength of the delayed image echo.", min: 0, max: 1, step: 0.01, default: 0.46 },
    ],
  },
  {
    type: "dither-field", name: "Dither Field", category: "Quantize",
    description: "Quantize channels into a granular threshold field.",
    parameters: [
      { id: "levels", label: "Color Steps", description: "How many signal levels remain available.", min: 2, max: 16, step: 1, default: 4 },
      { id: "grain", label: "Pixel Grain", description: "Scale of the threshold lattice.", min: 1, max: 12, step: 1, default: 2 },
      { id: "pressure", label: "Error Pressure", description: "How strongly threshold error marks the result.", min: 0, max: 1, step: 0.01, default: 0.68 },
      { id: "channelOffset", label: "Channel Offset", description: "Separates the red and blue threshold fields.", min: 0, max: 12, step: 1, default: 2 },
    ],
  },
  {
    type: "lens-warp", name: "Lens Warp", category: "Spatial",
    description: "Use the image's own signal as a lens that bends its coordinates.",
    parameters: [
      { id: "bendX", label: "Horizontal Bend", description: "How much signal displaces the horizontal axis.", min: 0, max: 1, step: 0.01, default: 0.22 },
      { id: "bendY", label: "Vertical Bend", description: "How much signal displaces the vertical axis.", min: 0, max: 1, step: 0.01, default: 0.14 },
      { id: "frequency", label: "Lens Frequency", description: "How often the lens changes its mind across the image.", min: 0.2, max: 12, step: 0.1, default: 3.4 },
      { id: "mode", label: "Lens Shape", description: "Linear, sinusoidal, or polar coordinate pressure.", min: 0, max: 2, step: 1, default: 1, choices: ["Linear", "Sinusoidal", "Polar"] },
    ],
  },
  {
    type: "mirror-cut", name: "Mirror Cut", category: "Fold",
    description: "Fold axes and diagonals into asymmetric copied architecture.",
    parameters: [
      { id: "mode", label: "Fold", description: "Axis, diagonal, shifted, or kaleidoscopic copy.", min: 0, max: 5, step: 1, default: 2, choices: ["Left", "Right", "Top", "Bottom", "Diagonal", "Shifted"] },
      { id: "offset", label: "Cut Offset", description: "Where the copied structure stops obeying symmetry.", min: -1, max: 1, step: 0.01, default: 0.16 },
      { id: "mix", label: "Fold Memory", description: "Balance between the prior image and its folded replacement.", min: 0, max: 1, step: 0.01, default: 0.74 },
    ],
  },
  {
    type: "motion-leak", name: "Motion Leak", category: "Temporal",
    description: "Make a still misremember itself as damaged predictive video blocks.",
    parameters: [
      { id: "block", label: "Prediction Block", description: "Size of the false codec memory units.", min: 4, max: 64, step: 2, default: 16 },
      { id: "vector", label: "Motion Vector", description: "How far a block reaches into the wrong remembered place.", min: 0, max: 96, step: 1, default: 28 },
      { id: "leak", label: "Reference Leak", description: "How many blocks accept the false prediction.", min: 0, max: 1, step: 0.01, default: 0.58 },
      { id: "residual", label: "Residual Memory", description: "How much of the current image survives over predicted blocks.", min: 0, max: 1, step: 0.01, default: 0.34 },
      { id: "coherence", label: "Vector Coherence", description: "From granular block noise to a shared directional failure.", min: 0, max: 1, step: 0.01, default: 0.67 },
    ],
  },
  {
    type: "resolution-quilt", name: "Resolution Quilt", category: "Spatial",
    description: "Build one image from unequal territories of sharp, soft, and broken resolution.",
    parameters: [
      { id: "minChunk", label: "Smallest Chunk", description: "The smallest local territory allowed to retain its own resolution.", min: 4, max: 160, step: 1, default: 18 },
      { id: "maxChunk", label: "Largest Chunk", description: "The largest slab that can interrupt the finer field.", min: 16, max: 480, step: 1, default: 180 },
      { id: "resolutionDrop", label: "Resolution Drop", description: "How aggressively regions collapse into fewer pixels.", min: 0, max: 1, step: 0.01, default: 0.64 },
      { id: "softness", label: "Soft Enlargement", description: "From hard pixel edges to blurred resampling.", min: 0, max: 1, step: 0.01, default: 0.32 },
      { id: "displacement", label: "Block Travel", description: "How far resampled territories leave their original coordinates.", min: 0, max: 1, step: 0.01, default: 0.18 },
      { id: "vacancy", label: "Missing Territory", description: "How often a region becomes deliberate absence.", min: 0, max: 1, step: 0.01, default: 0.08 },
    ],
  },
  {
    type: "shard-field", name: "Shard Field", category: "Spatial",
    description: "Detach rectangular pieces, rotate them, repeat them, and leave the image structurally incomplete.",
    parameters: [
      { id: "pieces", label: "Piece Count", description: "How many pieces negotiate a new arrangement.", min: 3, max: 140, step: 1, default: 34 },
      { id: "minSpan", label: "Smallest Piece", description: "Minimum piece size as a fraction of the image.", min: 0.01, max: 0.3, step: 0.01, default: 0.04 },
      { id: "maxSpan", label: "Largest Piece", description: "Maximum piece size as a fraction of the image.", min: 0.05, max: 0.85, step: 0.01, default: 0.28 },
      { id: "travel", label: "Shard Travel", description: "How far detached pieces can abandon their source.", min: 0, max: 1, step: 0.01, default: 0.24 },
      { id: "rotation", label: "Rotation", description: "Angular instability of detached pieces.", min: 0, max: 1, step: 0.01, default: 0.12 },
      { id: "repetition", label: "Repetition", description: "Chance that one piece echoes into another position.", min: 0, max: 1, step: 0.01, default: 0.22 },
      { id: "absence", label: "Absence", description: "Chance that a detached region refuses replacement.", min: 0, max: 1, step: 0.01, default: 0.12 },
    ],
  },
  {
    type: "cut-repeat", name: "Cut / Repeat", category: "Order",
    description: "Select strips by signal, stretch them, repeat them, and cut holes in the expected sequence.",
    parameters: [
      { id: "selector", label: "Selection Signal", description: "Which image evidence decides what can be cut.", min: 0, max: 3, step: 1, default: 3, choices: ["Bright", "Dark", "Edges", "Chance"] },
      { id: "cuts", label: "Cut Count", description: "Number of candidate fragments.", min: 2, max: 120, step: 1, default: 26 },
      { id: "span", label: "Cut Span", description: "Typical width of selected material.", min: 0.01, max: 0.5, step: 0.01, default: 0.12 },
      { id: "stretch", label: "Stretch", description: "How far a fragment changes proportion.", min: 0, max: 1, step: 0.01, default: 0.38 },
      { id: "repetition", label: "Repeat Count", description: "How many echoes a chosen fragment may produce.", min: 1, max: 12, step: 1, default: 4 },
      { id: "drift", label: "Sequence Drift", description: "Distance between repeated fragments.", min: 0, max: 1, step: 0.01, default: 0.16 },
      { id: "absence", label: "Cut Away", description: "How often selection produces a gap rather than a copy.", min: 0, max: 1, step: 0.01, default: 0.14 },
    ],
  },
  {
    type: "ascii-field", name: "ASCII Field", category: "Character",
    description: "Build a pure character field or replace selected image territories with an exact ASCII pattern.",
    parameters: [
      { id: "cellSize", label: "Cell Size", description: "The scale of each character cell, held proportionally across preview and export.", min: 7, max: 56, step: 1, default: 15 },
      { id: "coverage", label: "Pattern Fill", description: "How many cells inside the chosen territory print a character; silent cells retain the chosen ground.", min: 0, max: 1, step: 0.01, default: 1 },
      { id: "imageLoyalty", label: "Mass Fidelity", description: "How faithfully character weight rebuilds the source image's light and dark masses.", min: 0, max: 1, step: 0.01, default: 0.88 },
      { id: "edgeVoice", label: "Contour Voice", description: "How strongly directional ASCII strokes draw boundaries through the pattern.", min: 0, max: 1, step: 0.01, default: 0.28 },
      { id: "instability", label: "Alphabet Instability", description: "Legacy character mutation retained for older recipes.", min: 0, max: 1, step: 0.01, default: 0 },
      { id: "vacancy", label: "Vacancy", description: "Legacy random silence retained for older recipes.", min: 0, max: 0.9, step: 0.01, default: 0 },
      { id: "gridDamage", label: "Grid Damage", description: "Legacy grid displacement retained for older recipes.", min: 0, max: 1, step: 0.01, default: 0 },
      { id: "invertDensity", label: "Density", description: "Choose whether dark or light regions carry the heaviest marks.", min: 0, max: 1, step: 1, default: 0, choices: ["Dark is dense", "Light is dense"] },
    ],
  },
  {
    type: "zhuyin-weave", name: "Zhuyin Weave", category: "Character",
    description: "Layer patterned Zhuyin signs as woven ink inside selected image territories.",
    parameters: [
      { id: "cellSize", label: "Cell Size", description: "The scale of the repeating Zhuyin cell.", min: 9, max: 64, step: 1, default: 22 },
      { id: "coverage", label: "Pattern Fill", description: "How many cells inside the chosen territory receive the weave.", min: 0, max: 1, step: 0.01, default: 0.82 },
      { id: "voices", label: "Voices", description: "How many related symbol layers inhabit the same territory.", min: 1, max: 4, step: 1, default: 2 },
      { id: "misregistration", label: "Misregistration", description: "How far the layered voices slip apart like imperfect printing.", min: 0, max: 1, step: 0.01, default: 0.22 },
      { id: "rowDrift", label: "Row Drift", description: "How strongly each row advances through the symbol sequence.", min: 0, max: 1, step: 0.01, default: 0.42 },
      { id: "imageRhythm", label: "Image Rhythm", description: "How much source brightness bends the repeating symbol phase.", min: 0, max: 1, step: 0.01, default: 0.38 },
      { id: "motion", label: "Loop Motion", description: "How far row phase and layered registration travel during a closed loop.", min: 0, max: 1, step: 0.01, default: 0.32 },
    ],
  },
  {
    type: "petscii-study", name: "PETSCII Study", category: "Character",
    description: "Rebuild the complete image from a fixed 40 × 25 vocabulary of quadrant tiles.",
    parameters: [
      { id: "threshold", label: "Tile Threshold", description: "Which sampled quadrants become foreground tile mass.", min: 0.05, max: 0.95, step: 0.01, default: 0.48 },
      { id: "imagePull", label: "Image Pull", description: "From one shared ink color to the nearest C64-inspired color in each cell.", min: 0, max: 1, step: 0.01, default: 0.78 },
      { id: "reverseMass", label: "Mass Direction", description: "Choose whether dark or light source mass becomes the foreground tile.", min: 0, max: 1, step: 1, default: 0, choices: ["Dark becomes tile", "Light becomes tile"] },
    ],
  },
];

export const definitionFor = (type: EffectType) => effectDefinitions.find((item) => item.type === type)!;

let instanceCounter = 0;
export function defaultWhere(seed = 0): EffectWhere {
  return { mode: "whole", threshold: 0.5, softness: 0.12, hue: 0, hueWidth: 36, scale: 48, invert: false, seed: Math.max(0, Math.round(seed)) };
}

export function createEffect(type: EffectType, seed = Date.now()): EffectInstance {
  const definition = definitionFor(type);
  const random = randomSource(seed + instanceCounter++ * 997);
  const effect: EffectInstance = {
    id: `${type}-${Math.floor(random() * 0xffffff).toString(16).padStart(6, "0")}`,
    type,
    enabled: true,
    where: defaultWhere(seed + instanceCounter * 7919),
    parameters: Object.fromEntries(definition.parameters.map((parameter) => [parameter.id, parameter.default])),
  };
  if (type === "ascii-field") effect.characterField = defaultCharacterField();
  if (type === "zhuyin-weave") effect.zhuyinField = defaultZhuyinField();
  if (type === "petscii-study") effect.tileField = defaultTileField();
  if (type === "ultimate-sort") effect.ultimateSort = defaultUltimateSortStack();
  if (type === "wizprocess") effect.wizprocess = defaultWizprocess();
  return effect;
}

export const defaultPaletteSettings = (): PaletteSettings => ({
  structure: "analogous",
  hue: 22,
  hueSpread: 34,
  saturation: 28,
  saturationRange: 18,
  lightnessFloor: 8,
  lightnessCeiling: 94,
});

export const defaultRecipe = (): StudioRecipe => {
  const paletteSettings = defaultPaletteSettings();
  return {
  schemaVersion: 1,
  revision: 1,
  seed: 886,
  colorSeed: 886042,
  iteration: 0,
  renderSize: 1600,
  renderWidth: 1600,
  renderHeight: 1600,
  gifWidth: 960,
  gifHeight: 960,
  loopFrames: 36,
  loopFps: 12,
  aspectLocked: true,
  gifAspectLocked: true,
  sourceFit: "contain",
  colorMode: "palette",
  sourcePresence: 0,
  paletteSettings,
  palette: paletteFromSettings(paletteSettings),
  layers: [],
  effects: [createEffect("band-rupture", 886), createEffect("signal-echo", 887)],
  };
};

export function randomSource(seed: number) {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export function nextStructure(recipe: StudioRecipe): StudioRecipe {
  const seed = Math.floor(Math.random() * 2_000_000_000);
  const random = randomSource(seed);
  return {
    ...recipe,
    revision: recipe.revision + 1,
    seed,
    iteration: 0,
    effects: recipe.effects.map((effect) => {
      const wizprocess = effect.type === "wizprocess" ? effect.wizprocess : undefined;
      const mutateWhere = !wizprocess || wizprocess.newStructureWhere;
      return {
      ...effect,
      where: mutateWhere ? {
          ...effect.where,
          mode: whereModes[Math.floor(random() * whereModes.length)].value,
          threshold: Number(random().toFixed(2)),
          softness: Number((random() * 0.32).toFixed(2)),
          hue: Math.round(random() * 359),
          hueWidth: Math.round(8 + random() * 112),
          scale: Math.round(8 + random() * 152),
          invert: random() > 0.72,
          seed: Math.floor(random() * 2_000_000_000),
        } : effect.where,
        parameters: Object.fromEntries(definitionFor(effect.type).parameters.map((parameter) => {
        if (parameter.choices) return [parameter.id, Math.floor(random() * parameter.choices.length)];
        const raw = parameter.min + random() * (parameter.max - parameter.min);
        const stepped = Math.round(raw / parameter.step) * parameter.step;
        return [parameter.id, Number(stepped.toFixed(parameter.step < 0.1 ? 2 : parameter.step < 1 ? 1 : 0))];
      })),
        wizprocess: wizprocess ? {
          ...wizprocess,
          ...(wizprocess.newStructureScale ? {
            mass: Number((0.05 + random() * 0.95).toFixed(2)),
            structure: Number((0.05 + random() * 0.95).toFixed(2)),
            grain: Number((0.05 + random() * 0.95).toFixed(2)),
          } : {}),
          compression: Math.round(4 + random() * 276),
          expansion: Math.round(4 + random() * 276),
          path: (["rows", "columns", "snake", "clustered"] as Wizprocess["path"][])[Math.floor(random() * 4)],
          tide: Number(random().toFixed(2)),
        } : undefined,
      };
    }),
  };
}

export function nextIteration(recipe: StudioRecipe): StudioRecipe {
  return { ...recipe, revision: recipe.revision + 1, iteration: recipe.iteration + 1 };
}

export function mutateZhuyinSequence(
  glyphs: string[],
  seed: number,
  iteration: number,
  mode: ZhuyinField["mutationMode"],
) {
  const mutated = glyphs.length ? [...glyphs] : ["ㄅ"];
  if (mode === "held") return mutated;
  const original = [...mutated];
  const random = randomSource(seed + iteration * 104729 + mutated.length * 8191);
  const edits = mode === "drift" ? 1 : Math.min(8, Math.max(3, Math.ceil(mutated.length * 0.12)));

  for (let edit = 0; edit < edits; edit += 1) {
    const operation = Math.floor(random() * 4);
    const index = Math.floor(random() * mutated.length);
    if ((operation === 0 || (operation === 1 && mutated.length >= 64)) && mutated.length > 1) {
      const other = (index + 1 + Math.floor(random() * (mutated.length - 1))) % mutated.length;
      [mutated[index], mutated[other]] = [mutated[other], mutated[index]];
    } else if (operation === 1 && mutated.length < 64) {
      mutated.splice(index + 1, 0, mutated[index]);
    } else if (operation === 2 && mutated.length > 1) {
      mutated.splice(index, 1);
    } else if (mutated.length >= 64) {
      mutated.splice(index, 1);
    } else if (mutated.length < 64) {
      const clusterSize = Math.min(64 - mutated.length, mode === "fracture" ? 2 + Math.floor(random() * 3) : 1);
      mutated.splice(index, 0, ...Array.from({ length: clusterSize }, () => mutated[index]));
    }
  }

  const result = mutated.slice(0, 64);
  if (result.length === original.length && result.every((glyph, index) => glyph === original[index])) {
    if (result.length < 64) result.splice(1, 0, result[0]);
    else result.splice(Math.floor(random() * result.length), 1);
  }
  return result;
}

export function nextZhuyinIteration(recipe: StudioRecipe): StudioRecipe {
  const iteration = recipe.iteration + 1;
  return {
    ...recipe,
    revision: recipe.revision + 1,
    iteration,
    effects: recipe.effects.map((effect) => {
      const field = effect.type === "zhuyin-weave" ? effect.zhuyinField : undefined;
      if (!field || field.mutationMode === "held") return effect;
      return {
        ...effect,
        zhuyinField: {
          ...field,
          bank: "custom",
          glyphs: mutateZhuyinSequence(field.glyphs, recipe.seed + effect.where.seed, iteration, field.mutationMode),
        },
      };
    }),
  };
}

export function cleanPassRecipe(recipe: StudioRecipe, sourceImage: string): StudioRecipe {
  return {
    ...recipe,
    revision: recipe.revision + 1,
    seed: Math.floor(Math.random() * 2_000_000_000),
    iteration: 0,
    sourceImage,
    colorMode: "source",
    sourcePresence: 0.18,
    layers: [],
    effects: [createEffect("resolution-quilt", recipe.seed + recipe.revision)],
  };
}

export function parameterPrecision(step: number) {
  if (step >= 1) return 0;
  return Math.min(6, Math.max(1, Math.ceil(-Math.log10(step))));
}

export function parameterSuggestions(parameter: EffectParameter): ParameterSuggestion[] {
  if (parameter.suggestions) return parameter.suggestions;
  if (parameter.choices) return parameter.choices.map((label, value) => ({ value, label }));
  const labels = ["minimum", "trace", "low", "turn", "strong", "break", "maximum"];
  const positions = [0, 0.08, 0.2, 0.4, 0.62, 0.82, 1];
  const precision = parameterPrecision(parameter.step);
  const values = positions.map((position) => {
    const raw = parameter.min + (parameter.max - parameter.min) * position;
    const stepped = Math.round((raw - parameter.min) / parameter.step) * parameter.step + parameter.min;
    return Number(stepped.toFixed(precision));
  });
  return values.filter((value, index) => values.indexOf(value) === index).map((value, index, unique) => ({
    value,
    label: labels[Math.round(index * (labels.length - 1) / Math.max(1, unique.length - 1))],
  }));
}

function hslToPacked(h: number, s: number, l: number) {
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) => {
    const k = (n + h * 12) % 12;
    return l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
  };
  return (Math.round(f(0) * 255) << 16) | (Math.round(f(8) * 255) << 8) | Math.round(f(4) * 255);
}

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const wrapHue = (value: number) => ((value % 360) + 360) % 360;

export function paletteFromSettings(settings: PaletteSettings): [number, number, number, number] {
  const hue = wrapHue(settings.hue);
  const spread = clamp(settings.hueSpread, 0, 180);
  const hueOffsets: Record<Exclude<PaletteStructure, "source" | "custom">, number[]> = {
    monochrome: [0, 0, 0, 0],
    duotone: [0, spread, spread, 0],
    analogous: [-spread, -spread / 3, spread / 3, spread],
    complementary: [0, 180, 180, 0],
    "split-complementary": [0, 180 - spread / 2, 180 + spread / 2, 0],
    triadic: [0, 120, 240, 0],
  };
  const offsets = hueOffsets[settings.structure as keyof typeof hueOffsets] ?? [0, 0, 0, 0];
  const saturation = clamp(settings.saturation, 0, 100);
  const saturationRange = clamp(settings.saturationRange, 0, 100);
  const floor = clamp(Math.min(settings.lightnessFloor, settings.lightnessCeiling), 0, 100);
  const ceiling = clamp(Math.max(settings.lightnessFloor, settings.lightnessCeiling), 0, 100);
  const lightSpan = ceiling - floor;
  const lightness = [floor + lightSpan * 0.24, floor + lightSpan * 0.5, floor + lightSpan * 0.74, ceiling];
  const saturationOffsets = [-saturationRange * 0.28, saturationRange * 0.18, saturationRange * 0.5, -saturationRange * 0.72];
  return offsets.map((offset, index) => hslToPacked(
    wrapHue(hue + offset) / 360,
    clamp(saturation + saturationOffsets[index], 0, 100) / 100,
    lightness[index] / 100,
  )) as [number, number, number, number];
}

export function applyPaletteSettings(recipe: StudioRecipe, patch: Partial<PaletteSettings>): StudioRecipe {
  const paletteSettings = { ...recipe.paletteSettings, ...patch };
  if (paletteSettings.lightnessFloor > paletteSettings.lightnessCeiling) {
    if (patch.lightnessFloor !== undefined) paletteSettings.lightnessCeiling = paletteSettings.lightnessFloor;
    else paletteSettings.lightnessFloor = paletteSettings.lightnessCeiling;
  }
  const preserveSwatches = paletteSettings.structure === "custom" || paletteSettings.structure === "source";
  return {
    ...recipe,
    revision: recipe.revision + 1,
    paletteSettings,
    palette: preserveSwatches ? recipe.palette : paletteFromSettings(paletteSettings),
  };
}

export function nextColors(recipe: StudioRecipe): StudioRecipe {
  const colorSeed = Math.floor(Math.random() * 2_000_000_000);
  const random = randomSource(colorSeed);
  const effects: EffectInstance[] = recipe.effects.map((effect): EffectInstance => {
    const wizprocess = effect.type === "wizprocess" ? effect.wizprocess : undefined;
    if (!wizprocess?.newColors) return effect;
    const channels = random() > 0.5 ? "together" : "separate";
    return {
      ...effect,
      wizprocess: {
        ...wizprocess,
        colorSpace: (random() > 0.5 ? "hsb" : "rgb") as Wizprocess["colorSpace"],
        channels: channels as Wizprocess["channels"],
        channelPhase: channels === "together" ? Math.round(random() * 24 - 12) : 0,
        reconstruction: (["fold", "wrap", "clip", "reflect"] as Wizprocess["reconstruction"][])[Math.floor(random() * 4)],
      },
    };
  });
  if (recipe.paletteSettings.structure !== "custom" && recipe.paletteSettings.structure !== "source") {
    const paletteSettings = { ...recipe.paletteSettings, hue: Math.round(random() * 359) };
    return {
      ...recipe,
      revision: recipe.revision + 1,
      colorSeed,
      paletteSettings,
      palette: paletteFromSettings(paletteSettings),
      effects,
    };
  }
  const base = random();
  const relation = [0.08 + random() * 0.1, 0.38 + random() * 0.18, 0.62 + random() * 0.24];
  return {
    ...recipe,
    revision: recipe.revision + 1,
    colorSeed,
    effects,
    paletteSettings: { ...recipe.paletteSettings, structure: "custom" },
    palette: [
      hslToPacked(base, 0.2 + random() * 0.48, 0.24 + random() * 0.34),
      hslToPacked((base + relation[0]) % 1, 0.16 + random() * 0.46, 0.28 + random() * 0.38),
      hslToPacked((base + relation[1]) % 1, 0.12 + random() * 0.42, 0.42 + random() * 0.38),
      hslToPacked((base + relation[2]) % 1, 0.03 + random() * 0.18, 0.02 + random() * 0.14),
    ],
  };
}

function normalizeUltimateSortStack(stack: UltimateSortStack | undefined): UltimateSortStack {
  const fallback = defaultUltimateSortStack();
  const incoming = Array.isArray(stack?.recipes) && stack.recipes.length ? stack.recipes.slice(0, 12) : fallback.recipes;
  const methods = ["bubble", "insertion", "selection", "merge", "permute", "roll"];
  const actions = ["sort", "sort-outline", "wand"];
  const directions = ["left", "right", "up", "down"];
  const signals = ["red", "green", "blue", "hue", "saturation", "brightness"];
  const territories = ["whole", "light", "dark", "edges", "red", "orange", "yellow", "green", "cyan", "blue", "pink"];
  const resolutions = ["pixel", "fixed", "wake"];
  return {
    kind: "ultimate-sort",
    recipes: incoming.map((recipe, index) => {
      const base = fallback.recipes[index] ?? defaultUltimateSortRecipe(index);
      const minBlock = Math.max(1, Math.min(32, Math.round(Number(recipe.minBlock ?? base.minBlock))));
      return {
        ...base,
        ...recipe,
        id: String(recipe.id ?? `sort-recipe-${index + 1}`),
        enabled: recipe.enabled !== false,
        method: (methods.includes(recipe.method) ? recipe.method : base.method) as UltimateSortRecipe["method"],
        amount: Math.max(0, Math.min(1, Number(recipe.amount ?? base.amount))),
        action: (actions.includes(recipe.action) ? recipe.action : base.action) as UltimateSortRecipe["action"],
        direction: (directions.includes(recipe.direction) ? recipe.direction : base.direction) as UltimateSortRecipe["direction"],
        signal: (signals.includes(recipe.signal) ? recipe.signal : base.signal) as UltimateSortRecipe["signal"],
        territory: (territories.includes(recipe.territory) ? recipe.territory : base.territory) as UltimateSortRecipe["territory"],
        gate: Math.max(0, Math.min(1200, Number(recipe.gate ?? base.gate))),
        resolution: (resolutions.includes(recipe.resolution) ? recipe.resolution : base.resolution) as UltimateSortRecipe["resolution"],
        minBlock,
        maxBlock: Math.max(minBlock, Math.min(32, Math.round(Number(recipe.maxBlock ?? base.maxBlock)))),
        selectionSpeed: Math.max(0, Math.min(12, Math.round(Number(recipe.selectionSpeed ?? base.selectionSpeed)))),
      };
    }),
  };
}

function normalizeWizprocess(chamber: Wizprocess | undefined): Wizprocess {
  const fallback = defaultWizprocess();
  const colorSpaces = ["rgb", "hsb"];
  const channels = ["together", "separate"];
  const paths = ["rows", "columns", "snake", "clustered"];
  const reconstructions = ["fold", "wrap", "clip", "reflect"];
  return {
    ...fallback,
    ...(chamber ?? {}),
    kind: "wizprocess",
    mass: Math.max(0, Math.min(1, Number(chamber?.mass ?? fallback.mass))),
    structure: Math.max(0, Math.min(1, Number(chamber?.structure ?? fallback.structure))),
    grain: Math.max(0, Math.min(1, Number(chamber?.grain ?? fallback.grain))),
    compression: Math.max(1, Math.min(1200, Number(chamber?.compression ?? fallback.compression))),
    expansion: Math.max(0, Math.min(1200, Number(chamber?.expansion ?? fallback.expansion))),
    colorSpace: (colorSpaces.includes(chamber?.colorSpace ?? "") ? chamber!.colorSpace : fallback.colorSpace) as Wizprocess["colorSpace"],
    channels: (channels.includes(chamber?.channels ?? "") ? chamber!.channels : fallback.channels) as Wizprocess["channels"],
    channelPhase: Math.max(-48, Math.min(48, Math.round(Number(chamber?.channelPhase ?? fallback.channelPhase)))),
    path: (paths.includes(chamber?.path ?? "") ? chamber!.path : fallback.path) as Wizprocess["path"],
    reconstruction: (reconstructions.includes(chamber?.reconstruction ?? "") ? chamber!.reconstruction : fallback.reconstruction) as Wizprocess["reconstruction"],
    tide: Math.max(0, Math.min(1, Number(chamber?.tide ?? fallback.tide))),
    newStructureScale: chamber?.newStructureScale !== false,
    newStructureWhere: chamber?.newStructureWhere !== false,
    newColors: chamber?.newColors !== false,
  };
}

export function normalizeRecipe(value: Partial<StudioRecipe> | null | undefined): StudioRecipe {
  const fallback = defaultRecipe();
  if (!value || value.schemaVersion !== 1 || !Array.isArray(value.effects)) return fallback;
  const legacySize = Math.max(320, Math.min(3840, Math.round(value.renderSize ?? fallback.renderSize)));
  const renderWidth = Math.max(320, Math.min(3840, Math.round(value.renderWidth ?? legacySize)));
  const renderHeight = Math.max(320, Math.min(3840, Math.round(value.renderHeight ?? legacySize)));
  const legacyGifScale = Math.min(1, 960 / Math.max(renderWidth, renderHeight));
  const gifWidth = Math.max(64, Math.min(3840, Math.round(value.gifWidth ?? renderWidth * legacyGifScale)));
  const gifHeight = Math.max(64, Math.min(3840, Math.round(value.gifHeight ?? renderHeight * legacyGifScale)));
  return {
    ...fallback,
    ...value,
    iteration: Math.max(0, Math.round(value.iteration ?? fallback.iteration)),
    renderSize: Math.max(renderWidth, renderHeight),
    renderWidth,
    renderHeight,
    gifWidth,
    gifHeight,
    loopFrames: Math.max(2, Math.min(240, Math.round(Number(value.loopFrames ?? fallback.loopFrames)))),
    loopFps: Math.max(1, Math.min(30, Math.round(Number(value.loopFps ?? fallback.loopFps)))),
    aspectLocked: value.aspectLocked !== false,
    gifAspectLocked: value.gifAspectLocked !== false,
    sourceFit: "contain",
    colorMode: value.colorMode === "source" ? "source" : "palette",
    sourcePresence: Math.max(0, Math.min(1, Number(value.sourcePresence ?? fallback.sourcePresence))),
    paletteSettings: value.paletteSettings ? {
      ...fallback.paletteSettings,
      ...value.paletteSettings,
      structure: paletteStructures.some((item) => item.value === value.paletteSettings?.structure)
        ? value.paletteSettings.structure
        : fallback.paletteSettings.structure,
    } : { ...fallback.paletteSettings, structure: "custom" },
    palette: Array.isArray(value.palette) && value.palette.length === 4 ? value.palette.map((color) => Math.max(0, Math.min(0xffffff, Math.round(color)))) as StudioRecipe["palette"] : fallback.palette,
    layers: Array.isArray(value.layers) ? value.layers.filter((layer) => layer && typeof layer.filePath === "string").map((layer) => ({
      id: String(layer.id ?? `layer-${Date.now()}`),
      label: String(layer.label ?? "Layer"),
      filePath: layer.filePath,
      enabled: layer.enabled !== false,
      opacity: Math.max(0, Math.min(1, Number(layer.opacity ?? 1))),
      blendMode: (["normal", "difference", "overlay", "hard-mix", "screen", "multiply", "lighten", "darken"].includes(layer.blendMode) ? layer.blendMode : "normal") as LayerBlendMode,
      maskMode: (["whole", "checker", "stripes", "blocks", "light", "dark", "edges"].includes(layer.maskMode) ? layer.maskMode : "whole") as LayerMaskMode,
      maskScale: Math.max(2, Math.min(240, Number(layer.maskScale ?? 48))),
      seed: Math.max(0, Math.round(Number(layer.seed ?? value.seed ?? fallback.seed))),
    })) : [],
    effects: value.effects.map((effect) => {
      if ((effect as unknown as { type: string }).type !== "wavelet-chamber") return effect;
      const legacy = effect as unknown as Omit<EffectInstance, "type"> & { type: string; waveletChamber?: Wizprocess };
      const { waveletChamber, ...rest } = legacy;
      return { ...rest, type: "wizprocess" as const, wizprocess: legacy.wizprocess ?? waveletChamber };
    }).filter((effect) => effectDefinitions.some((definition) => definition.type === effect.type)).map((effect) => {
      const base = createEffect(effect.type, value.seed);
      const incomingWhere = effect.where;
      return {
        ...base,
        ...effect,
        where: {
          ...base.where,
          ...(incomingWhere ?? {}),
          mode: (whereModes.some((item) => item.value === incomingWhere?.mode) ? incomingWhere?.mode : "whole") as EffectWhereMode,
          threshold: Math.max(0, Math.min(1, Number(incomingWhere?.threshold ?? base.where.threshold))),
          softness: Math.max(0, Math.min(0.5, Number(incomingWhere?.softness ?? base.where.softness))),
          hue: Math.max(0, Math.min(359, Math.round(Number(incomingWhere?.hue ?? base.where.hue)))),
          hueWidth: Math.max(1, Math.min(180, Math.round(Number(incomingWhere?.hueWidth ?? base.where.hueWidth)))),
          scale: Math.max(2, Math.min(240, Math.round(Number(incomingWhere?.scale ?? base.where.scale)))),
          invert: incomingWhere?.invert === true,
          seed: Math.max(0, Math.round(Number(incomingWhere?.seed ?? base.where.seed))),
        },
        parameters: { ...base.parameters, ...effect.parameters },
        characterField: effect.type === "ascii-field" ? {
          ...defaultCharacterField(),
          ...(effect.characterField ?? {}),
          kind: "ascii",
          composition: (["field", "inlay"].includes(effect.characterField?.composition ?? "") ? effect.characterField!.composition : "field") as CharacterField["composition"],
          glyphLogic: (["mass", "repeat"].includes(effect.characterField?.glyphLogic ?? "") ? effect.characterField!.glyphLogic : "mass") as CharacterField["glyphLogic"],
          bank: asciiBanks.some((bank) => bank.id === effect.characterField?.bank) ? effect.characterField!.bank : "density",
          glyphs: Array.isArray(effect.characterField?.glyphs) && effect.characterField!.glyphs.length
            ? effect.characterField!.glyphs.map((glyph) => String(glyph)).filter((glyph) => glyph.length > 0).slice(0, 64)
            : [...asciiBanks[0].glyphs],
          inkMode: (["source", "palette", "chosen"].includes(effect.characterField?.inkMode ?? "") ? effect.characterField!.inkMode : "source") as CharacterField["inkMode"],
          inkColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.characterField?.inkColor ?? 0xf2eee7)))),
          groundColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.characterField?.groundColor ?? 0x151319)))),
        } : undefined,
        zhuyinField: effect.type === "zhuyin-weave" ? {
          ...defaultZhuyinField(),
          ...(effect.zhuyinField ?? {}),
          kind: "zhuyin",
          composition: (["field", "inlay"].includes(effect.zhuyinField?.composition ?? "") ? effect.zhuyinField!.composition : "inlay") as ZhuyinField["composition"],
          bank: zhuyinBanks.some((bank) => bank.id === effect.zhuyinField?.bank) ? effect.zhuyinField!.bank : "full",
          glyphs: Array.isArray(effect.zhuyinField?.glyphs) && effect.zhuyinField!.glyphs.length
            ? effect.zhuyinField!.glyphs.map((glyph) => String(glyph)).filter((glyph) => glyph.length > 0).slice(0, 64)
            : [...zhuyinBanks[0].glyphs],
          mutationMode: (["held", "drift", "fracture"].includes(effect.zhuyinField?.mutationMode ?? "")
            ? effect.zhuyinField!.mutationMode
            : "held") as ZhuyinField["mutationMode"],
          inkMode: (["source", "palette", "chosen"].includes(effect.zhuyinField?.inkMode ?? "") ? effect.zhuyinField!.inkMode : "palette") as ZhuyinField["inkMode"],
          inkColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.zhuyinField?.inkColor ?? 0xf2eee7)))),
          groundColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.zhuyinField?.groundColor ?? 0x151319)))),
        } : undefined,
        tileField: effect.type === "petscii-study" ? {
          ...defaultTileField(),
          ...(effect.tileField ?? {}),
          kind: "petscii-study",
          foregroundColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.tileField?.foregroundColor ?? petsciiPalette[14])))),
          backgroundColor: Math.max(0, Math.min(0xffffff, Math.round(Number(effect.tileField?.backgroundColor ?? petsciiPalette[0])))),
        } : undefined,
        ultimateSort: effect.type === "ultimate-sort" ? normalizeUltimateSortStack(effect.ultimateSort) : undefined,
        wizprocess: effect.type === "wizprocess" ? normalizeWizprocess(effect.wizprocess) : undefined,
      };
    }),
  };
}
