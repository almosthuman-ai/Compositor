var TempleEngine = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // local/glitch-build/bridge.ts
  var bridge_exports = {};
  __export(bridge_exports, {
    catalog: () => catalog,
    normalize: () => normalize,
    palette: () => palette,
    render: () => render,
    vary: () => vary
  });

  // local/glitch-build/studio.ts
  var defaultWizprocess = () => ({
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
    newColors: true
  });
  var ultimateRecipeCounter = 0;
  var defaultUltimateSortRecipe = (seed = Date.now()) => ({
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
    selectionSpeed: 3
  });
  var defaultUltimateSortStack = () => ({
    kind: "ultimate-sort",
    recipes: [
      {
        ...defaultUltimateSortRecipe(280),
        id: "selection-ghost",
        amount: 1e-4,
        action: "wand",
        signal: "brightness",
        territory: "edges",
        resolution: "pixel",
        maxBlock: 1
      },
      {
        ...defaultUltimateSortRecipe(281),
        id: "green-resolution-wake"
      }
    ]
  });
  var asciiBanks = [
    { id: "density", label: "ASCII", description: "A classic light-to-dark density ramp.", glyphs: [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"] },
    { id: "punctuation", label: "Punctuation", description: "Nervous language fragments and small cuts.", glyphs: [" ", ".", ",", ":", ";", "!", "?", "'", '"', "/", "\\", "|", "_", "~"] },
    { id: "symbols", label: "Symbols", description: "Stars, hearts, moons, circles, and signs.", glyphs: [" ", "\xB7", "\u25CB", "\u25CF", "\u25C7", "\u25C6", "\u25B3", "\u25B2", "\u2665", "\u263E", "\u263C", "\u2726", "\u2715"] },
    { id: "tiles", label: "Tiles", description: "Block elements that rebuild the image as masonry.", glyphs: [" ", "\u2591", "\u2592", "\u2593", "\u2588", "\u2580", "\u2584", "\u258C", "\u2590", "\u25A0", "\u25A1", "\u25C6"] },
    { id: "custom", label: "Custom", description: "Your own ordered character vocabulary.", glyphs: [" ", ".", ":", "*", "#", "@"] }
  ];
  var defaultCharacterField = () => ({
    kind: "ascii",
    bank: "punctuation",
    glyphs: [...asciiBanks[1].glyphs],
    composition: "inlay",
    glyphLogic: "repeat",
    inkMode: "chosen",
    inkColor: 15920871,
    groundColor: 1381145
  });
  var zhuyinInitials = Array.from("\u3105\u3106\u3107\u3108\u3109\u310A\u310B\u310C\u310D\u310E\u310F\u3110\u3111\u3112\u3113\u3114\u3115\u3116\u3117\u3118\u3119");
  var zhuyinFinals = Array.from("\u3127\u3128\u3129\u311A\u311B\u311C\u311D\u311E\u311F\u3120\u3121\u3122\u3123\u3124\u3125\u3126");
  var zhuyinTones = Array.from("\u02C9\u02CA\u02C7\u02CB\u02D9");
  var zhuyinBanks = [
    { id: "full", label: "Full system", description: "Initials and finals in their standard Zhuyin order.", glyphs: [...zhuyinInitials, ...zhuyinFinals] },
    { id: "initials", label: "Initials", description: "The sharper consonant-bearing signs.", glyphs: [...zhuyinInitials] },
    { id: "finals", label: "Finals", description: "The rounder vowel and ending signs.", glyphs: [...zhuyinFinals] },
    { id: "tones", label: "Tone marks", description: "Five small directional accents.", glyphs: [...zhuyinTones] },
    { id: "custom", label: "Custom sequence", description: "A deliberate Zhuyin phrase, fragment, or reordered vocabulary.", glyphs: Array.from("\u3105\u3106\u3107\u3108\u02CA\u02C7\u02CB\u02D9") }
  ];
  var defaultZhuyinField = () => ({
    kind: "zhuyin",
    bank: "full",
    glyphs: [...zhuyinBanks[0].glyphs],
    mutationMode: "held",
    composition: "inlay",
    inkMode: "palette",
    inkColor: 15920871,
    groundColor: 1381145
  });
  var petsciiPalette = [
    0,
    16777215,
    8467256,
    7720648,
    9321623,
    5680205,
    3026075,
    15593841,
    9326633,
    5584896,
    12872817,
    4868682,
    8092539,
    11141023,
    7368171,
    11711154
  ];
  var defaultTileField = () => ({
    kind: "petscii-study",
    foregroundColor: petsciiPalette[14],
    backgroundColor: petsciiPalette[0]
  });
  var whereModes = [
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
    { value: "blocks", label: "Blocks", description: "Use a deterministic broken field of territories." }
  ];
  var paletteStructures = [
    { value: "monochrome", label: "Monochrome", description: "One hue carried through a tonal ladder." },
    { value: "duotone", label: "Duotone", description: "Two hue families arguing across the image." },
    { value: "analogous", label: "Analogous", description: "Neighboring hues held inside a narrow weather system." },
    { value: "complementary", label: "Complementary", description: "A direct opposition across the color wheel." },
    { value: "split-complementary", label: "Split complementary", description: "One anchor facing two uneven opponents." },
    { value: "triadic", label: "Triadic", description: "Three equidistant signals with controlled intensity." },
    { value: "source", label: "Extracted from image", description: "Four colors sampled from the current source material." },
    { value: "custom", label: "Restricted custom", description: "The four swatches stay exactly as you set them." }
  ];
  var effectDefinitions = [
    {
      type: "band-rupture",
      name: "Band Rupture",
      category: "Order",
      description: "Break horizontal memory into displaced bands and hard scars.",
      parameters: [
        { id: "rupture", label: "Rupture", description: "How far bands abandon alignment.", min: 0, max: 1, step: 0.01, default: 0.48 },
        { id: "bands", label: "Band Count", description: "Fewer creates slabs; more creates nervous strata.", min: 8, max: 160, step: 1, default: 72 },
        { id: "scar", label: "Scar Chance", description: "How often an interruption refuses the image.", min: 0, max: 1, step: 0.01, default: 0.24 },
        { id: "memory", label: "Retained Memory", description: "How strongly the source survives inside displaced bands.", min: 0, max: 1, step: 0.01, default: 0.72 }
      ]
    },
    {
      type: "wrong-sort",
      name: "Wrong Sort",
      category: "Order",
      description: "Sort only fragments, then deliberately abandon the rest.",
      parameters: [
        { id: "amount", label: "Completion", description: "How much of the image is allowed to become ordered.", min: 0, max: 1, step: 0.01, default: 0.42 },
        { id: "threshold", label: "Value Gate", description: "Which brightness territory is eligible to move.", min: 0, max: 1, step: 0.01, default: 0.32 },
        { id: "chunk", label: "Chunk", description: "The length of each local argument about order.", min: 4, max: 180, step: 1, default: 54 },
        { id: "direction", label: "Direction", description: "Horizontal or vertical sorting, forward or reversed.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] },
        { id: "channel", label: "Signal", description: "The channel whose value decides the order.", min: 0, max: 5, step: 1, default: 5, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness"] }
      ]
    },
    {
      type: "median-filter",
      name: "Median Filter",
      category: "Order",
      description: "Order every 3 \xD7 3 neighborhood by one color signal: the median heals noise, while off-center ranks grow painterly smears.",
      parameters: [
        { id: "position", label: "Neighborhood Rank", description: "Choose which of the nine locally ordered pixels replaces the center. Four is the true median.", min: 0, max: 8, step: 1, default: 3, choices: ["Lowest", "Low 2", "Low 3", "Near-median low", "True median", "Near-median high", "High 3", "High 2", "Highest"] },
        { id: "channel", label: "Ordering Signal", description: "The color evidence used to order each neighborhood; inverted signals reverse its pressure.", min: 0, max: 11, step: 1, default: 11, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness", "Inverted red", "Inverted green", "Inverted blue", "Inverted hue", "Inverted saturation", "Inverted brightness"] },
        { id: "iterations", label: "Filter Passes", description: "Repeated passes let a subtle local choice spread into a larger liquid or brushed territory.", min: 1, max: 24, step: 1, default: 6 },
        { id: "blendMode", label: "Original Blend", description: "Optionally recombine the original image with the filtered result using the source sketch's blend logic.", min: 0, max: 6, step: 1, default: 0, choices: ["Filter only", "Overlay", "Hard light", "Screen", "Multiply", "Add", "Difference"] }
      ]
    },
    {
      type: "sorting-motion",
      name: "Sorting Motion",
      category: "Temporal",
      description: "Let a partial sorting method reach maximum order, release to the incoming image, and return in a seamless loop.",
      parameters: [
        { id: "method", label: "Method", description: "The temporal handwriting used to reorganize each fragment.", min: 0, max: 5, step: 1, default: 0, choices: ["Bubble", "Insertion", "Selection", "Merge", "Permute", "Roll"] },
        { id: "maximumOrder", label: "Maximum Order", description: "The strongest partial ordering reached at the loop boundary.", min: 0, max: 1, step: 0.01, default: 0.72 },
        { id: "span", label: "Fragment Span", description: "Length of each local interval allowed to negotiate a new order.", min: 8, max: 240, step: 1, default: 72 },
        { id: "channel", label: "Signal", description: "The color evidence that decides the order.", min: 0, max: 5, step: 1, default: 5, choices: ["Red", "Green", "Blue", "Hue", "Saturation", "Brightness"] },
        { id: "direction", label: "Travel", description: "The spatial direction receiving the reorganized fragments.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] },
        { id: "reverse", label: "Order Direction", description: "Choose whether low or high signal values lead each fragment.", min: 0, max: 1, step: 1, default: 0, choices: ["Low leads", "High leads"] }
      ]
    },
    {
      type: "ultimate-sort",
      name: "Ultimate Sort",
      category: "Order",
      description: "Stack independent sorting, selection-wand, and resolution recipes so different territories obey different rules.",
      parameters: []
    },
    {
      type: "wizprocess",
      name: "Wizprocess",
      category: "Signal",
      description: "",
      parameters: []
    },
    {
      type: "pixel-drift",
      name: "Pixel Drift",
      category: "Decay",
      description: "Let neighboring pixels pull the image into directional spectral erosion.",
      parameters: [
        { id: "distance", label: "Drift Distance", description: "How far each iteration reaches for its neighbor.", min: 1, max: 42, step: 1, default: 9 },
        { id: "iterations", label: "Decay Passes", description: "How many times the image forgets its prior boundary.", min: 1, max: 18, step: 1, default: 4 },
        { id: "hueMemory", label: "Hue Memory", description: "How stubbornly hue resists the drift.", min: 0, max: 1, step: 0.01, default: 0.82 },
        { id: "lightMemory", label: "Light Memory", description: "How stubbornly brightness resists the drift.", min: 0, max: 1, step: 0.01, default: 0.38 },
        { id: "direction", label: "Direction", description: "The direction of the erosion current.", min: 0, max: 3, step: 1, default: 0, choices: ["Right", "Left", "Down", "Up"] }
      ]
    },
    {
      type: "signal-echo",
      name: "Signal Echo",
      category: "Signal",
      description: "Misregister color signal, scan phase, and remembered transmissions.",
      parameters: [
        { id: "separation", label: "Channel Separation", description: "Distance between the color ghosts.", min: 0, max: 64, step: 1, default: 13 },
        { id: "bleed", label: "Chroma Bleed", description: "How far color spills outside form.", min: 0, max: 1, step: 0.01, default: 0.54 },
        { id: "scan", label: "Scan Pressure", description: "Visibility and violence of scanning structure.", min: 0, max: 1, step: 0.01, default: 0.28 },
        { id: "ghost", label: "Ghost Memory", description: "Strength of the delayed image echo.", min: 0, max: 1, step: 0.01, default: 0.46 }
      ]
    },
    {
      type: "dither-field",
      name: "Dither Field",
      category: "Quantize",
      description: "Quantize channels into a granular threshold field.",
      parameters: [
        { id: "levels", label: "Color Steps", description: "How many signal levels remain available.", min: 2, max: 16, step: 1, default: 4 },
        { id: "grain", label: "Pixel Grain", description: "Scale of the threshold lattice.", min: 1, max: 12, step: 1, default: 2 },
        { id: "pressure", label: "Error Pressure", description: "How strongly threshold error marks the result.", min: 0, max: 1, step: 0.01, default: 0.68 },
        { id: "channelOffset", label: "Channel Offset", description: "Separates the red and blue threshold fields.", min: 0, max: 12, step: 1, default: 2 }
      ]
    },
    {
      type: "lens-warp",
      name: "Lens Warp",
      category: "Spatial",
      description: "Use the image's own signal as a lens that bends its coordinates.",
      parameters: [
        { id: "bendX", label: "Horizontal Bend", description: "How much signal displaces the horizontal axis.", min: 0, max: 1, step: 0.01, default: 0.22 },
        { id: "bendY", label: "Vertical Bend", description: "How much signal displaces the vertical axis.", min: 0, max: 1, step: 0.01, default: 0.14 },
        { id: "frequency", label: "Lens Frequency", description: "How often the lens changes its mind across the image.", min: 0.2, max: 12, step: 0.1, default: 3.4 },
        { id: "mode", label: "Lens Shape", description: "Linear, sinusoidal, or polar coordinate pressure.", min: 0, max: 2, step: 1, default: 1, choices: ["Linear", "Sinusoidal", "Polar"] }
      ]
    },
    {
      type: "mirror-cut",
      name: "Mirror Cut",
      category: "Fold",
      description: "Fold axes and diagonals into asymmetric copied architecture.",
      parameters: [
        { id: "mode", label: "Fold", description: "Axis, diagonal, shifted, or kaleidoscopic copy.", min: 0, max: 5, step: 1, default: 2, choices: ["Left", "Right", "Top", "Bottom", "Diagonal", "Shifted"] },
        { id: "offset", label: "Cut Offset", description: "Where the copied structure stops obeying symmetry.", min: -1, max: 1, step: 0.01, default: 0.16 },
        { id: "mix", label: "Fold Memory", description: "Balance between the prior image and its folded replacement.", min: 0, max: 1, step: 0.01, default: 0.74 }
      ]
    },
    {
      type: "motion-leak",
      name: "Motion Leak",
      category: "Temporal",
      description: "Make a still misremember itself as damaged predictive video blocks.",
      parameters: [
        { id: "block", label: "Prediction Block", description: "Size of the false codec memory units.", min: 4, max: 64, step: 2, default: 16 },
        { id: "vector", label: "Motion Vector", description: "How far a block reaches into the wrong remembered place.", min: 0, max: 96, step: 1, default: 28 },
        { id: "leak", label: "Reference Leak", description: "How many blocks accept the false prediction.", min: 0, max: 1, step: 0.01, default: 0.58 },
        { id: "residual", label: "Residual Memory", description: "How much of the current image survives over predicted blocks.", min: 0, max: 1, step: 0.01, default: 0.34 },
        { id: "coherence", label: "Vector Coherence", description: "From granular block noise to a shared directional failure.", min: 0, max: 1, step: 0.01, default: 0.67 }
      ]
    },
    {
      type: "resolution-quilt",
      name: "Resolution Quilt",
      category: "Spatial",
      description: "Build one image from unequal territories of sharp, soft, and broken resolution.",
      parameters: [
        { id: "minChunk", label: "Smallest Chunk", description: "The smallest local territory allowed to retain its own resolution.", min: 4, max: 160, step: 1, default: 18 },
        { id: "maxChunk", label: "Largest Chunk", description: "The largest slab that can interrupt the finer field.", min: 16, max: 480, step: 1, default: 180 },
        { id: "resolutionDrop", label: "Resolution Drop", description: "How aggressively regions collapse into fewer pixels.", min: 0, max: 1, step: 0.01, default: 0.64 },
        { id: "softness", label: "Soft Enlargement", description: "From hard pixel edges to blurred resampling.", min: 0, max: 1, step: 0.01, default: 0.32 },
        { id: "displacement", label: "Block Travel", description: "How far resampled territories leave their original coordinates.", min: 0, max: 1, step: 0.01, default: 0.18 },
        { id: "vacancy", label: "Missing Territory", description: "How often a region becomes deliberate absence.", min: 0, max: 1, step: 0.01, default: 0.08 }
      ]
    },
    {
      type: "shard-field",
      name: "Shard Field",
      category: "Spatial",
      description: "Detach rectangular pieces, rotate them, repeat them, and leave the image structurally incomplete.",
      parameters: [
        { id: "pieces", label: "Piece Count", description: "How many pieces negotiate a new arrangement.", min: 3, max: 140, step: 1, default: 34 },
        { id: "minSpan", label: "Smallest Piece", description: "Minimum piece size as a fraction of the image.", min: 0.01, max: 0.3, step: 0.01, default: 0.04 },
        { id: "maxSpan", label: "Largest Piece", description: "Maximum piece size as a fraction of the image.", min: 0.05, max: 0.85, step: 0.01, default: 0.28 },
        { id: "travel", label: "Shard Travel", description: "How far detached pieces can abandon their source.", min: 0, max: 1, step: 0.01, default: 0.24 },
        { id: "rotation", label: "Rotation", description: "Angular instability of detached pieces.", min: 0, max: 1, step: 0.01, default: 0.12 },
        { id: "repetition", label: "Repetition", description: "Chance that one piece echoes into another position.", min: 0, max: 1, step: 0.01, default: 0.22 },
        { id: "absence", label: "Absence", description: "Chance that a detached region refuses replacement.", min: 0, max: 1, step: 0.01, default: 0.12 }
      ]
    },
    {
      type: "cut-repeat",
      name: "Cut / Repeat",
      category: "Order",
      description: "Select strips by signal, stretch them, repeat them, and cut holes in the expected sequence.",
      parameters: [
        { id: "selector", label: "Selection Signal", description: "Which image evidence decides what can be cut.", min: 0, max: 3, step: 1, default: 3, choices: ["Bright", "Dark", "Edges", "Chance"] },
        { id: "cuts", label: "Cut Count", description: "Number of candidate fragments.", min: 2, max: 120, step: 1, default: 26 },
        { id: "span", label: "Cut Span", description: "Typical width of selected material.", min: 0.01, max: 0.5, step: 0.01, default: 0.12 },
        { id: "stretch", label: "Stretch", description: "How far a fragment changes proportion.", min: 0, max: 1, step: 0.01, default: 0.38 },
        { id: "repetition", label: "Repeat Count", description: "How many echoes a chosen fragment may produce.", min: 1, max: 12, step: 1, default: 4 },
        { id: "drift", label: "Sequence Drift", description: "Distance between repeated fragments.", min: 0, max: 1, step: 0.01, default: 0.16 },
        { id: "absence", label: "Cut Away", description: "How often selection produces a gap rather than a copy.", min: 0, max: 1, step: 0.01, default: 0.14 }
      ]
    },
    {
      type: "ascii-field",
      name: "ASCII Field",
      category: "Character",
      description: "Build a pure character field or replace selected image territories with an exact ASCII pattern.",
      parameters: [
        { id: "cellSize", label: "Cell Size", description: "The scale of each character cell, held proportionally across preview and export.", min: 7, max: 56, step: 1, default: 15 },
        { id: "coverage", label: "Pattern Fill", description: "How many cells inside the chosen territory print a character; silent cells retain the chosen ground.", min: 0, max: 1, step: 0.01, default: 1 },
        { id: "imageLoyalty", label: "Mass Fidelity", description: "How faithfully character weight rebuilds the source image's light and dark masses.", min: 0, max: 1, step: 0.01, default: 0.88 },
        { id: "edgeVoice", label: "Contour Voice", description: "How strongly directional ASCII strokes draw boundaries through the pattern.", min: 0, max: 1, step: 0.01, default: 0.28 },
        { id: "instability", label: "Alphabet Instability", description: "Legacy character mutation retained for older recipes.", min: 0, max: 1, step: 0.01, default: 0 },
        { id: "vacancy", label: "Vacancy", description: "Legacy random silence retained for older recipes.", min: 0, max: 0.9, step: 0.01, default: 0 },
        { id: "gridDamage", label: "Grid Damage", description: "Legacy grid displacement retained for older recipes.", min: 0, max: 1, step: 0.01, default: 0 },
        { id: "invertDensity", label: "Density", description: "Choose whether dark or light regions carry the heaviest marks.", min: 0, max: 1, step: 1, default: 0, choices: ["Dark is dense", "Light is dense"] }
      ]
    },
    {
      type: "zhuyin-weave",
      name: "Zhuyin Weave",
      category: "Character",
      description: "Layer patterned Zhuyin signs as woven ink inside selected image territories.",
      parameters: [
        { id: "cellSize", label: "Cell Size", description: "The scale of the repeating Zhuyin cell.", min: 9, max: 64, step: 1, default: 22 },
        { id: "coverage", label: "Pattern Fill", description: "How many cells inside the chosen territory receive the weave.", min: 0, max: 1, step: 0.01, default: 0.82 },
        { id: "voices", label: "Voices", description: "How many related symbol layers inhabit the same territory.", min: 1, max: 4, step: 1, default: 2 },
        { id: "misregistration", label: "Misregistration", description: "How far the layered voices slip apart like imperfect printing.", min: 0, max: 1, step: 0.01, default: 0.22 },
        { id: "rowDrift", label: "Row Drift", description: "How strongly each row advances through the symbol sequence.", min: 0, max: 1, step: 0.01, default: 0.42 },
        { id: "imageRhythm", label: "Image Rhythm", description: "How much source brightness bends the repeating symbol phase.", min: 0, max: 1, step: 0.01, default: 0.38 },
        { id: "motion", label: "Loop Motion", description: "How far row phase and layered registration travel during a closed loop.", min: 0, max: 1, step: 0.01, default: 0.32 }
      ]
    },
    {
      type: "petscii-study",
      name: "PETSCII Study",
      category: "Character",
      description: "Rebuild the complete image from a fixed 40 \xD7 25 vocabulary of quadrant tiles.",
      parameters: [
        { id: "threshold", label: "Tile Threshold", description: "Which sampled quadrants become foreground tile mass.", min: 0.05, max: 0.95, step: 0.01, default: 0.48 },
        { id: "imagePull", label: "Image Pull", description: "From one shared ink color to the nearest C64-inspired color in each cell.", min: 0, max: 1, step: 0.01, default: 0.78 },
        { id: "reverseMass", label: "Mass Direction", description: "Choose whether dark or light source mass becomes the foreground tile.", min: 0, max: 1, step: 1, default: 0, choices: ["Dark becomes tile", "Light becomes tile"] }
      ]
    }
  ];
  var definitionFor = (type) => effectDefinitions.find((item) => item.type === type);
  var instanceCounter = 0;
  function defaultWhere(seed = 0) {
    return { mode: "whole", threshold: 0.5, softness: 0.12, hue: 0, hueWidth: 36, scale: 48, invert: false, seed: Math.max(0, Math.round(seed)) };
  }
  function createEffect(type, seed = Date.now()) {
    const definition = definitionFor(type);
    const random = randomSource(seed + instanceCounter++ * 997);
    const effect = {
      id: `${type}-${Math.floor(random() * 16777215).toString(16).padStart(6, "0")}`,
      type,
      enabled: true,
      where: defaultWhere(seed + instanceCounter * 7919),
      parameters: Object.fromEntries(definition.parameters.map((parameter) => [parameter.id, parameter.default]))
    };
    if (type === "ascii-field") effect.characterField = defaultCharacterField();
    if (type === "zhuyin-weave") effect.zhuyinField = defaultZhuyinField();
    if (type === "petscii-study") effect.tileField = defaultTileField();
    if (type === "ultimate-sort") effect.ultimateSort = defaultUltimateSortStack();
    if (type === "wizprocess") effect.wizprocess = defaultWizprocess();
    return effect;
  }
  var defaultPaletteSettings = () => ({
    structure: "analogous",
    hue: 22,
    hueSpread: 34,
    saturation: 28,
    saturationRange: 18,
    lightnessFloor: 8,
    lightnessCeiling: 94
  });
  var defaultRecipe = () => {
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
      effects: [createEffect("band-rupture", 886), createEffect("signal-echo", 887)]
    };
  };
  function randomSource(seed) {
    let state = seed >>> 0;
    return () => {
      state += 1831565813;
      let value = state;
      value = Math.imul(value ^ value >>> 15, value | 1);
      value ^= value + Math.imul(value ^ value >>> 7, value | 61);
      return ((value ^ value >>> 14) >>> 0) / 4294967296;
    };
  }
  function nextStructure(recipe) {
    const seed = Math.floor(Math.random() * 2e9);
    const random = randomSource(seed);
    return {
      ...recipe,
      revision: recipe.revision + 1,
      seed,
      iteration: 0,
      effects: recipe.effects.map((effect) => {
        const wizprocess2 = effect.type === "wizprocess" ? effect.wizprocess : void 0;
        const mutateWhere = !wizprocess2 || wizprocess2.newStructureWhere;
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
            seed: Math.floor(random() * 2e9)
          } : effect.where,
          parameters: Object.fromEntries(definitionFor(effect.type).parameters.map((parameter) => {
            if (parameter.choices) return [parameter.id, Math.floor(random() * parameter.choices.length)];
            const raw = parameter.min + random() * (parameter.max - parameter.min);
            const stepped = Math.round(raw / parameter.step) * parameter.step;
            return [parameter.id, Number(stepped.toFixed(parameter.step < 0.1 ? 2 : parameter.step < 1 ? 1 : 0))];
          })),
          wizprocess: wizprocess2 ? {
            ...wizprocess2,
            ...wizprocess2.newStructureScale ? {
              mass: Number((0.05 + random() * 0.95).toFixed(2)),
              structure: Number((0.05 + random() * 0.95).toFixed(2)),
              grain: Number((0.05 + random() * 0.95).toFixed(2))
            } : {},
            compression: Math.round(4 + random() * 276),
            expansion: Math.round(4 + random() * 276),
            path: ["rows", "columns", "snake", "clustered"][Math.floor(random() * 4)],
            tide: Number(random().toFixed(2))
          } : void 0
        };
      })
    };
  }
  function mutateZhuyinSequence(glyphs, seed, iteration, mode) {
    const mutated = glyphs.length ? [...glyphs] : ["\u3105"];
    if (mode === "held") return mutated;
    const original = [...mutated];
    const random = randomSource(seed + iteration * 104729 + mutated.length * 8191);
    const edits = mode === "drift" ? 1 : Math.min(8, Math.max(3, Math.ceil(mutated.length * 0.12)));
    for (let edit = 0; edit < edits; edit += 1) {
      const operation = Math.floor(random() * 4);
      const index = Math.floor(random() * mutated.length);
      if ((operation === 0 || operation === 1 && mutated.length >= 64) && mutated.length > 1) {
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
  function nextZhuyinIteration(recipe) {
    const iteration = recipe.iteration + 1;
    return {
      ...recipe,
      revision: recipe.revision + 1,
      iteration,
      effects: recipe.effects.map((effect) => {
        const field = effect.type === "zhuyin-weave" ? effect.zhuyinField : void 0;
        if (!field || field.mutationMode === "held") return effect;
        return {
          ...effect,
          zhuyinField: {
            ...field,
            bank: "custom",
            glyphs: mutateZhuyinSequence(field.glyphs, recipe.seed + effect.where.seed, iteration, field.mutationMode)
          }
        };
      })
    };
  }
  function hslToPacked(h, s, l) {
    const a = s * Math.min(l, 1 - l);
    const f = (n) => {
      const k = (n + h * 12) % 12;
      return l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    };
    return Math.round(f(0) * 255) << 16 | Math.round(f(8) * 255) << 8 | Math.round(f(4) * 255);
  }
  var clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  var wrapHue = (value) => (value % 360 + 360) % 360;
  function paletteFromSettings(settings) {
    const hue = wrapHue(settings.hue);
    const spread = clamp(settings.hueSpread, 0, 180);
    const hueOffsets = {
      monochrome: [0, 0, 0, 0],
      duotone: [0, spread, spread, 0],
      analogous: [-spread, -spread / 3, spread / 3, spread],
      complementary: [0, 180, 180, 0],
      "split-complementary": [0, 180 - spread / 2, 180 + spread / 2, 0],
      triadic: [0, 120, 240, 0]
    };
    const offsets = hueOffsets[settings.structure] ?? [0, 0, 0, 0];
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
      lightness[index] / 100
    ));
  }
  function applyPaletteSettings(recipe, patch) {
    const paletteSettings = { ...recipe.paletteSettings, ...patch };
    if (paletteSettings.lightnessFloor > paletteSettings.lightnessCeiling) {
      if (patch.lightnessFloor !== void 0) paletteSettings.lightnessCeiling = paletteSettings.lightnessFloor;
      else paletteSettings.lightnessFloor = paletteSettings.lightnessCeiling;
    }
    const preserveSwatches = paletteSettings.structure === "custom" || paletteSettings.structure === "source";
    return {
      ...recipe,
      revision: recipe.revision + 1,
      paletteSettings,
      palette: preserveSwatches ? recipe.palette : paletteFromSettings(paletteSettings)
    };
  }
  function nextColors(recipe) {
    const colorSeed = Math.floor(Math.random() * 2e9);
    const random = randomSource(colorSeed);
    const effects = recipe.effects.map((effect) => {
      const wizprocess2 = effect.type === "wizprocess" ? effect.wizprocess : void 0;
      if (!wizprocess2?.newColors) return effect;
      const channels = random() > 0.5 ? "together" : "separate";
      return {
        ...effect,
        wizprocess: {
          ...wizprocess2,
          colorSpace: random() > 0.5 ? "hsb" : "rgb",
          channels,
          channelPhase: channels === "together" ? Math.round(random() * 24 - 12) : 0,
          reconstruction: ["fold", "wrap", "clip", "reflect"][Math.floor(random() * 4)]
        }
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
        effects
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
        hslToPacked((base + relation[2]) % 1, 0.03 + random() * 0.18, 0.02 + random() * 0.14)
      ]
    };
  }
  function normalizeUltimateSortStack(stack) {
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
          method: methods.includes(recipe.method) ? recipe.method : base.method,
          amount: Math.max(0, Math.min(1, Number(recipe.amount ?? base.amount))),
          action: actions.includes(recipe.action) ? recipe.action : base.action,
          direction: directions.includes(recipe.direction) ? recipe.direction : base.direction,
          signal: signals.includes(recipe.signal) ? recipe.signal : base.signal,
          territory: territories.includes(recipe.territory) ? recipe.territory : base.territory,
          gate: Math.max(0, Math.min(1200, Number(recipe.gate ?? base.gate))),
          resolution: resolutions.includes(recipe.resolution) ? recipe.resolution : base.resolution,
          minBlock,
          maxBlock: Math.max(minBlock, Math.min(32, Math.round(Number(recipe.maxBlock ?? base.maxBlock)))),
          selectionSpeed: Math.max(0, Math.min(12, Math.round(Number(recipe.selectionSpeed ?? base.selectionSpeed))))
        };
      })
    };
  }
  function normalizeWizprocess(chamber) {
    const fallback = defaultWizprocess();
    const colorSpaces = ["rgb", "hsb"];
    const channels = ["together", "separate"];
    const paths = ["rows", "columns", "snake", "clustered"];
    const reconstructions = ["fold", "wrap", "clip", "reflect"];
    return {
      ...fallback,
      ...chamber ?? {},
      kind: "wizprocess",
      mass: Math.max(0, Math.min(1, Number(chamber?.mass ?? fallback.mass))),
      structure: Math.max(0, Math.min(1, Number(chamber?.structure ?? fallback.structure))),
      grain: Math.max(0, Math.min(1, Number(chamber?.grain ?? fallback.grain))),
      compression: Math.max(1, Math.min(1200, Number(chamber?.compression ?? fallback.compression))),
      expansion: Math.max(0, Math.min(1200, Number(chamber?.expansion ?? fallback.expansion))),
      colorSpace: colorSpaces.includes(chamber?.colorSpace ?? "") ? chamber.colorSpace : fallback.colorSpace,
      channels: channels.includes(chamber?.channels ?? "") ? chamber.channels : fallback.channels,
      channelPhase: Math.max(-48, Math.min(48, Math.round(Number(chamber?.channelPhase ?? fallback.channelPhase)))),
      path: paths.includes(chamber?.path ?? "") ? chamber.path : fallback.path,
      reconstruction: reconstructions.includes(chamber?.reconstruction ?? "") ? chamber.reconstruction : fallback.reconstruction,
      tide: Math.max(0, Math.min(1, Number(chamber?.tide ?? fallback.tide))),
      newStructureScale: chamber?.newStructureScale !== false,
      newStructureWhere: chamber?.newStructureWhere !== false,
      newColors: chamber?.newColors !== false
    };
  }
  function normalizeRecipe(value) {
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
        structure: paletteStructures.some((item) => item.value === value.paletteSettings?.structure) ? value.paletteSettings.structure : fallback.paletteSettings.structure
      } : { ...fallback.paletteSettings, structure: "custom" },
      palette: Array.isArray(value.palette) && value.palette.length === 4 ? value.palette.map((color) => Math.max(0, Math.min(16777215, Math.round(color)))) : fallback.palette,
      layers: Array.isArray(value.layers) ? value.layers.filter((layer) => layer && typeof layer.filePath === "string").map((layer) => ({
        id: String(layer.id ?? `layer-${Date.now()}`),
        label: String(layer.label ?? "Layer"),
        filePath: layer.filePath,
        enabled: layer.enabled !== false,
        opacity: Math.max(0, Math.min(1, Number(layer.opacity ?? 1))),
        blendMode: ["normal", "difference", "overlay", "hard-mix", "screen", "multiply", "lighten", "darken"].includes(layer.blendMode) ? layer.blendMode : "normal",
        maskMode: ["whole", "checker", "stripes", "blocks", "light", "dark", "edges"].includes(layer.maskMode) ? layer.maskMode : "whole",
        maskScale: Math.max(2, Math.min(240, Number(layer.maskScale ?? 48))),
        seed: Math.max(0, Math.round(Number(layer.seed ?? value.seed ?? fallback.seed)))
      })) : [],
      effects: value.effects.map((effect) => {
        if (effect.type !== "wavelet-chamber") return effect;
        const legacy = effect;
        const { waveletChamber, ...rest } = legacy;
        return { ...rest, type: "wizprocess", wizprocess: legacy.wizprocess ?? waveletChamber };
      }).filter((effect) => effectDefinitions.some((definition) => definition.type === effect.type)).map((effect) => {
        const base = createEffect(effect.type, value.seed);
        const incomingWhere = effect.where;
        return {
          ...base,
          ...effect,
          where: {
            ...base.where,
            ...incomingWhere ?? {},
            mode: whereModes.some((item) => item.value === incomingWhere?.mode) ? incomingWhere?.mode : "whole",
            threshold: Math.max(0, Math.min(1, Number(incomingWhere?.threshold ?? base.where.threshold))),
            softness: Math.max(0, Math.min(0.5, Number(incomingWhere?.softness ?? base.where.softness))),
            hue: Math.max(0, Math.min(359, Math.round(Number(incomingWhere?.hue ?? base.where.hue)))),
            hueWidth: Math.max(1, Math.min(180, Math.round(Number(incomingWhere?.hueWidth ?? base.where.hueWidth)))),
            scale: Math.max(2, Math.min(240, Math.round(Number(incomingWhere?.scale ?? base.where.scale)))),
            invert: incomingWhere?.invert === true,
            seed: Math.max(0, Math.round(Number(incomingWhere?.seed ?? base.where.seed)))
          },
          parameters: { ...base.parameters, ...effect.parameters },
          characterField: effect.type === "ascii-field" ? {
            ...defaultCharacterField(),
            ...effect.characterField ?? {},
            kind: "ascii",
            composition: ["field", "inlay"].includes(effect.characterField?.composition ?? "") ? effect.characterField.composition : "field",
            glyphLogic: ["mass", "repeat"].includes(effect.characterField?.glyphLogic ?? "") ? effect.characterField.glyphLogic : "mass",
            bank: asciiBanks.some((bank) => bank.id === effect.characterField?.bank) ? effect.characterField.bank : "density",
            glyphs: Array.isArray(effect.characterField?.glyphs) && effect.characterField.glyphs.length ? effect.characterField.glyphs.map((glyph) => String(glyph)).filter((glyph) => glyph.length > 0).slice(0, 64) : [...asciiBanks[0].glyphs],
            inkMode: ["source", "palette", "chosen"].includes(effect.characterField?.inkMode ?? "") ? effect.characterField.inkMode : "source",
            inkColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.characterField?.inkColor ?? 15920871)))),
            groundColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.characterField?.groundColor ?? 1381145))))
          } : void 0,
          zhuyinField: effect.type === "zhuyin-weave" ? {
            ...defaultZhuyinField(),
            ...effect.zhuyinField ?? {},
            kind: "zhuyin",
            composition: ["field", "inlay"].includes(effect.zhuyinField?.composition ?? "") ? effect.zhuyinField.composition : "inlay",
            bank: zhuyinBanks.some((bank) => bank.id === effect.zhuyinField?.bank) ? effect.zhuyinField.bank : "full",
            glyphs: Array.isArray(effect.zhuyinField?.glyphs) && effect.zhuyinField.glyphs.length ? effect.zhuyinField.glyphs.map((glyph) => String(glyph)).filter((glyph) => glyph.length > 0).slice(0, 64) : [...zhuyinBanks[0].glyphs],
            mutationMode: ["held", "drift", "fracture"].includes(effect.zhuyinField?.mutationMode ?? "") ? effect.zhuyinField.mutationMode : "held",
            inkMode: ["source", "palette", "chosen"].includes(effect.zhuyinField?.inkMode ?? "") ? effect.zhuyinField.inkMode : "palette",
            inkColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.zhuyinField?.inkColor ?? 15920871)))),
            groundColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.zhuyinField?.groundColor ?? 1381145))))
          } : void 0,
          tileField: effect.type === "petscii-study" ? {
            ...defaultTileField(),
            ...effect.tileField ?? {},
            kind: "petscii-study",
            foregroundColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.tileField?.foregroundColor ?? petsciiPalette[14])))),
            backgroundColor: Math.max(0, Math.min(16777215, Math.round(Number(effect.tileField?.backgroundColor ?? petsciiPalette[0]))))
          } : void 0,
          ultimateSort: effect.type === "ultimate-sort" ? normalizeUltimateSortStack(effect.ultimateSort) : void 0,
          wizprocess: effect.type === "wizprocess" ? normalizeWizprocess(effect.wizprocess) : void 0
        };
      })
    };
  }

  // local/glitch-build/effects.ts
  var packedCss = (packed, alpha = 1) => `rgba(${packed >> 16 & 255},${packed >> 8 & 255},${packed & 255},${alpha})`;
  var param = (effect, id, fallback) => effect.parameters[id] ?? fallback;
  function fittedSource(image, width, height, recipe) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    context.imageSmoothingEnabled = false;
    context.fillStyle = packedCss(recipe.palette[3]);
    context.fillRect(0, 0, width, height);
    if (image) {
      const scale = recipe.sourceFit === "contain" ? Math.min(width / image.naturalWidth, height / image.naturalHeight) : Math.max(width / image.naturalWidth, height / image.naturalHeight);
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
  function newSurface(width, height) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    return canvas;
  }
  function cloneSurface(input) {
    const output = newSurface(input.width, input.height);
    output.getContext("2d").drawImage(input, 0, 0);
    return output;
  }
  function resolutionQuilt(input, effect, recipe) {
    const output = cloneSurface(input);
    const context = output.getContext("2d");
    const minChunk = Math.max(4, param(effect, "minChunk", 18));
    const maxChunk = Math.max(minChunk, param(effect, "maxChunk", 180));
    const drop = param(effect, "resolutionDrop", 0.64);
    const softness = param(effect, "softness", 0.32);
    const displacement = param(effect, "displacement", 0.18);
    const vacancy = param(effect, "vacancy", 0.08);
    const random = randomSource(recipe.seed + 19013);
    for (let y = 0; y < input.height; ) {
      const rowHeight = Math.min(input.height - y, minChunk + random() * (maxChunk - minChunk));
      for (let x = 0; x < input.width; ) {
        const chunkWidth = Math.min(input.width - x, minChunk + random() * (maxChunk - minChunk));
        if (random() < vacancy) {
          context.fillStyle = recipe.colorMode === "palette" ? packedCss(recipe.palette[3]) : "rgba(0,0,0,.92)";
          context.fillRect(x, y, chunkWidth, rowHeight);
        } else {
          const level = Math.max(1, 2 ** Math.floor(random() * (1 + drop * 5)));
          const tiny = newSurface(Math.max(1, Math.round(chunkWidth / level)), Math.max(1, Math.round(rowHeight / level)));
          tiny.getContext("2d").drawImage(input, x, y, chunkWidth, rowHeight, 0, 0, tiny.width, tiny.height);
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
  function shardField(input, effect, recipe) {
    const output = cloneSurface(input);
    const context = output.getContext("2d");
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
  function cutRepeat(input, effect, recipe) {
    const output = cloneSurface(input);
    const context = output.getContext("2d");
    const selector = Math.round(param(effect, "selector", 3));
    const cuts = Math.round(param(effect, "cuts", 26));
    const span = param(effect, "span", 0.12);
    const stretch = param(effect, "stretch", 0.38);
    const repetitions = Math.round(param(effect, "repetition", 4));
    const drift = param(effect, "drift", 0.16);
    const absence = param(effect, "absence", 0.14);
    const random = randomSource(recipe.seed + 39041);
    const sample = input.getContext("2d", { willReadFrequently: true });
    for (let cut = 0; cut < cuts; cut += 1) {
      const vertical = random() > 0.5;
      const width = vertical ? Math.max(2, input.width * span * (0.3 + random())) : input.width;
      const height = vertical ? input.height : Math.max(2, input.height * span * (0.3 + random()));
      const sx = random() * Math.max(1, input.width - width);
      const sy = random() * Math.max(1, input.height - height);
      const pixel = sample.getImageData(Math.floor(sx + width / 2), Math.floor(sy + height / 2), 1, 1).data;
      const light = (pixel[0] + pixel[1] + pixel[2]) / 765;
      const eligible = selector === 3 || selector === 0 && light > 0.58 || selector === 1 && light < 0.42 || selector === 2 && Math.abs(pixel[0] - pixel[2]) + Math.abs(pixel[1] - pixel[2]) > 72;
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
  function blendSource(processed, source, presence) {
    if (presence <= 0) return processed;
    const output = cloneSurface(processed);
    const context = output.getContext("2d");
    context.globalAlpha = Math.max(0, Math.min(1, presence));
    context.drawImage(source, 0, 0);
    context.globalAlpha = 1;
    return output;
  }
  function bandRupture(input, effect, recipe, phase) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
  function colorKey(data, offset, channel) {
    const r = data[offset], g = data[offset + 1], b = data[offset + 2];
    if (channel < 3) return data[offset + channel];
    const max = Math.max(r, g, b), min = Math.min(r, g, b), delta = max - min;
    if (channel === 4) return max === 0 ? 0 : delta / max * 255;
    if (channel === 5) return max;
    if (delta === 0) return 0;
    const hue = max === r ? (g - b) / delta % 6 : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
    return (hue * 42.5 + 255) % 255;
  }
  function wrongSort(input, effect, recipe) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
        const pixels = [];
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
  function medianFilter(input, effect) {
    const width = input.width, height = input.height;
    if (width < 3 || height < 3) return cloneSurface(input);
    const position = Math.max(0, Math.min(8, Math.round(param(effect, "position", 3))));
    const channel = Math.max(0, Math.min(11, Math.round(param(effect, "channel", 11))));
    const iterations = Math.max(1, Math.min(24, Math.round(param(effect, "iterations", 6))));
    const original = input.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, width, height);
    let source = new Uint8ClampedArray(original.data);
    let target = new Uint8ClampedArray(source);
    const ranked = new Int32Array(9);
    const colors = new Uint32Array(9);
    const packedRank = (offset) => {
      const red = source[offset], green = source[offset + 1], blue = source[offset + 2];
      const hsb = channel % 6 >= 3 ? rgbToHsb255(red, green, blue) : null;
      const baseChannel = channel % 6;
      let value = baseChannel === 0 ? red : baseChannel === 1 ? green : baseChannel === 2 ? blue : hsb[baseChannel - 3];
      if (channel >= 6) value = 255 - value;
      const color = red << 16 | green << 8 | blue;
      return { packed: value << 24 | color, color };
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
    const result = output.getContext("2d").createImageData(width, height);
    result.data.set(source);
    output.getContext("2d").putImageData(result, 0, 0);
    const blendMode = Math.max(0, Math.min(6, Math.round(param(effect, "blendMode", 0))));
    if (blendMode > 0) {
      const context = output.getContext("2d");
      context.globalCompositeOperation = ["source-over", "overlay", "hard-light", "screen", "multiply", "lighter", "difference"][blendMode];
      context.drawImage(input, 0, 0);
      context.globalCompositeOperation = "source-over";
    }
    return output;
  }
  function motionHash(seed, line, start, salt) {
    let value = seed ^ Math.imul(line + salt, 374761393) ^ Math.imul(start - salt, 668265263) | 0;
    value = Math.imul(value ^ value >>> 13, 1274126177);
    return ((value ^ value >>> 16) & 2147483647) / 2147483647;
  }
  function orderMotionFragment(pixels, method, progress, reverse, seed, line, start) {
    const orderedBefore = (a, b) => reverse ? a.key >= b.key : a.key <= b.key;
    const compare = (a, b) => reverse ? b.key - a.key : a.key - b.key;
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
        while (cursor > 0 && !orderedBefore(pixels[cursor - 1], held)) {
          pixels[cursor] = pixels[cursor - 1];
          cursor -= 1;
        }
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
  function sortingMotion(input, effect, recipe, phase) {
    const output = cloneSurface(input);
    const context = output.getContext("2d");
    const image = context.getImageData(0, 0, input.width, input.height);
    const source = new Uint8ClampedArray(image.data);
    const method = Math.round(param(effect, "method", 0));
    const motion = 0.5 + 0.5 * Math.cos(phase);
    const progress = Math.max(0, Math.min(1, param(effect, "maximumOrder", 0.72) * motion));
    if (progress <= 1e-6) return output;
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
        const pixels = [];
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
  var ultimateMethods = ["bubble", "insertion", "selection", "merge", "permute", "roll"];
  var ultimateSignals = ["red", "green", "blue", "hue", "saturation", "brightness"];
  function ultimateTerritoryMask(data, width, height, recipe) {
    const mask = new Uint8Array(width * height);
    const hueCenters = {
      red: 0,
      orange: 28,
      yellow: 58,
      green: 120,
      cyan: 185,
      blue: 235,
      pink: 325
    };
    const brightnessAt = (x, y) => {
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
        const gx = -brightnessAt(x - 1, y - 1) - 2 * brightnessAt(x - 1, y) - brightnessAt(x - 1, y + 1) + brightnessAt(x + 1, y - 1) + 2 * brightnessAt(x + 1, y) + brightnessAt(x + 1, y + 1);
        const gy = -brightnessAt(x - 1, y - 1) - 2 * brightnessAt(x, y - 1) - brightnessAt(x + 1, y - 1) + brightnessAt(x - 1, y + 1) + 2 * brightnessAt(x, y + 1) + brightnessAt(x + 1, y + 1);
        mask[index] = Math.hypot(gx, gy) >= recipe.gate ? 1 : 0;
      } else {
        const signal = hueAndSaturation(data[offset], data[offset + 1], data[offset + 2]);
        const center = hueCenters[recipe.territory] ?? 0;
        const distance = Math.abs((signal.hue - center + 540) % 360 - 180);
        mask[index] = signal.saturation >= 0.12 && distance <= 28 ? 1 : 0;
      }
    }
    return mask;
  }
  function applyUltimateResolution(incoming, sorted, mask, width, height, recipe) {
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
        if (sampleX < 0) {
          sampleX = x;
          sampleY = y;
        }
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
  function ultimateSort(input, effect, recipe, phase) {
    let output = cloneSurface(input);
    const recipes = effect.ultimateSort?.recipes ?? [];
    const motion = 0.5 + 0.5 * Math.cos(phase);
    recipes.forEach((sortRecipe, recipeIndex) => {
      if (!sortRecipe.enabled) return;
      const context = output.getContext("2d");
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
          const positions = [];
          const pixels = [];
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
        const march = Math.floor(phase / (Math.PI * 2) * 8 * sortRecipe.selectionSpeed);
        for (let y = 0; y < output.height; y += 1) for (let x = 0; x < output.width; x += 1) {
          const pixel = y * output.width + x;
          if (!mask[pixel]) continue;
          const boundary = x === 0 || y === 0 || x === output.width - 1 || y === output.height - 1 || !mask[pixel - 1] || !mask[pixel + 1] || !mask[pixel - output.width] || !mask[pixel + output.width];
          if (!boundary) continue;
          const value = (x + y + march) % 8 < 4 ? 245 : 20;
          image.data.set([value, value, value, 255], pixel * 4);
        }
      }
      context.putImageData(image, 0, 0);
    });
    return output;
  }
  function wizPixelOrder(width, height, path) {
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
            localX |= (morton >> bit * 2 & 1) << bit;
            localY |= (morton >> bit * 2 + 1 & 1) << bit;
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
  function rgbToHsb255(red, green, blue) {
    const r = red / 255, g = green / 255, b = blue / 255;
    const high = Math.max(r, g, b), low = Math.min(r, g, b), delta = high - low;
    let hue = 0;
    if (delta > 0) {
      hue = high === r ? (g - b) / delta % 6 : high === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
      hue = (hue * 60 + 360) % 360;
    }
    return [hue / 360 * 255, high <= 0 ? 0 : delta / high * 255, high * 255];
  }
  function hsbToRgb255(hue, saturation, brightness) {
    const h = hue / 255 * 360 % 360, s = saturation / 255, v = brightness / 255;
    const chroma = v * s, section = h / 60, middle = chroma * (1 - Math.abs(section % 2 - 1));
    const [r1, g1, b1] = section < 1 ? [chroma, middle, 0] : section < 2 ? [middle, chroma, 0] : section < 3 ? [0, chroma, middle] : section < 4 ? [0, middle, chroma] : section < 5 ? [middle, 0, chroma] : [chroma, 0, middle];
    const match = v - chroma;
    return [(r1 + match) * 255, (g1 + match) * 255, (b1 + match) * 255];
  }
  function wizRecover(value, mode) {
    if (mode === "clip") return Math.max(0, Math.min(255, value));
    if (mode === "wrap") return (value % 256 + 256) % 256;
    if (mode === "reflect") {
      const reflected = (value % 510 + 510) % 510;
      return reflected <= 255 ? reflected : 510 - reflected;
    }
    return Math.abs(value < 0 ? 256 + value : value) % 256;
  }
  function wizScaleWeight(span, process, phase) {
    const tide = process.tide;
    const mass = process.mass * (1 - tide * 0.9 * Math.sin(phase * 0.5) ** 2);
    const structure = process.structure * (1 - tide * 0.9 * Math.sin(phase) ** 2);
    const grain = process.grain * (1 - tide * 0.9 * Math.sin(phase * 1.5) ** 2);
    return span <= 8 ? grain : span <= 128 ? structure : mass;
  }
  function transformWizSignal(signal, process, phase) {
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
  function wizprocess(input, effect, phase) {
    const process = effect.wizprocess;
    if (!process) return cloneSurface(input);
    const output = cloneSurface(input), context = output.getContext("2d");
    const image = context.getImageData(0, 0, output.width, output.height);
    const source = new Uint8ClampedArray(image.data);
    const order = wizPixelOrder(output.width, output.height, process.path);
    const evidence = new Float32Array(order.length * 3);
    for (let position = 0; position < order.length; position += 1) {
      const offset = order[position] * 4;
      const values = process.colorSpace === "hsb" ? rgbToHsb255(source[offset], source[offset + 1], source[offset + 2]) : [source[offset], source[offset + 1], source[offset + 2]];
      for (let channel = 0; channel < 3; channel += 1) evidence[position * 3 + channel] = values[channel] > 127 ? values[channel] - 256 : values[channel];
    }
    const reconstructed = new Float32Array(evidence.length);
    if (process.channels === "together") {
      transformWizSignal(evidence, process, phase);
      const shift = process.channelPhase;
      let offset = 0;
      while (offset < evidence.length) {
        const length = 2 ** Math.floor(Math.log2(Math.min(16384, evidence.length - offset)));
        for (let local = 0; local < length; local += 1) reconstructed[offset + local] = evidence[offset + (local + shift + length) % length];
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
      const recovered = [0, 1, 2].map((channel) => wizRecover(reconstructed[position * 3 + channel], process.reconstruction));
      const rgb = process.colorSpace === "hsb" ? hsbToRgb255(...recovered) : recovered;
      image.data[offset] = rgb[0];
      image.data[offset + 1] = rgb[1];
      image.data[offset + 2] = rgb[2];
      image.data[offset + 3] = 255;
    }
    context.putImageData(image, 0, 0);
    return output;
  }
  function pixelDrift(input, effect) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
  function signalEcho(input, effect, recipe, phase) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
  function ditherField(input, effect) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
          const threshold = (matrix[(Math.floor(y / grain) & 3) * 4 + (Math.floor(x / grain) & 3)] / 15 - 0.5) * step * pressure;
          image.data[target + channel] = Math.max(0, Math.min(255, Math.round((prior[source] + threshold) / step) * step));
        }
      }
    }
    context.putImageData(image, 0, 0);
    return output;
  }
  function lensWarp(input, effect, phase) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
    const sourceContext = input.getContext("2d");
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
        const sx = (Math.round(x + ox) % input.width + input.width) % input.width;
        const sy = (Math.round(y + oy) % input.height + input.height) % input.height;
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
  function mirrorCut(input, effect) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
  function motionLeak(input, effect, recipe, phase) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
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
  function asciiHash(seed, column, row, salt = 0) {
    let value = seed ^ Math.imul(column + salt, 374761393) ^ Math.imul(row - salt, 668265263) | 0;
    value = Math.imul(value ^ value >>> 13, 1274126177);
    return ((value ^ value >>> 16) >>> 0) / 4294967295;
  }
  function asciiField(input, effect, recipe, phase) {
    const field = effect.characterField;
    const composition = field?.composition ?? "field";
    const glyphLogic = field?.glyphLogic ?? "mass";
    const output = composition === "inlay" ? cloneSurface(input) : newSurface(input.width, input.height);
    const context = output.getContext("2d");
    const source = input.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, input.width, input.height);
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
    const seed = recipe.seed + effect.where.seed + Math.round(phase * 1e3);
    const territoryScale = Math.max(cell, effect.where.scale * scale);
    const lumaAt = (x, y) => {
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
        const feather = composition === "inlay" ? 1e-3 : Math.max(1e-3, effect.where.softness);
        const territoryColumn = Math.floor(x / territoryScale);
        const territoryRow = Math.floor(y / territoryScale);
        let territory = 1;
        if (effect.where.mode === "light") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
        else if (effect.where.mode === "dark") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
        else if (effect.where.mode === "edges") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, edge);
        else if (effect.where.mode === "saturated") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
        else if (effect.where.mode === "muted") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
        else if (effect.where.mode === "hue") {
          const distance = Math.abs((signal.hue - effect.where.hue + 540) % 360 - 180);
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
        let index = glyphLogic === "repeat" ? (column + row) % glyphs.length : Math.max(0, Math.min(glyphs.length - 1, Math.round(density * (glyphs.length - 1))));
        if (asciiHash(seed, column, row, 43) < instability) {
          const reach = Math.max(1, Math.round(instability * glyphs.length * 0.6));
          index = Math.max(0, Math.min(glyphs.length - 1, index + Math.round((asciiHash(seed, column, row, 47) * 2 - 1) * reach)));
        }
        let glyph = glyphs[index] ?? " ";
        if (edge * edgeVoice > asciiHash(seed, column, row, 53) * 0.35) {
          glyph = Math.abs(edgeX) > Math.abs(edgeY) * 2 ? "|" : Math.abs(edgeY) > Math.abs(edgeX) * 2 ? "-" : edgeX * edgeY > 0 ? "/" : "\\";
        }
        if (field?.inkMode === "source") context.fillStyle = `rgb(${source.data[at]},${source.data[at + 1]},${source.data[at + 2]})`;
        else if (field?.inkMode === "chosen") context.fillStyle = packedCss(field.inkColor);
        else context.fillStyle = packedCss(recipe.palette[Math.max(0, Math.min(2, Math.round(density * 2)))]);
        context.fillText(glyph, x, y + cell * 0.04);
      }
    }
    return output;
  }
  function zhuyinWeave(input, effect, recipe, phase) {
    const field = effect.zhuyinField;
    const composition = field?.composition ?? "inlay";
    const output = composition === "inlay" ? cloneSurface(input) : newSurface(input.width, input.height);
    const context = output.getContext("2d");
    const source = input.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, input.width, input.height);
    const glyphs = field?.glyphs?.length ? field.glyphs : Array.from("\u3105\u3106\u3107\u3108\u3109\u310A\u310B\u310C\u310D\u310E\u310F\u3110\u3111\u3112\u3113\u3114\u3115\u3116\u3117\u3118\u3119\u3127\u3128\u3129\u311A\u311B\u311C\u311D\u311E\u311F\u3120\u3121\u3122\u3123\u3124\u3125\u3126");
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
    const sampleAt = (x, y) => {
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
        const feather = composition === "inlay" ? 1e-3 : Math.max(1e-3, effect.where.softness);
        const territoryColumn = Math.floor(baseX / territoryScale);
        const territoryRow = Math.floor(baseY / territoryScale);
        let territory = 1;
        if (effect.where.mode === "light") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
        else if (effect.where.mode === "dark") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, light);
        else if (effect.where.mode === "edges") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, edge);
        else if (effect.where.mode === "saturated") territory = smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
        else if (effect.where.mode === "muted") territory = 1 - smoothstep(effect.where.threshold - feather, effect.where.threshold + feather, signal.saturation);
        else if (effect.where.mode === "hue") {
          const distance = Math.abs((signal.hue - effect.where.hue + 540) % 360 - 180);
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
  function petsciiStudy(input, effect) {
    const output = newSurface(input.width, input.height);
    const context = output.getContext("2d");
    const source = input.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, input.width, input.height);
    const foreground = effect.tileField?.foregroundColor ?? petsciiPalette[14];
    const background = effect.tileField?.backgroundColor ?? petsciiPalette[0];
    const threshold = param(effect, "threshold", 0.48);
    const imagePull = param(effect, "imagePull", 0.78);
    const reverseMass = param(effect, "reverseMass", 0) >= 0.5;
    const sample = (x, y) => {
      const sx = Math.max(0, Math.min(input.width - 1, Math.round(x)));
      const sy = Math.max(0, Math.min(input.height - 1, Math.round(y)));
      const at = (sy * input.width + sx) * 4;
      return { r: source.data[at], g: source.data[at + 1], b: source.data[at + 2] };
    };
    const nearestPalette = (r, g, b) => {
      let nearest = petsciiPalette[0], distance = Number.POSITIVE_INFINITY;
      for (const packed of petsciiPalette) {
        const pr = packed >> 16 & 255, pg = packed >> 8 & 255, pb = packed & 255;
        const next = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2;
        if (next < distance) {
          nearest = packed;
          distance = next;
        }
      }
      return nearest;
    };
    const mixedInk = (sampled) => {
      const red = Math.round((foreground >> 16 & 255) * (1 - imagePull) + (sampled >> 16 & 255) * imagePull);
      const green = Math.round((foreground >> 8 & 255) * (1 - imagePull) + (sampled >> 8 & 255) * imagePull);
      const blue = Math.round((foreground & 255) * (1 - imagePull) + (sampled & 255) * imagePull);
      return red << 16 | green << 8 | blue;
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
          sample((middleX + x1) / 2, (middleY + y1) / 2)
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
          [middleX, middleY, x1 - middleX, y1 - middleY]
        ];
        active.forEach((visible, index) => {
          if (visible) context.fillRect(...regions[index]);
        });
      }
    }
    return output;
  }
  function transformEffect(input, effect, recipe, phase, animated = false) {
    if (!effect.enabled) return input;
    switch (effect.type) {
      case "band-rupture":
        return bandRupture(input, effect, recipe, phase);
      case "wrong-sort":
        return wrongSort(input, effect, recipe);
      case "median-filter":
        return medianFilter(input, effect);
      case "sorting-motion":
        return sortingMotion(input, effect, recipe, phase);
      case "ultimate-sort":
        return ultimateSort(input, effect, recipe, phase);
      case "wizprocess":
        return wizprocess(input, effect, animated ? phase : 0);
      case "pixel-drift":
        return pixelDrift(input, effect);
      case "signal-echo":
        return signalEcho(input, effect, recipe, phase);
      case "dither-field":
        return ditherField(input, effect);
      case "lens-warp":
        return lensWarp(input, effect, phase);
      case "mirror-cut":
        return mirrorCut(input, effect);
      case "motion-leak":
        return motionLeak(input, effect, recipe, phase);
      case "resolution-quilt":
        return resolutionQuilt(input, effect, recipe);
      case "shard-field":
        return shardField(input, effect, recipe);
      case "cut-repeat":
        return cutRepeat(input, effect, recipe);
      case "ascii-field":
        return asciiField(input, effect, recipe, phase);
      case "zhuyin-weave":
        return zhuyinWeave(input, effect, recipe, phase);
      case "petscii-study":
        return petsciiStudy(input, effect);
    }
  }
  var smoothstep = (low, high, value) => {
    if (high <= low) return value >= high ? 1 : 0;
    const t = Math.max(0, Math.min(1, (value - low) / (high - low)));
    return t * t * (3 - 2 * t);
  };
  function hueAndSaturation(r, g, b) {
    const red = r / 255, green = g / 255, blue = b / 255;
    const maximum = Math.max(red, green, blue), minimum = Math.min(red, green, blue);
    const delta = maximum - minimum;
    let hue = 0;
    if (delta > 0) {
      if (maximum === red) hue = (green - blue) / delta % 6;
      else if (maximum === green) hue = (blue - red) / delta + 2;
      else hue = (red - green) / delta + 4;
      hue = (hue * 60 + 360) % 360;
    }
    return { hue, saturation: maximum === 0 ? 0 : delta / maximum };
  }
  function whereWeights(input, effect) {
    const context = input.getContext("2d", { willReadFrequently: true });
    const image = context.getImageData(0, 0, input.width, input.height);
    const pixels = image.data;
    const weights = new Float32Array(input.width * input.height);
    const where = effect.where;
    const luminance = new Float32Array(weights.length);
    for (let index = 0; index < weights.length; index += 1) {
      const offset = index * 4;
      luminance[index] = (pixels[offset] * 0.2126 + pixels[offset + 1] * 0.7152 + pixels[offset + 2] * 0.0722) / 255;
    }
    const feather = Math.max(1e-3, where.softness);
    const blockValue = (column, row) => {
      let hash = where.seed ^ Math.imul(column, 374761393) ^ Math.imul(row, 668265263) | 0;
      hash = Math.imul(hash ^ hash >>> 13, 1274126177);
      return ((hash ^ hash >>> 16) >>> 0) / 4294967295;
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
            const distance = Math.abs((signal.hue - where.hue + 540) % 360 - 180);
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
  function applyEffect(input, effect, recipe, phase, animated = false) {
    if (!effect.enabled) return input;
    const transformed = transformEffect(input, effect, recipe, phase, animated);
    if (effect.type === "ascii-field" || effect.type === "zhuyin-weave" || effect.type === "petscii-study") return transformed;
    if (effect.where.mode === "whole" && !effect.where.invert) return transformed;
    const output = cloneSurface(input);
    const inputData = input.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, input.width, input.height);
    const transformedData = transformed.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, input.width, input.height);
    const outputContext = output.getContext("2d");
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
  function targetSurface(input, effect) {
    const output = document.createElement("canvas");
    output.width = input.width;
    output.height = input.height;
    const context = output.getContext("2d");
    const image = context.createImageData(output.width, output.height);
    const weights = whereWeights(input, effect);
    for (let index = 0; index < weights.length; index += 1) {
      const value = Math.round(weights[index] * 255);
      const offset = index * 4;
      image.data[offset] = value;
      image.data[offset + 1] = value;
      image.data[offset + 2] = value;
      image.data[offset + 3] = 255;
    }
    context.putImageData(image, 0, 0);
    return output;
  }

  // local/glitch-build/bridge.ts
  function catalog() {
    return {
      definitions: effectDefinitions,
      defaults: defaultRecipe(),
      templates: Object.fromEntries(effectDefinitions.map((d) => [d.type, createEffect(d.type, 886)])),
      whereModes,
      asciiBanks,
      zhuyinBanks,
      paletteStructures,
      petsciiPalette,
      sortRecipe: defaultUltimateSortRecipe(886)
    };
  }
  function normalize(value) {
    if (!value || value.schemaVersion !== 1 || !Array.isArray(value.effects)) throw new Error("Choose a Glitch Temple recipe");
    if (value.effects.some((e) => !e || !effectDefinitions.some((d) => d.type === e.type) && e.type !== "wavelet-chamber")) throw new Error("This recipe uses an unavailable effect");
    const recipe = normalizeRecipe(value);
    for (const key of ["renderWidth", "renderHeight"]) if (value[key] != null) recipe[key] = Math.max(1, Math.min(3840, Math.round(value[key])));
    recipe.renderSize = Math.max(recipe.renderWidth, recipe.renderHeight);
    for (const effect of recipe.effects) {
      const definition = definitionFor(effect.type);
      for (const p of definition.parameters) {
        const number = Number(effect.parameters[p.id]);
        if (!Number.isFinite(number)) throw new Error("Invalid value for " + p.label);
        effect.parameters[p.id] = Math.max(p.min, Math.min(p.max, number));
      }
    }
    return recipe;
  }
  function palette(value) {
    return applyPaletteSettings(normalize(value), {});
  }
  function vary(value, kind) {
    const recipe = normalize(value);
    if (kind === "structure") return nextStructure(recipe);
    if (kind === "colors") return nextColors(recipe);
    if (kind === "iteration") return nextZhuyinIteration(recipe);
    throw new Error("Unknown variation");
  }
  async function render(request) {
    const recipe = normalize(request.recipe);
    const width = request.width, height = request.height;
    recipe.renderWidth = width;
    recipe.renderHeight = height;
    recipe.renderSize = Math.max(width, height);
    const image = request.source ? await new Promise((resolve, reject) => {
      const im = new Image();
      im.onload = () => resolve(im);
      im.onerror = () => reject(new Error("Could not read the source image"));
      im.src = request.source;
    }) : null;
    await document.fonts.ready;
    const held = { ...recipe, seed: recipe.seed + recipe.iteration * 104729 };
    let surface = fittedSource(image, width, height, held);
    const original = cloneSurface(surface);
    const phase = request.phase ?? recipe.iteration % recipe.loopFrames / recipe.loopFrames * Math.PI * 2;
    let sourceBlended = false;
    for (const effect of held.effects) {
      if (effect.enabled && ["ascii-field", "zhuyin-weave", "petscii-study"].includes(effect.type) && !sourceBlended && held.sourcePresence > 0) {
        surface = blendSource(surface, original, held.sourcePresence);
        sourceBlended = true;
      }
      if (request.targetEffectId === effect.id) {
        surface = targetSurface(surface, effect);
        break;
      }
      surface = applyEffect(surface, effect, held, phase, Boolean(request.animated));
    }
    if (!request.targetEffectId && !sourceBlended) surface = blendSource(surface, original, held.sourcePresence);
    return { image: surface.toDataURL("image/png"), recipe, width, height };
  }
  return __toCommonJS(bridge_exports);
})();
