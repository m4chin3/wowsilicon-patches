# WoWSilicon compatibility patches

Two fixes for World of Warcraft WotLK 3.3.5a on Apple Silicon running via WowSilicon 3.2.2:

- **Rosetta x87 crash fix — any server:** for WoWSilicon users experiencing
  seemingly random crashes caused by Rosetta's x87 state-recovery decoder. 
  If you have random game crashes (sometimes in populated areas like Dalaran), 
  this one is for you.
- **LSP DLL — Whitemane players:** This patch resolves visual artifacts caused 
  by the SiliconPatch conflict with Rebuffed SkinLevels. Based on the official
  **LSP 3.3.0 Preview** dll.

The patches can be installed independently. For the crash fix alone, use your
existing game profile and bottle, and follow step 2. The Whitemane DLL 
installation in step 3 is optional for Whitemane Frostmourne Rebuffed players.

**Target renderer: `mtld3d`**, using the `rosettax87` x87 backend in
WoWSilicon stable 3.2.2. Select these backends in the game profile before
launching.

## Requirements

- An existing WoWSilicon **stable 3.2.2** setup with its dependencies and Wine bottle.
- For the Rosetta patch: **macOS 27.2 (26B123)** with the matching Rosetta runtime.
- For the libSiliconPatch DLL: an updated Whitemane client with Rebuffed SkinLevels support
  and WoWSilicon's game mod-loader patch applied.
- Git and Python 3.

## 1. Clone and enter the package root

Replace `YOUR_REPOSITORY_URL` with the clone URL of the repository containing
these packages:

```sh
git clone YOUR_REPOSITORY_URL wowsilicon-patches
cd wowsilicon-patches
```

Check the included files:

```sh
shasum -a 256 -c SHA256SUMS
```

## 2. Install the Rosetta crash fix

**Default locations:**

- WS322: `/Applications/WoWSilicon.app`
- Whitemane: `~/Library/Games/Whitemane/FrostmourneRebuffed`

The Rosetta installer uses the app path; the game path comes from your
WoWSilicon profile. Use `--app '/path/to/WoWSilicon.app'` for a different app location.

Quit WoW and WoWSilicon, then run from the repo root:

```sh
python3 rosettax87/runtime/install.py
python3 rosettax87/runtime/install.py --apply
```

The first command checks compatibility. The second installs the patch and
creates a backup under `~/Library/Application Support/WoWSilicon/Backups/`.
Keep the printed backup path. An already-installed patch is left in place.

## 3. Install the Whitemane libSiliconPatch DLL

1. Quit WoW, then open WoWSilicon and select the **Whitemane** profile.
2. Open **Mods → Mod Manager → Install DLL…**.
3. Select `siliconpatch/libSiliconPatch_Whitemane_SkinLevels.dll`.
4. Keep `winerosetta.dll` and this DLL enabled. Disable other LSP variants.

WoWSilicon copies and enables the DLL. You can also copy it into the game's
`mods/` folder manually and enable it in Mod Manager.

Launch your game normally through WoWSilicon.

## Remove a patch

Disable the Whitemane DLL in Mod Manager to remove its effect.

For the Rosetta patch, quit WoW and WoWSilicon, then run:

```sh
python3 rosettax87/runtime/restore.py --backup '/path/printed/by/installer'
python3 rosettax87/runtime/restore.py --backup '/path/printed/by/installer' --apply
```

For an older backup containing game files, add `--runtime-only` to both commands.

## Source and changes

- [Rosetta x87](rosettax87/README.md): changes, full patched source, build instructions,
  and [MIT license](rosettax87/LICENSE).
- [Whitemane LSP](siliconpatch/README.md): changes, binary-patch source, and build
  instructions. [Exact byte replacements](siliconpatch/patches.json).
