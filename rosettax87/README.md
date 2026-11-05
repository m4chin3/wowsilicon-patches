# Rosetta x87 recovery patch

For WoWSilicon users on any server experiencing seemingly random crashes
caused by Rosetta's x87 state-recovery decoder. Resolves this crash condition
on the supported runtime configuration.

## Changes

- Adds `emit_f64_bits`, which loads floating-point bit patterns through an
  allocated scratch GPR using `MOVZ`/`MOVK` and a register-to-register `FMOV`.
- Uses this sequence for `FLD1`, other x87 constants, fused constant loads, and
  IR `ConstOne`/`ConstF64` lowering. These paths avoid immediate `FMOV` and
  inline literal data that conflict with Rosetta's state-recovery decoder.
- Adds `bzero` forwarding to `rt_memset` for AppleClang's freestanding-runtime
  linkage.

Updates `libRuntimeRosettax87` and retains the matching original `rosettax87`
loader.

## Install

The default setup uses `/Applications/WoWSilicon.app` for WS322 and
`~/Library/Games/Whitemane/FrostmourneRebuffed` for Whitemane. The Rosetta
installer uses only the app path (`--app` overrides it); select the game
path in WoWSilicon.

For the complete setup, including the separate Whitemane DLL, start with the
[package-root installation guide](../README.md). The commands below run from
this `rosettax87/` directory; the root guide uses root-relative commands.

Requires Python 3, WoWSilicon stable 3.2.2, and the matching macOS 27.2 (26B123)
Rosetta runtime. The installer rejects different loader/runtime baselines.

Quit WoW and WoWSilicon. From this directory:

```sh
python3 runtime/install.py
python3 runtime/install.py --apply
```

The first command checks compatibility; the second installs the companion,
backs up original files and app signature under the current user's
`~/Library/Application Support/WoWSilicon/Backups/`, and ad-hoc signs the app.
Launch through WoWSilicon normally afterward. Game files and mod selections
are separate from this installation.

For a different app location, add `--app '/path/to/WoWSilicon.app'` to both
commands. Keep the printed backup path. With WoW and WoWSilicon closed, restore
using that path:

```sh
python3 runtime/restore.py --backup '/path/printed/by/installer'
python3 runtime/restore.py --backup '/path/printed/by/installer' --apply
```

For older backups that also contain game files, add `--runtime-only` to both
restore commands to restore just the native app files and signature.

## Source and build

`src/upstream/` contains the patched source of
`Lifeisawful/rosettax87_jit` at commit
`e858b62292b16859d3fda53719756164a9e67ea2`. The two `.patch` files contain
the changes relative to that commit. The MIT license is in `LICENSE`.

Requires Xcode/Clang, CMake, and Python 3. Build from this directory:

```sh
python3 src/build.py --out /private/tmp/rosettax87-build
```

The build uses `Debug`, ARM64, and `-fno-stack-check`, and produces a
`runtime/` directory under the output path. Use a new output directory.
Rebuilt binaries can have different hashes across toolchains and build paths;
the installer payload is the binary supplied in this package.
