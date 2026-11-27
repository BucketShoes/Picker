# EXR layers -> 8-bit PNGs for the web viewer, HDR-safe and invertible:
#   x = linear * exposure;  y = (x / (1 + x)) ** (1/2.2)     decode: r = y ** 2.2;  x = r / (1 - r)
# blender -b -P export.py -- indir outdir exposure width
import bpy, sys, os, glob, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, EXP, W = a[0], a[1], float(a[2]), int(a[3])
os.makedirs(OUT, exist_ok=True)
for f in sorted(glob.glob(os.path.join(IN, "*.exr"))):
    img = bpy.data.images.load(f)
    w, h = img.size
    if w != W:
        img.scale(W, round(h * W / w)); w, h = img.size
    px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px)
    x = np.clip(px.reshape(h, w, 4)[..., :3] * EXP, 0, None)
    y = np.power(x / (1 + x), 1 / 2.2)
    out = bpy.data.images.new("o", w, h, alpha=False)
    out.pixels.foreach_set(np.concatenate([y, np.ones((h, w, 1), np.float32)], 2).ravel())
    name = os.path.splitext(os.path.basename(f))[0]
    out.filepath_raw = os.path.join(OUT, name + ".png"); out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out); bpy.data.images.remove(img)
    print("PNG", name, w, h)
