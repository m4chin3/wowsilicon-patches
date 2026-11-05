# Whitemane SkinLevels patch

Resolves visual artifacts on Whitemane caused by the SiliconPatch conflict
with Rebuffed SkinLevels. **For Whitemane players; based on LSP 3.3.0 Preview.**

## Changes

- Reconstructs 32-bit triangle-index starts from the submesh's upper word at
  `+2` and lower word at `+8`, preserving indices above 65,535.
- Replaces four index reads in the preview SiliconPatch rendering bodies for
  game functions `0x8203b0` and `0x829ba0`.
- Adds position-independent stubs in `.text` padding. The stubs preserve scratch
  registers and flags and replay displaced instructions.
- Extends `.text.VirtualSize` and updates the PE checksum.
- Retains all 217 initializer hooks, including `CM2Model::AnimateMT`.

Byte replacements and addresses are listed in `patches.json`.

## Install

**Whitemane-specific:** supports Rebuffed SkinLevels.
For the complete setup from cloning through launching, start with the
[package-root installation guide](../README.md).

For Whitemane's WotLK 3.3.5a client with Rebuffed SkinLevels support and
WoWSilicon's game mod-loader patch.

1. Quit WoW and select the Whitemane profile in WoWSilicon.
2. Open **Mods → Mod Manager → Install DLL…** and choose
   `libSiliconPatch_Whitemane_SkinLevels.dll` from this directory. WoWSilicon
   copies the DLL into the game's `mods/` folder and enables it.
3. Keep `winerosetta.dll` enabled and disable other SiliconPatch variants.

Alternatively, copy the DLL into `mods/` manually and enable it in Mod Manager.
The game root's `dlls.txt` should select:

```text
mods/winerosetta.dll
mods/libSiliconPatch_Whitemane_SkinLevels.dll
```

The Divx mod-loader hook must be present; client repair can remove it. The
Rosetta x87 runtime patch is installed separately. To disable this patch,
deselect this DLL in the Mod Manager.

## Build

Requires Python 3. Use the included binary-patch builder with the pristine
preview DLL with
SHA256 `2a845570706db093b2937057946e0c79b584d017f5d1eb2e9164c3da8ce70473`.

From this directory, using a new output filename:

```sh
python3 src/build_patch.py --source /path/to/libSiliconPatch_WOTLK_3.3.0_preview.dll \
  --output /private/tmp/libSiliconPatch_Whitemane_SkinLevels.dll
```

Output SHA256: `58de8c9edcd54d752c43cd641f0e868007c3bb036fe0c5cb77b0b032c21535da`.

Upstream preview DLL redistribution terms are not supplied with that binary;
the launcher's license does not establish a separate DLL license.
