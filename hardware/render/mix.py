# Mix linear EXR layers and write an sRGB PNG.  Light adds, so any combination is exact.
# blender -b -P mix.py -- indir out.png exposure "room=1,seat1=1,..."
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, EXP, spec = a[0], a[1], float(a[2]), a[3]
acc = None
for part in spec.split(","):
    name, k = part.split("=")
    img = bpy.data.images.load(f"{IN}{name}.exr")
    w, h = img.size
    px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3] * float(k)
    acc = px if acc is None else acc + px
x = np.clip(acc * EXP, 0, None)
# gentle shoulder so bright LED cores don't hard-clip to flat colour
x = x / (1 + x / 4.0) * 1.25
x = np.clip(x, 0, 1)
srgb = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
out = bpy.data.images.new("o", w, h, alpha=False)
rgba = np.concatenate([srgb, np.ones((h, w, 1), np.float32)], axis=2)
out.pixels.foreach_set(rgba.ravel())
out.filepath_raw = OUT; out.file_format = "PNG"; out.save()
print("SAVED", OUT)
