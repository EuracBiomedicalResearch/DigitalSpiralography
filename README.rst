DrawingRecorder
===============

.. contents::


Overview
--------

How to use the recorder
~~~~~~~~~~~~~~~~~~~~~~~

1. Start the recorder.
2. Properly set a "save path" that will contain all the subsequent recordings.
3. Fit the paper onto the tablet, and ensure it doesn't move.
4. Calibrate:

   * Enter a Tablet ID, Pen ID and a Drawing ID (when using a barcode gun, zap
     the tablet, pen and the paper).
   * Hold the pen straight.
   * Move the pen over the red point indicated in the screen (which fills red),
     then press ENTER.
   * Repeat for all the points, until all points are green and the cursor
     appears as a crossbar.
   * Review that the pen matches the screen position/drawing by moving it over
     intersection points.
   * If it doesn't match properly, press TAB to reset.
   * When satisfied, press ENTER.

5. Press 'New Recording'.
6. Enter a valid Patient ID (when using a barcode gun, zap the AID).
7. Let the patient hold the pen straight and without touching the surface.
8. Let the patient draw a spiral *within* the spiral (in the space between the
   lines), starting from the center and outward.
9. Review that the drawing has no holes and/or jerkiness.
10. If the drawing has any problems, press TAB and repeat from step 7.
11. When satisfied, press ENTER.
12. Set the patient details (left/right handedness, hand used for drawing,
    patient/case) and eventually comments when needed.
13. Save the drawing.
14. Double-check that the paper still doesn't move. If the paper moves, repeat
    the calibration procedure from step 3.
15. Repeat from step 5 forcing the patient to use the other hand, or with a
    different patient.


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

1.3:

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
  + A new option "Next hand" has been added to preserve the patient data and
    automatically create a recording for the other hand.
  + Quality of the preview has been improved.

* A new tool ``StylusProfiler`` has been added:

  + Allows to profile the individual pressure response of each stylus.
  + Performs a simple quadratic fit of the response curve.
  + A new file format ``prof.yaml.gz`` has been designed for the purpose.

1.2:

* An exception caused by empty recordings was fixed.
* Internationalization of the Recorder/Visualizer interface.
* Add a new checkbox "Blood drawn on drawing arm" after finishing the recording
  and in the recorded data to reflect our new workflow.
* An image of the spiral is now shown after performing a recording.
* The name/id of the operator is now requested for each recording.

1.1:

* Locale issues under Windows were fixed (notably, DrawingRecorder would refuse
  to save a recording if the comment contained any accented letter).
* DrawingRecorder had a glitch that would sometimes cause a failure to start
  recording (requiring the user to release/press the pen again).
* Tablet enter/leave events are now also recorded, which improves "trace"
  tracking as "jumps" are now absent.
* Improved performance for high-throughput tablets (such as Intuos5).
* Tilt information is now recorded, both raw and corrected (file format 1.1).
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

- python 2.7 (python-2.7.3.msi)
- PyQt4 (PyQt-Py2.7-x86-gpl-4.9.4-1.exe)
- PyYAML (PyYAML-3.10.win32-py2.7.exe,
  use "Run as administrator" to avoid crashes during the setup)

Customize Windows 7 as follows:

- Control panel:

  + Pen & touch:

    - Pen options:

      * Disable press & hold

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

File formats
~~~~~~~~~~~~

The file formats are stored in self-descriptive GZip-compressed YaML_. GZip is
used both to conserve space (YaML is quite inefficient) and for check-summing
purposes.

To speed-up loading for repeated processing, ``drwconvert`` can be used to
convert an existing file into a "dump" object that loads faster. It's important
to note though that such dumps must not be used for distribution and are not
compatible across different versions.


Recorder ``rec.yaml.gz`` File format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Keys related to drawing/calibration (all keys are mandatory):

* ``drawing/points``: contains a list of coordinate pairs (from now on: points)
  in "normalized drawing space" that represent the the drawing to be reproduced
  (the spiral itself).
* ``drawing/cpoints``: contains a list of points in ''normalized drawing
  space'' that are expected to be used as ''reference points'' for the
  calibration procedure.
* ``calibration/cpoints``: contains a list of points, each point being in "raw
  screen-transformed" space in respect to the reference point in
  ``drawing/cpoints`` at the same position (as returned by the tablet/operator
  during the calibration).
* ``recording/events``: each event has at least two point pairs: ``cdraw`` and
  ``ctrans``:

  + ``cdraw`` contains *corrected* and "normalized drawing coordinates" as
    produced by the built-in DrawingRecorder calibration/alignment module.
  + ``ctrans`` contains *uncorrected* "raw screen-transformed" coordinates
    coming from the tablet.

* ``recording/rect_drawing``: contains the screen quadrilateral in effect to
  map the "raw screen-space" to "normalized drawing space".
* ``recording/rect_trans``: contains the screen quadrilateral in effect to map
  "*uncorrected* drawing-normalized" coordinates to "*corrected*
  drawing-normalized" coordinates.
* ``recording/rect_size``: the size of the screen during the recording.

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
  + ``ttrans`` (optional): rotation-adjusted x/y tilt information

* ``extra_data``:

  + ``blood_drawn`` (optional): reflects the new "Blood drawn on drawing arm"
    introduced in DrawingRecorder 1.2.

  + ``operator`` (optional): the name of the operator assisting during the
    recording (introduced in DrawingRecorder 1.2).

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


Profiler ``prof.yaml.gz`` File format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Keys related to the profile (all keys are mandatory):

* ``data``: list of data points, where each point contains:

  + ``press``: stylus pressure reported
  + ``weight``: applied weight

* ``fit``: 2nd degree polynomial fit of the response curve.

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


Coordinate projection types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several coordinate types and transformations are stored in the file itself.
It's important to understand how these coordinates are manipulated.

First, the coordinates coming from the tablet are mapped onto the screen (their
extension is 0x0 to screen's WxH). Since the tablet has a higher resolution
than that of the screen, the resulting coordinates are always floating point.
This space is called "raw screen-transformed space", as it's independent of the
tablet itself.

When the user draws on the tablet during the calibration (producing
``calibration/cpoints`` pairs) or during the recording itself
(``recording/events/ctrans``), the coordinates are mapped again, so that the
center of the spiral on the tablet matches the center of the spiral on the
screen.

The spiral on the screen though is always located at the ideal location 0x0,
with an extension of exactly 1x1. This is referred to as the "normalized
drawing space", which makes comparing different spirals trivial. The
quadrilateral in effect to transform "raw screen-trasformed" coordinates to
"normalized drawing coordinates" is stored in the ``recording/rect_drawing``
tree in the file. The resulting coordinate is then transformed again to correct
for the calibration points, by using the ``recording/rect_trans``
quadrilateral.

The full flow during the recording is thus:

1. raw coordinates coming from the tablet
2. scale to screen size ("raw screen-transformed space")
3. scale to drawing size ("*uncorrected* normalized drawing space")
4. correct for deformations ("*corrected* normalized drawing space")

Mappings from one coordinate space to the other can be performed by calculating
the affine matrix transforming the ideal quadrilateral [[-1,1],[1,-1]] to the
specified screen size, ``rect_drawing`` or ``rect_trans`` quadrilateral.
Storing the mapped quadrilateral (2x2 matrix) instead of the transform (3x3
matrix) allows for less rounding errors in less space. Transformation from "raw
screen-space" to "*uncorrected* normalized drawing space" is also always a
linear scaling operation, and thus also simpler to perform.

It's important to note that the ``recording/events/cdraw`` points and the
``recording/rect_trans`` quadrilateral itself can be recomputed from scratch in
case a flaw in the calibration or a better calibration model is found. These
coordinates are "redundant" on purpose. DrawingVisualizer allows to switch
between the uncorrected/corrected models.


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
* To be able to generate a score of the digitized spiral, we also need a sample
  of human-rated scores.
* Record the actual tablet serial/details in the file instead of relying on the
  user scanning a barcode.
* Add a pressure indicator during the calibration.
* Pressure has currently no reference value. Introducing pressure calibration
  would allow us to compare pressure among different tablets.


.. _YaML: http://www.yaml.org/
