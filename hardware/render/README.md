# Lit renders

Path-traced renders of the board with its own LEDs as the light (Blender 4.0, Cycles, OptiX). Each seat's LEDs are
rendered alone in the dark, plus one render with only the room light. Light adds, so any mix of seats, brightness and
room light is exact: `mix.py` does it offline, `viewer.html` does it live in WebGL.

```
kicad-cli pcb export glb -f --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask -o board.glb ../pcb/picker-box.kicad_pcb
blender -b -P scene.py -- board.glb out all all 2048          # views x layers (room, seat1..8) -> linear EXR
blender -b -P export.py -- out web/img 7.15 1200              # EXR -> 8-bit PNG, x/(1+x) encoded, for viewer.html
blender -b -P mix.py -- out/side_ still.png 7.15 "room=1,seat1=1"
```

- Use absolute paths for the folders. Blender sometimes crashes on exit (or at the start of a run) after writing; re-run that view.
- 7.15 is the exposure that shows 18% grey at 300 lux as 0.18 (scene.py prints it).
- Physical numbers are at the top of `scene.py`: 40 mcd per LED (KT-0603R: 145-300 mcd at 20 mA per LCSC; the cell gives
  about 4 mA), 300 lux room. Materials are estimates.
- Model fixes made in the script: the holder's imported normals are dropped, the 1206 cap is recoloured, a CR2032 is
  added, and the JISP header is removed (holes only on the real board).
- The website idea: ship the 9 PNGs per view and mix in the page (as `viewer.html` does). Cross-fading plain stills
  works for one seat at a time; the mix also gives several seats at once, dimming, breathing, and any room level.
  The PNGs (about 16 MB for 5 views) aren't committed; regenerate them with the commands above.
