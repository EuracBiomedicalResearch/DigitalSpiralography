DrawingRecorder installation instructions
=========================================

As an administrator, install in order:

- python 2.7 (python-2.7.3.msi)
- PyQt4 (PyQt-Py2.7-x86-gpl-4.9.4-1.exe)
- PyYAML (PyYAML-3.10.win32-py2.7.exe,
  use "Run as administrator" to avoid crashes during the setup)
- Wacom drivers (cons525-5a_int.exe)

After installing the Wacom drivers, you have to tune the following settings in
a Windows 7 installation:

- Control panel:
  - Pen & touch:
    - Pen options:
      - Disable press & hold
    - Flicks:
      - Disable flicks
  - Tablet PC settings:
    - Other:
      - Set left/right
      - Input panel settings:
        - Disable "For tablet pen input, show icon next to the text box"
        - Disable "Use the Input Panel tab"
  - Bamboo Preferences:
    - Tablet:
      - Set orientation
      - Disable all "Express Keys"
    - Pen:
      - Disable "Pan/scroll"
      - Mapping:
	- In a single-monitor setup, leave the default.
        - In a dual-monitor setup, set the pen to use the whole
	  area of the screen used for display.
    - Touch options:
      - Disable touch input
