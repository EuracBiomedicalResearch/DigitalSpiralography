DrawingRecorder
===============

.. contents::


Overview
--------

How to use the recorder
~~~~~~~~~~~~~~~~~~~~~~~

1. Start the recorder.
2. Properly set the correct project path.
3. Fit the paper onto the tablet, and ensure it doesn't move.
4. Calibrate:

   * Enter an Operator, Tablet ID, Pen ID and a Drawing ID (when using a
     barcode gun, zap the tablet, pen and the paper).
   * Move the pen over the red point indicated in the screen.
   * Hold the pen straight. When the point fills yellow, press ENTER.
   * Repeat for all the points, until all points are green and the cursor
     appears as a crossbar.
   * Review that the pen matches the screen position/drawing by moving it over
     intersection points.
   * If it doesn't match properly, press TAB to reset.
   * When satisfied, press ENTER.

5. Press 'New Recording'.
6. Enter a valid Operator and Patient ID (when using a barcode gun, zap the AID).
7. Let the patient hold the pen straight and without touching the surface.
   The patient must hold the other hand on the lap (to avoid moving the table).
8. Let the patient draw a spiral *within* the spiral (in the space between the
   lines), starting from the center and outward.
9. Review that the drawing has no recording issues.
10. If the drawing has any problems, press TAB and repeat from step 7.
11. When satisfied, press ENTER.
12. Set the patient details (left/right handedness, hand used for drawing,
    patient/case) and eventually comments when needed.
13. Save the drawing by pressing "Next hand", which will automatically cycle
    between hands until all the required spirals have been recorded.
14. Double-check that the paper still doesn't move. If the paper moves, repeat
    the calibration procedure from step 3.


Recording warnings
~~~~~~~~~~~~~~~~~~

**Multiple strokes**:

  There are some holes in the drawing (the pen was lifted while drawing), which
  might result in a recording which is more difficult to analyze. Consider
  repeating the recording.

**Short recording**:

  The recording was either very quick, or contained very few events. Check for
  potential problems.

**Old calibration data**:

  The last calibration was performed more than 8 hours ago and/or more than 50
  drawings ago. Ensure that the paper is still properly fitted.


Usage recommendation
~~~~~~~~~~~~~~~~~~~~

* Do not run concurrent applications while recording, as doing so may introduce
  jitter in the recording!
* Disable any feature of the tablet/pen: patients should not worry about
  pressing buttons accidentally on the tablet, and doing so should not
  interrupt the recording (this is described in the installation instructions).
* Do not change any pressure setting *ever* in the tablet/Wacom preferences.
  Follow the recommended configuration instructions precisely.
* If the sheet of paper moves and/or is wavy, replace it and *recalibrate*.
* When calibrating, hold the pen straight, then review the intersection points.
* The patient should be concentrated on the drawing, not on the screen.
  Turn away the screen from the patient.
* Review the drawing when the patient terminates. The drawing should consist of
  a single line without holes (watch out for unexpected jumps of the cursor,
  etc). If you see a problem with the drawing, reset with TAB and restart.


Testing
~~~~~~~

Codes that can be used for testing:

* AID: "0"
* Tablet ID: "T0"
* Pen ID: "S0"
* Drawing ID: "DSPR1"

To see how codes should be constructed, see `Coding of IDs`_.


Troubleshooting
~~~~~~~~~~~~~~~

* Windows 7/Wacom Intuos: During calibration, when pressing the pen onto the
  tablet, the point never fills red:

  The tablet might not be working correctly, or might not yet be ready. It
  seems that the Wacom drivers require up to 60 seconds after login to work.
  You can verify this problem by going to the control panel and clicking on the
  Wacom preferences link just after logging in (an error message will appear
  mentioning that there are no Wacom tablets connected).

  Wait at least 60 seconds after login before starting the Recorder
  application. Quit and restart the Recorder if necessary.

  If the Recorder still fails to recognize any pressure on the tablet, check in
  the Wacom preferences that the pen is working correctly.


Version changes
~~~~~~~~~~~~~~~

1.5:

* DrawingRecorder file format 1.4.
* ``drwstats/drwset`` now produce/parse the same data format and field names.
* ``profmap`` has been added in order to visualize the stylus profile
  correction over the study time span.
* ``surgen`` can read ``drwstats`` output files to generate usage reports that
  can be input to ``profmap``.
* DrawingRecorder shows the hand being recorded in the main header after the
  first patient details have been entered.
* DrawingRecorder can now require a comment to be given when patient details
  are being changed by the operator in the same recording session.

1.4:

* DrawingRecorder file format 1.3.
* DrawingVisualizer/``drwrenderer`` correctly draw spirals resulting from
  partial recordings (as generated by pressing RESET mid-flight).
* DrawingVisualizer samples the drawing speed only once, on demand.
* DrawingVisualizer shows stroke order/lifting points by default.
* DrawingVisualizer includes contrast/bias controls for speed and pressure.
* DrawingVisualizer supports fast-loading.
* StylusProfiler includes a "tare" field for improved calibration workflow.
* DrawingRecorder enforces a <5deg tilt while calibrating.
* DrawingRecorder blinks "RECORDING" when the event stream starts.
* DrawingRecorder shows the current spiral count/total after each recording.
* DrawingRecorder requires a "Project file" (``config.yaml``) to be present in
  the project path. This file defines the recording settings and patient types,
  which were previously fixed.
* DrawingRecorder saves the spirals in a YYYYMM sub-directory of the project
  path, to avoid directory performance issues on large studies.
* ``drwset/profset`` have been added to upgrade, update or dump attributes
  within existing drawings/profiles.
* ``drwconvert`` has been removed (superseded by ``drwset``).

1.3:

* DrawingRecorder file format 1.2.
* Several tools for data analysis have been added (``drwstats``,
  ``drwrenderer`` and ``drwstackrenderer``).
* Tools for analysis and DrawingVisualizer can now use 'dump' files to speed-up
  loading/saving time. ``drwconvert`` can convert between YaML/dump formats.
* A simple tool to generate and check IDs with a Verhoeff check digit
  (patient/table/stylus ID) has been added (``genverhoeff``).
* In DrawingVisualizer, the speed is now sampled to give more accurate results.
* An exception caused by an aborted calibration has been fixed.
* During calibration, the operator and stylus id are now being requested.
* All recorded trials (caused by pressing RESET while recording) are now saved.
* DrawingVisualizer can show recorded trials, when present.
* Default extension for recordings has been changed to ``rec.yaml.gz``, and a
  new ``type`` record has been added.
* The prompt dialog at the end of a recording has been extensively revised:

  + The operator id is now also included.
  + Patient handedness, drawing hand and blood drawn status are now mandatory
    (the user needs to check the appropriate option in all cases)
  + Quality of the preview has been improved.
  + A new option "Next hand" has been added to preserve the patient data and
    automatically create a recording for the other hand.
  + "Hand cycling" (first hand, second hand, first hand ...) is automatically
    performed, with 3 cycles being hard-coded, for a total of 6 spirals being
    requested per-patient.

* A new tool ``StylusProfiler`` has been added:

  + Allows to profile the individual pressure response of each stylus.
  + Performs a simple 3rd degree polynomial fit of the samples.
  + A new file format ``prof.yaml.gz`` has been designed for the purpose.

1.2:

* DrawingRecorder file format 1.1.
* An exception caused by empty recordings was fixed.
* Internationalization of the Recorder/Visualizer interface.
* Add a new checkbox "Blood drawn on drawing arm" after finishing the recording
  and in the recorded data to reflect our new workflow.
* An image of the spiral is now shown after performing a recording.
* The name/id of the operator is now requested for each recording.

1.1:

* DrawingRecorder file format 1.1.
* Locale issues under Windows were fixed (notably, DrawingRecorder would refuse
  to save a recording if the comment contained any accented letter).
* DrawingRecorder had a glitch that would sometimes cause a failure to start
  recording (requiring the user to release/press the pen again).
* Tablet enter/leave events are now also recorded, which improves "trace"
  tracking as "jumps" are now absent.
* Improved performance for high-throughput tablets (such as Intuos5).
* Tilt information is now recorded, both raw and corrected.
* Added the "DSPR2" drawing ID with the same spiral as DSPR1, but larger sheet
  for the Intuos5 tablet.


Known issues
~~~~~~~~~~~~

* 1.0/1.1: Quantization of event's timestamps: the "stamp" value of the event
  stream is badly quantized due to it not coming directly from the tablet.
  Unfortunately QT4 does not offer event timestamps. One must currently derive
  the device's event rate instead of relying on the timestamp for proper
  analysis.
* 1.0: Tablet enter/leave events not properly tracked: proximity events are
  still missing from the event stream, meaning that holes in the "trace"
  require post-processing to be detected, and doing so it not easy due to the
  quantization of event timestamps. This has been fixed in DrawingRecorder 1.1,
  but must be kept in mind for files produced by older releases.


Installation instructions
-------------------------

As an administrator, install in order:

- Python 2.7 (``python-2.7.3.msi``)
- PyQt4 (``PyQt-Py2.7-x86-gpl-4.9.4-1.exe``)
- PyYAML (``PyYAML-3.10.win32-py2.7.exe``)
- NumPy (``numpy-MKL-1.8.1.win32-py2.7.exe``)
- SciPy (``scipy-0.14.0c1.win32-py2.7.exe``)
- pyqtgraph 0.9.8 (``pyqtgraph-0.9.8.win32.exe``)

  * Expand ``pyqtgraph-0.9.8-patches.zip`` into Python's ``site-packages`` path.
  * Run ``pyqtgraph-recompile.bat``.

- Pip (``pip-install.bat``)
- Python Dateutil (``python_dateutil-install.bat``)

You'll need to use "Run as Administrator" (also for executing a prompt with
``CMD.EXE``) in order to make a system-wide installation.

Customize Windows 7 as follows:

- Control panel:

  + Pen & touch:

    - Pen options:

      * Disable press & hold
      * Disable visual feedback when touching screen

    - Flicks:

      * Disable flicks

  + Tablet PC settings:

    - Other:

      * Set left/right
      * Input panel settings:

	- Disable "For tablet pen input, show icon next to the text box"
	- Disable "Use the Input Panel tab"


Wacom/Bamboo drivers
~~~~~~~~~~~~~~~~~~~~

After performing the common installation/customization procedure, proceed by
installing in order:

- Wacom drivers (cons525-5a_int.exe)

Then customize the tablet preferences:

- Control panel:

  + Bamboo Preferences:

    - Tablet:

      * Set orientation
      * Disable all "Express Keys"

    - Pen:

      * Disable "Pan/scroll"
      * Mapping:

	- In a single-monitor setup, leave the default.
	- In a dual-monitor setup, set the pen to use the whole
	  area of the screen used for display.

    + Touch options:

      * Disable touch input


Wacom/Intuos drivers
~~~~~~~~~~~~~~~~~~~~

After performing the common installation/customization procedure, proceed by
installing in order:

* Wacom drivers (WacomTablet_634-3.exe)

After installing/rebooting, please move the pen *over* the tablet at least once
so that the Wacom driver shows it into the preferences.

Customize the tablet preferences as follows:

* Control panel:

  - Wacom Tablet Properties:

    + Options:

      * Disable "Pressure compatibility" (important!)

    + Tablet/Functions/All:

      * Express keys:

	+ Disable all "Express Keys"
	+ Disable "Show Express View"

      * Touch ring:

	+ Disable all corners
	+ Disable "Show touch ring setting"


    + Tablet/Touch/All:

      * Touch options:

	+ Disable touch input

    + Tablet/Grip pen/All:

      * Pen:

	+ Disable buttons (double/right click)

      * Eraser:

	+ Disable eraser

      * Mapping:

	+ Set orientation (usually "ExpressKeys Left")
	+ Screen area:

	  - In a single-monitor setup, leave the default.
	  - In a dual-monitor setup, set the pen to use the whole
	    area of the screen used for display.


Technical informations
----------------------

Stylus response profiling
~~~~~~~~~~~~~~~~~~~~~~~~~

The analysis modules will work with just the reported pressure, but for
comparable measures the real applied weight is required. ``StylusProfiler`` is
a simple tool that allows to build a response curve of the stylus.

.. important:: Never change the configuration settings for the stylus/tablet
  during the study; **especially** the settings for the pressure *feel*, as it
  would obviously make values incomparable.

Brand-new styluses will quickly drift between each single measurement, making
it impossible to get a reliable profile. The styluses need to be used for at
least ~20 recordings in order to get stable measurements.

It's recommended to perform a response profile as often as possible in order to
capture the response variability, especially during the first week of usage.
The analysis modules can load multiple profiles at different time points and
interpolate to get a reasonable estimate of the real weight.


Making a calibration profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start ``StylusProfiler`` and insert the basic parameters (operator,
tablet/stylus ID).

The data can be inserted either manually (by setting both "Pressure" and
"Weight") or by inserting "Pressures" as directly measured by the tablet by
putting the stylus on top of the tablet. When the stylus is on the tablet the
mouse cannot be used (use the key accelerators or TAB to move between fields).

Insert a (0,0) data-point manually first.

Put the stylus on a scale and measure/enter its weight. Put the calibrator base
on the tablet, then put the stylus in it by dropping it 2cm above its resting
position (to reduce nib friction). The "Pressure" field is automatically
populated. Press "Add" once the pressure is stable. This first measurement
constitutes the lightest measurable pressure.

Put the stylus in the reversed pusher plate, then measure both on a scale.
Enable the "Tare" field by pressing the "T" button and enter the base weight
which will also serve for further measurements. Put the stylus/plate onto the
base. Enter "0" as a weight and add the data-point.

Use a liquid in a light plastic container (a regular plastic cup is fine) to
measure the response at 25g intervals in 2 ramps:

* Start by measuring from the base weight in 50g intervals until the upper
  limit is reached (the reported pressure is the closest < 1).
* Hold the base while applying heavy weights on the pusher plate.
* Restart from the base + 25g and measure the remaining data-points at 50g
  intervals.

This protocol will reduce cumulative errors introduced by the response drift in
the upper range. When measuring the reported pressure, be sure to release the
weight on top the stylus *quickly* (it's easily done by dropping the weight
from 1-2cm above the pusher plate).

An easy way to check each measurement for potential drift is to lift/drop the
pusher plate before applying the weight, and check that the previous reference
value is *still matching*.

After all the 25g intervals are taken, to measure weights lower than the pusher
plate, use the tubes 2, 1+4, 1+2+5 in sequence by placing them onto the stylus
and measuring pen+tubes together first on a scale, then onto the tablet. Be
sure to disable the "Tare" (these are direct measurements). Each tube
combination increases by approximately 10g.


File formats
~~~~~~~~~~~~

The file formats are stored in self-descriptive GZip-compressed YaML. GZip is
used both to conserve space (YaML is quite inefficient) and for check-summing
purposes.

To speed-up loading for repeated processing, ``drwset`` can be used to convert
an existing file into a "dump" object that loads faster. It's important to note
though that such dumps must not be used for distribution and are not compatible
across different versions.

``drwset/profset`` can also export raw, unprocessed values into tabular text
files for other (usually debugging) purposes.


Project ``config.yaml`` File format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The project configuration file is required to be present in the project
directory, where the recorded spirals are also stored. It must be named as
``config.yaml`` and includes recording settings, patient types and study
details which are used for all subsequent recordings.

A sample file (with explanatory comments) is included in
``recordings/config.yaml`` which details all the required keys. Copy/customize
this sample file as required.


Recorder ``rec.yaml.gz`` File format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Keys related to drawing/calibration (all keys are mandatory):

* ``drawing/points``: contains a list of coordinate pairs (from now on: points)
  in "normalized drawing space" that represent the drawing as overlaid on the
  paper (the spiral itself).
* ``drawing/cpoints``: contains a list of points in "normalized drawing space".
  Each point is used as a calibration target, and is mapped to a different
  coordinate space in ``calibration/cpoints`` at the same list index.
* ``calibration/cpoints``: contains a list of points, with each point being a
  calibration target for ``drawing/cpoints`` but in the same coordinate space
  as ``recording/events/cdraw``.
* ``recording/events``: each event has at least two point pairs: ``cdraw`` and
  ``ctrans``:

  + ``cdraw``: points in the same coordinate space as ``calibration/cpoints``.
  + ``ctrans``: points in recorder's internal viewing space.

* ``recording/rect_drawing``: contains the screen quadrilateral in the same
  coordinate space as ``calibration/cpoints``.
* ``recording/rect_trans``:  contains the screen quadrilateral in the same
  coordinate space as ``recording/events/ctrans``.
* ``recording/rect_size``: the size of the screen (in pixels) during the
  recording.

Ancillary data (all keys are mandatory):

* ``format``: file format version (1.* describes this format)
* ``version``: application version
* ``aid``: patient AID
* ``drawing/id``: drawing ID
* ``drawing/str``: drawing description (redundant for human readability)
* ``calibration/tablet_id``: tablet ID used for calibration
* ``calibration/stamp``: timestamp of the last calibration
* ``calibration_age``: number of drawings since the last calibration
* ``recording/session_start``: timestamp of the start of the session (when the
  recording window is initially shown)
* ``recording/retries``: number of attempts required for a correct recording
* ``recording/strokes``: number of strokes in the recording (redundant for
  human readability)
* ``pat_type``: patient type
* ``pat_handedness``: patient handedness
* ``pat_hand``: patient hand
* ``comments``: free text comment for the recording

Chunks introduced with format 1.1:

* ``recording/events``:

  + ``tdraw`` (optional): *uncorrected* x/y tilt information expressed in +/-
    0-60 degrees for each axis.
  + ``ttrans`` (optional): rotation-adjusted x/y tilt information.

* ``extra_data``:

  + ``blood_drawn`` (optional): reflects the new "Blood drawn on drawing arm"
    introduced in DrawingRecorder 1.2.
  + ``operator`` (optional): the name of the operator assisting during the
    recording (introduced in DrawingRecorder 1.2, moved in 1.4).

Chunks introduced with format 1.2:

* ``type``: to distinguish file types (recording/profiles), type has been
  added, and needs to be ``rec`` when present.
* ``calibration/stylus_id``: stylus ID (introduced in DrawingRecorder 1.3)
* ``calibration/operator``: operator performing the calibration (introduced in
  DrawingRecorder 1.3)
* ``recording/retries_events``: An ''array'' of events with the same data and
  format as ``recording/events``, one for each trial during the recording.
  ``recording/retries`` is just the length of this array + 1 (for backward
  compatibility).
* ``pat_hand_cnt``: number of hands the patient is able to draw with.
* ``cycle``: cycle number in a single recording session.

Chunks introduced with format 1.3:

* ``ts_created``: drawing creation timestamp
* ``ts_updated``: drawing update (last change) timestamp
* ``operator``: the name of the operator assisting during the
  recording (moved from ``extra_data/operator`` in DrawingRecorder 1.4).

* ``extra_data``:

  These fields were introduced in DrawingRecorder 1.4 and moved in 1.5:

  + ``orig_format``: original file format version before the file has been
    re-saved. This field is created by ``drwset`` when a file has been
    upgraded from an older format, and is never overwritten.
  + ``orig_version``: original application version version before the file has
    been re-saved. This field is created by ``drwset`` when a file has been
    upgraded from an older format, and is never overwritten.
  + ``orig_pat_type``: original patient type before being modified by
    ``drwset``. This field is created by ``drwset`` when the patient type has been
    manually reset and is never overwritten.

Chunks introduced with format 1.4:

* ``tz``: timezone offset in seconds from UTC
* ``extra_data/orig``:

  Dictionary of initial values which have been changed when writing/updating an
  existing file. Existing values are never replaced. Keys include:

  + ``format`` moved from ``extra_data/orig_format`` in DrawingRecorder 1.5.
  + ``version`` moved from ``extra_data/orig_version`` in DrawingRecorder 1.5.
  + Any field name from the output of ``drwstats``.


Profiler ``prof.yaml.gz`` File format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Keys related to the profile (all keys are mandatory):

* ``data``: list of data points, where each point contains:

  + ``press``: stylus pressure reported
  + ``weight``: applied weight

* ``fit``: 3rd degree polynomial fit of the response curve. Can be ``null``.

Ancillary data (all keys are mandatory):

* ``format``: file format version (1.* describes this format)
* ``type``: "prof".
* ``version``: application version
* ``tablet_id``: tablet ID used for calibration
* ``operator``: the name of the operator performing the calibration
* ``stylus_id``: stylus ID currently being profiled
* ``ts_created``: profile creation timestamp
* ``ts_updated``: profile update (last change) timestamp
* ``extra_data``: provisional dictionary for arbitrary data.

Chunks introduced with format 1.4:

* ``tz``: timezone offset in seconds from UTC


Coordinate projection types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several coordinate types and transformations are stored in the file itself.

Coordinates that come directly from the tablet are mapped onto the screen (with
range 0x0 to screen's WxH). Since the tablet has a higher resolution than that
of the screen, the resulting coordinates are floating point.

When the user draws on the tablet during the calibration, the coordinates are
re-mapped so that the center of the tablet matches center of the drawing with
an unit-less scale and a square aspect ratio. This is the "drawing space" (as
stored in ``calibration/cpoints`` and ``recording/events/cdraw``).

The "normalized drawing space" uses information from the calibration points to
map the drawing to the unit length *and* direction using an affine transform.
By using such mapping it's possible to reconstruct the original drawing unit.


Coding of IDs
~~~~~~~~~~~~~

AID codes in the spirography software must be an all-numeric Verhoeff code. "0"
can be used here for testing purposes (which is still valid Verhoeff).

A tablet ID follows the pattern ``Txxxyyyz`` where:

* ``T``: mandatory
* ``xxx``: study code
* ``yyy``: incremental code
* ``z``: Verhoeff check digit

"T0" can be used for testing purposes.

A pen/stylus ID follows the pattern ``Sxxxyyyz`` where:

* ``S``: mandatory
* ``xxx``: study code
* ``yyy``: incremental code
* ``z``: Verhoeff check digit

"S0" can be used for testing purposes.

All drawing IDs currently begin with D have the structure ``Dxxxy``, where:

* ``D``: mandatory
* ``xxx``: drawing type
* ``y``: drawing number

Drawing IDs do not require a Verhoeff check digit, as the list of IDs is always
know to the recorder module.

The blueprints for the drawings are stored in the "drw/" directory in the
source code. Each drawing type is currently handled by a separated drawing
module, since the module itself contains the logic for proper calibration.


Future improvements
~~~~~~~~~~~~~~~~~~~

* Either fix PyQt4 to supplement device's timestamp to the QTabletEvent class,
  or use the pyglet's "wintab" module on Windows, which doesn't require
  re-compiling/patching PyQt.
* More drawing types (CCW, two spiral module, etc).
* Multiple drawings in a single session require rethinking a bit the output
  format (drawing/points needs to be a list of lists) and recording itself (do
  we want to perform drawing separation ourselves, or not?).
* Implement a batch analysis module.
* Record the actual tablet serial/details in the file instead of relying on the
  user scanning a barcode.
