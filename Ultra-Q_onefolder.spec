# -*- mode: python -*-

block_cipher = None

added_files = [
( 'src/company_logo.ico', '.' ),
( 'src/banner250x50.gif', '.' )
]

a = Analysis(['src/main.py'],
             pathex=['src'],
             binaries=None,
             datas = added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Device',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='company_logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Device')
