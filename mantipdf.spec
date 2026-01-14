# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Determine the base path
base_path = os.getcwd()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('gui/icons', 'gui/icons'),
    ],
    hiddenimports=[
        'PyQt6.QtSvg',
        'PyQt6.QtPrintSupport',
        'qt_material',
        'fitz',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MantıPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if sys.platform == 'win32' else 'resources/icon.icns' if sys.platform == 'darwin' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MantıPDF',
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='MantıPDF.app',
        icon='resources/icon.icns',
        bundle_identifier='tr.gen.korkusuz.mantipdf',
        info_plist={
            'CFBundleName': 'MantıPDF',
            'CFBundleDisplayName': 'MantıPDF',
            'CFBundleGetInfoString': 'PDF Editor',
            'CFBundleIdentifier': 'tr.gen.korkusuz.mantipdf',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'PDF Document',
                    'CFBundleTypeRole': 'Editor',
                    'LSHandlerRank': 'Alternate',
                    'CFBundleTypeExtensions': ['pdf'],
                    'CFBundleTypeIconFile': 'icon.icns',
                }
            ],
        },
    )
