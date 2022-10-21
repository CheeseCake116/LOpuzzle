# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['slidePuzzle_3.py'],
             pathex=['C:\\Users\\CheeseCake\\PycharmProjects\\pythonProject'],
             binaries=[],
             datas=[('./잠금일러스트/*', './잠금일러스트'),
                    ('./잠금일러스트/조각1*', './잠금일러스트/조각1'),
                    ('./잠금일러스트/조각2*', './잠금일러스트/조각2'),
                    ('./잠금일러스트/조각3*', './잠금일러스트/조각3'),
                    ('./잠금일러스트/조각4*', './잠금일러스트/조각4'),
                    ('./잠금일러스트/조각5*', './잠금일러스트/조각5'),
                    ('./잠금일러스트/조각6*', './잠금일러스트/조각6')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='slidePuzzle_3',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
