# Third-party provenance

- freeAudio by Surveyor123 and contributors, with acknowledged work by Gary Mp: https://github.com/Surveyor123/freeAudio ; commit f1ade61be7e5badd43dd9b58cba80ae26959148b. Original GPL version 2 text is in LICENSE. Original source headers and notices are retained in vendor/freeAudio.
- Python embedded runtimes already bundled upstream: licenses in vendor/freeAudio/python/x64/LICENSE.txt and python/x86/LICENSE.txt.
- BASS and its plug-ins are bundled upstream in vendor/freeAudio/bass. They have their own terms: https://www.un4seen.com/bass.html . BASS is not covered by the freeAudio GPL text. Check the applicable terms before commercial distribution; this preview grants no additional BASS rights.
- wxPython: https://wxpython.org/pages/license/index.html ; wxWindows Library Licence.
- accessible-output2 0.17: https://github.com/accessibleapps/accessible_output2 ; MIT. Bundled screen-reader controller DLLs retain their respective third-party terms, including NVDA controller LGPL terms.
- configobj: https://github.com/DiffSK/configobj ; BSD.
- packaging: https://github.com/pypa/packaging ; Apache-2.0 / BSD-2-Clause.
- comtypes: https://github.com/enthought/comtypes ; MIT.
- PyInstaller build tool: https://pyinstaller.org ; GPL with its bootloader distribution exception.
- Inno Setup compiler: https://jrsoftware.org ; its own license, used to produce the per-user installer.
- The upstream's 2018 FFmpeg executable is excluded from desktop packages and source distributions. FFmpeg-dependent functions use the external executable selected in Settings; obtain it separately from https://ffmpeg.org/download.html .
- Additional runtime dependencies and their installed license files are collected from the Python distributions by the build process.

No upstream repository has been modified or published by this task. No commercial licensing status or publisher identity is assumed.
