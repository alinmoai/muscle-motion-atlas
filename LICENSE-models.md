# Model data licence

The `LICENSE` file (MIT) covers the source code only.

The 3D models and the data computed from them are adapted from
[Z-Anatomy](https://github.com/LluisV/Z-Anatomy) by Lluís Vinent Juanico and contributors,
which is itself based on BodyParts3D (© The Database Center for Life Science).
They are licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

This covers:

- `site/dist/*.glb` (bone and muscle meshes, simplified and compressed)
- `site/dist/model.json` (joint centres and axes, muscle attachment points and paths, all derived from the meshes)
- everything the pipeline writes to `build/`

Changes made to the source models: right-limb bones and muscles extracted; meshes simplified and
compressed; joint centres, joint axes and muscle attachment paths computed from the geometry; the
upper and lower trapezius names corrected (they are swapped in the source); several muscle
attachments corrected (see `OVERRIDES` in `pipeline/bind.py`). Muscle names were translated into
Traditional Chinese.

If you redistribute these files or adaptations of them, credit the sources above and keep the
same licence.
