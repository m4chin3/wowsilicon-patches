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
existing game profile and bottle, and follow step 3. The Whitemane DLL 
installation in step 4 is optional for Whitemane Frostmourne Rebuffed players.

**Target renderer: `mtld3d`**, using the `rosettax87` x87 backend in
WoWSilicon stable 3.2.2. Select these backends in the game profile before
launching.

## Requirements

- WoWSilicon **stable 3.2.2**, with its Wine dependencies and a Wine bottle.
- For the Rosetta x87 installer: the matching **macOS 27.2 (26B123)** Rosetta
  runtime. The installer enforces exact loader/runtime hashes and refuses
  incompatible versions.
- For the LSP DLL: an installed, updated Whitemane WotLK 3.3.5a client with
  Rebuffed SkinLevels support.
- Git and Python 3 available in Terminal. Building from source is optional;
  the DLL and native runtime are included.

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

## 2. Prepare WoWSilicon and the game

The steps below describe the combined Whitemane setup. For the native crash
fix alone, keep your existing client/profile and complete the dependency and
backend configuration before step 3.

1. Install the matching stable WoWSilicon 3.2.2 app, normally at
   `/Applications/WoWSilicon.app`. Select/create a Wine bottle through
   **Wine Bottle**, then install the dependencies listed below.
2. Install and update the Whitemane/Rebuffed client using its normal updater.
   Allow the client update to finish before applying the game mod-loader patch.
3. Add/select a WotLK 3.3.5a profile in WoWSilicon and point its game path at
   that install's `Wow.exe`. Use the `rosettax87` x87 backend. The matching
   renderer configuration is `mtld3d`.
4. Use WoWSilicon's **Patch** action for that game profile. This supplies the
   DLL loader and `winerosetta.dll` and patches `DivxDecoder.dll` to load mods.
5. Quit WoW and WoWSilicon before proceeding.

For an existing setup, use the existing Whitemane profile and bottle.
Use the configuration below before proceeding to the patch installations.

## Configuration: WS322

Use **WoWSilicon stable 3.2.2**.

### Dependencies and Wine bottle

In WoWSilicon, use its **bundled Wine** and select/create a Wine bottle through
**Wine Bottle**. The default location is `~/WoWSilicon`.

Under **Dependencies**:

- Install **Rosetta 2** if needed.
- Install **VC++ Runtime 2022** into the selected bottle if needed.
- **Wine Mono** is optional, for launchers that require .NET.

### Renderer and translation

Select your WotLK 3.3.5a profile and use:

| Control | Value |
|---|---|
| Graphics Backend | **`mtld3d`** |
| x87 Translation | **`rosettax87`** |
| HDR Mode | Off |
| Custom environment variables | Empty |
| Game path | Your client's `Wow.exe` |
| Game patch (for the Whitemane LSP DLL) | Applied through WoWSilicon |

The Vulkan Driver setting is inactive with `mtld3d` selected. Install the patched
native companion in step 3. For the Whitemane model fix, enable
`winerosetta.dll` and the SkinLevels DLL in step 4, with other SiliconPatch
variants disabled.

<details>
<summary>Optional graphics preset</summary>

Optional reference preset. Adjust resolution and refresh rate for your display.

| Setting | Value |
|---|---|
| Window Mode | Fullscreen |
| Resolution / refresh rate | 1920 × 1080 / 60 Hz |
| VSync | Off |
| Anti-Aliasing | 2× |
| Texture Filtering | Anisotropic 16× |
| Shadows | Off |
| Specular Lighting / Projected Textures | On / On |
| View Distance | 1227 |
| Ground Effects / Weather | Medium / Low |
| Particle Density | 60% |
| Cursor size multiplier | 2× |

For the frame caps, quit WoW and update these entries in `WTF/Config.wtf`,
preserving the rest of the file:

```text
SET maxFPS "60"
SET maxFPSBk "15"
```

</details>

## 3. Install the Rosetta x87 runtime patch

The default setup uses `/Applications/WoWSilicon.app` for WS322 and
`~/Library/Games/Whitemane/FrostmourneRebuffed` for Whitemane. The Rosetta
installer uses only the app path (`--app` overrides it); select the game
path in WoWSilicon.

From the **package root**:

```sh
python3 rosettax87/runtime/install.py
python3 rosettax87/runtime/install.py --apply
```

The first command checks compatibility without changing files. If it accepts
this setup, the second command installs the patched `libRuntimeRosettax87`,
backs up the original files and app signature, and ad-hoc signs the app. If the
patch is already installed, it reports that and leaves it in place.

Keep the backup path printed by the installer. Backups are stored under your
own `~/Library/Application Support/WoWSilicon/Backups/`. No account names or
machine-specific paths need to be edited in the scripts. The installer finds
its payload next to itself, so it also works when invoked by an absolute path
or from another working directory.

For an app installed elsewhere, use the same app path for both commands:

```sh
python3 rosettax87/runtime/install.py --app '/path/to/WoWSilicon.app'
python3 rosettax87/runtime/install.py --app '/path/to/WoWSilicon.app' --apply
```

The installer requires matching loader/runtime hashes and updates the
WoWSilicon app. Select the game DLL separately below.

## 4. Install the Whitemane SiliconPatch DLL

1. Quit WoW, then open WoWSilicon and select the **Whitemane** profile.
2. Open **Mods → Mod Manager → Install DLL…**.
3. Choose `siliconpatch/libSiliconPatch_Whitemane_SkinLevels.dll` from this repo.
   WoWSilicon copies it into the game's `mods/` folder and enables it.
4. Keep `winerosetta.dll` enabled/required and confirm the SkinLevels DLL is
   enabled. Disable other SiliconPatch variants so exactly one LSP is selected.

Alternatively, copy the DLL into the game's `mods/` folder manually and enable
it in Mod Manager.

Selection is stored in the game root's `dlls.txt`. The relevant entries, in
order, should be:

```text
mods/winerosetta.dll
mods/libSiliconPatch_Whitemane_SkinLevels.dll
```

Other intentional, unrelated mods may remain enabled. Do not overwrite their
entries when checking this file. Merely copying a DLL into `mods/` does not
select it; selecting it also requires the game mod-loader patch from step 2.

## 5. Launch the game

Launch your game profile normally through WoWSilicon and sign in to your
own game account. No special Terminal launcher is needed. The app uses the
installed native runtime. On Whitemane, the game loader also loads the
SkinLevels DLL when selected.

After a game repair/update, check the game's patch status and mod selection:
repair can restore `DivxDecoder.dll` and remove mod injection while leaving
`dlls.txt` in place. After a WoWSilicon reinstall/update, rerun the native
installer's compatibility check before applying this runtime again. A macOS
update may make the native patch incompatible.

## Remove the patches

To disable the Whitemane model patch, deselect its DLL in the Mod Manager.
Keep `winerosetta.dll` enabled where required by the WoWSilicon setup.

To restore the native runtime, quit WoW and WoWSilicon and use the backup path
printed during installation:

```sh
python3 rosettax87/runtime/restore.py --backup '/path/printed/by/installer'
python3 rosettax87/runtime/restore.py --backup '/path/printed/by/installer' --apply
```

For an older backup containing game files too, add `--runtime-only` to both
restore commands to keep your current game files and mod selection.

These two rollback actions are independent.

## What was patched and where the source lives

| Package | Changes | Source | Deliverable |
|---|---|---|---|
| [Whitemane SiliconPatch](siliconpatch/README.md) | Restores full triangle-index starts at four rendering reads, preserving Rebuffed SkinLevels indices above 65,535; updates `.text.VirtualSize` and PE checksum; retains all 217 hooks. | [Binary-patch builder](siliconpatch/src/build_patch.py), [PE helpers](siliconpatch/src/pe.py), [byte replacements](siliconpatch/patches.json) | [Patched DLL](siliconpatch/libSiliconPatch_Whitemane_SkinLevels.dll) |
| [Rosetta x87 runtime](rosettax87/README.md) | Replaces immediate floating-point constants and inline literal data with recovery-compatible register materialization in x87, fusion, and IR paths; adds `bzero` forwarding. | [Patched upstream source](rosettax87/src/upstream/), [constant-recovery patch](rosettax87/src/rosettax87-constant-recovery.patch), [build-support patch](rosettax87/src/rosettax87-build-support.patch), [build script](rosettax87/src/build.py) | [Runtime and installer](rosettax87/runtime/) |

Each package README includes build instructions. SiliconPatch includes the
binary-patch builder. The native package includes the full patched upstream
source and its [MIT license](rosettax87/LICENSE).
