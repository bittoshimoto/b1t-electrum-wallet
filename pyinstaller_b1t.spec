# -*- mode: python -*-
import sys
import os
import glob
from typing import TYPE_CHECKING

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs, copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

if TYPE_CHECKING:
    pass


PYPKG="electrum"
MAIN_SCRIPT="run_electrum"
PROJECT_ROOT = os.getcwd()
ICONS_FILE=f"{PROJECT_ROOT}/{PYPKG}/gui/icons/b1t.ico"

cmdline_name = "b1t-electrum"

# see https://github.com/pyinstaller/pyinstaller/issues/2005
hiddenimports = []
hiddenimports += collect_submodules('pkg_resources')  # workaround for https://github.com/pypa/setuptools/issues/1963
hiddenimports += collect_submodules(f"{PYPKG}.plugins")


binaries = []
# Workaround for "Retro Look":
binaries += [b for b in collect_dynamic_libs('PyQt6') if 'qwindowsvista' in b[0]]

# Add libsecp256k1-0.dll from project root - embed into EXE
if os.path.exists(f"{PROJECT_ROOT}/libsecp256k1-0.dll"):
    binaries += [(f"{PROJECT_ROOT}/libsecp256k1-0.dll", '.')]

# Try to find libsecp256k1 DLLs from site-packages and embed them
try:
    import site
    for site_dir in site.getsitepackages():
        # Check for electrum_ecc package DLLs
        ecc_dir = os.path.join(site_dir, 'electrum_ecc')
        if os.path.exists(ecc_dir):
            for dll_file in glob.glob(os.path.join(ecc_dir, 'libsecp256k1-*.dll')):
                binaries += [(dll_file, '.')]
except Exception as e:
    print(f"Warning: Could not find libsecp256k1 DLLs: {e}")


datas = [
    (f"{PROJECT_ROOT}/{PYPKG}/*.json", PYPKG),
    (f"{PROJECT_ROOT}/{PYPKG}/chains", f"{PYPKG}/chains"),
    (f"{PROJECT_ROOT}/{PYPKG}/plugins", f"{PYPKG}/plugins"),
    (f"{PROJECT_ROOT}/{PYPKG}/gui/icons", f"{PYPKG}/gui/icons"),
    (f"{PROJECT_ROOT}/{PYPKG}/gui/fonts", f"{PYPKG}/gui/fonts"),
]

# Add optional data files if they exist
if glob.glob(f"{PROJECT_ROOT}/{PYPKG}/lnwire/*.csv"):
    datas.append((f"{PROJECT_ROOT}/{PYPKG}/lnwire/*.csv", f"{PYPKG}/lnwire"))
if os.path.exists(f"{PROJECT_ROOT}/{PYPKG}/wordlist/english.txt"):
    datas.append((f"{PROJECT_ROOT}/{PYPKG}/wordlist/english.txt", f"{PYPKG}/wordlist"))
if os.path.exists(f"{PROJECT_ROOT}/{PYPKG}/wordlist/slip39.txt"):
    datas.append((f"{PROJECT_ROOT}/{PYPKG}/wordlist/slip39.txt", f"{PYPKG}/wordlist"))
if os.path.exists(f"{PROJECT_ROOT}/{PYPKG}/locale"):
    datas.append((f"{PROJECT_ROOT}/{PYPKG}/locale", f"{PYPKG}/locale"))
datas += collect_data_files(f"{PYPKG}.plugins")
# Hardware wallet data files - only add if packages are available
try:
    datas += collect_data_files('trezorlib')
except:
    pass
try:
    datas += collect_data_files('safetlib')
except:
    pass
try:
    datas += collect_data_files('ckcc')
except:
    pass
try:
    datas += collect_data_files('bitbox02')
except:
    pass

# some deps rely on importlib metadata - only add if available
try:
    datas += copy_metadata('slip10')  # from trezor->slip10
except:
    pass

# Exclude parts of Qt that we never use. Reduces binary size by tens of MBs. see #4815
excludes = [
    "PyQt6.QtBluetooth",
    "PyQt6.QtDesigner",
    "PyQt6.QtNfc",
    "PyQt6.QtPositioning",
    "PyQt6.QtQml",
    "PyQt6.QtQuick",
    "PyQt6.QtQuick3D",
    "PyQt6.QtQuickWidgets",
    "PyQt6.QtRemoteObjects",
    "PyQt6.QtSensors",
    "PyQt6.QtSerialPort",
    "PyQt6.QtSpatialAudio",
    "PyQt6.QtSql",
    "PyQt6.QtTest",
    "PyQt6.QtTextToSpeech",
    "PyQt6.QtWebChannel",
    "PyQt6.QtWebSockets",
    "PyQt6.QtXml",
    # "PyQt6.QtNetwork",  # needed by QtMultimedia. kinda weird but ok.
]

# We don't put these files in to actually include them in the script but to make the Analysis method scan them for imports
a = Analysis([f"{PROJECT_ROOT}/{MAIN_SCRIPT}",
              f"{PROJECT_ROOT}/{PYPKG}/gui/qt/main_window.py",
              f"{PROJECT_ROOT}/{PYPKG}/gui/qt/qrreader/qtmultimedia/camera_dialog.py",
              f"{PROJECT_ROOT}/{PYPKG}/gui/text.py",
              f"{PROJECT_ROOT}/{PYPKG}/util.py",
              f"{PROJECT_ROOT}/{PYPKG}/wallet.py",
              f"{PROJECT_ROOT}/{PYPKG}/simple_config.py",
              f"{PROJECT_ROOT}/{PYPKG}/bitcoin.py",
              f"{PROJECT_ROOT}/{PYPKG}/dnssec.py",
              f"{PROJECT_ROOT}/{PYPKG}/commands.py",
              ],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             excludes=excludes,
             )


# http://stackoverflow.com/questions/19055089/pyinstaller-onefile-warning-pyconfig-h-when-importing-scipy-or-scipy-signal
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break


# hotfix for #3171 (pre-Win10 binaries) - not needed on native Windows
# a.binaries = [x for x in a.binaries if not x[1].lower().startswith(r'c:\windows')]

pyz = PYZ(a.pure)


# Standalone EXE-Dateien entfernt, da sie nicht korrekt funktionieren
# Nur die EXE-Dateien mit separaten Abhängigkeiten werden erstellt

#####
# exe and separate files that NSIS uses to build installer "setup" exe

# Standalone EXE with all dependencies included
exe_standalone = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f"{cmdline_name}.exe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=None,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=ICONS_FILE)

# Standalone Debug EXE with console
exe_debug = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f"{cmdline_name}-debug.exe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=None,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=ICONS_FILE)