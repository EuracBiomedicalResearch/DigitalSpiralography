# -*- coding: utf-8 -*-
"""Drawing record basic statistics extraction/application"""

from __future__ import print_function

# local modules
from . import Data
from . import ID
from .Shared import dtts

# system modules
import datetime
import re


# get drawing statistics in tabular form
def get(record, cmts=False):
    rec_secs = None
    if record.recording.events:
        rec_secs = (record.recording.events[-1].stamp - record.recording.events[0].stamp).total_seconds()

    rec_data_cnt = 0
    for events in [record.recording.events] + record.recording.retries:
        if len(events):
            rec_data_cnt += 1

    data = {"PAT_ID": record.aid,
            "PAT_TYPE_ID": record.pat_type,
            "PAT_TYPE_DSC": record.config.pat_types.get(record.pat_type),
            "PAT_HANDEDNESS": Data.PAT_HANDEDNESS.get(record.pat_handedness, record.pat_handedness),
            "PAT_HAND": Data.PAT_HAND.get(record.pat_hand, record.pat_hand),
            "PAT_HAND_CNT": record.pat_hand_cnt,
            "OPERATOR": record.oid,
            "BLOOD_DRAWN": record.extra_data.get('blood_drawn'),
            "DRW_ID": record.drawing.id,
            "DRW_DSC": record.drawing.str,
            "CREATED_DATE": record.ts_created,
            "CREATED_TS": dtts(record.ts_created),
            "UPDATED_DATE": record.ts_updated,
            "UPDATED_TS": dtts(record.ts_updated),
            "REC_DATE": record.recording.session_start,
            "REC_NO": record.extra_data['drawing_number'],
            "REC_TS": dtts(record.recording.session_start),
            "REC_CYCLE": record.cycle,
            "REC_RETRIES": len(record.recording.retries) + 1,
            "REC_DATA_CNT": rec_data_cnt,
            "REC_STROKES": record.recording.strokes,
            "REC_EVENTS": len(record.recording.events),
            "REC_SECS": rec_secs,
            "CAL_OPERATOR": record.calibration.oid,
            "CAL_TID": record.calibration.tablet_id,
            "CAL_SID": record.calibration.stylus_id,
            "CAL_DATE": record.calibration.stamp,
            "CAL_TS": dtts(record.calibration.stamp),
            "CAL_AGE": record.calibration_age,
            "SCR_WIDTH": record.recording.rect_size[0],
            "SCR_HEIGHT": record.recording.rect_size[1],
            "PROG_VER": record.extra_data['version'],
            "PROG_FMT": record.extra_data['format'],
            "PROG_ORIG_VER": record.extra_data.get('orig', {}).get('version'),
            "PROG_ORIG_FMT": record.extra_data.get('orig', {}).get('format'),
            "INST_UUID": record.extra_data['installation_uuid'],
            "INST_DATE": record.extra_data['installation_stamp'],
            "INST_RECNO": record.extra_data['total_recordings'],
            "PROJ_ID": record.config.project_id,
            "PROJ_NAME": record.config.project_name,
            "TZ": record.tz}

    if cmts:
        comments = re.sub(r'[\t\n ]+', ' ', record.comments)
        data['COMMENTS'] = comments.strip()

    return data


# apply/override existing fields to the requested record
def set(record, data, ignore_unknown=True, force=False):
    old_data = get(record, True)

    for k, v in data.iteritems():
        # check for changes
        if k not in old_data:
            if not ignore_unknown:
                raise ValueError('Unknown key {}'.format(k))
            continue
        if unicode(data[k]) == unicode(old_data[k]):
            continue

        # original copy
        if 'orig' not in record.extra_data:
            record.extra_data['orig'] = {}
        lk = k.lower()
        if lk not in record.extra_data['orig']:
            record.extra_data['orig'][lk] = old_data[k]

        # update values
        if k == 'CAL_SID':
            if force or ID.validate_sid(v):
                record.calibration.stylus_id = v
            else:
                raise ValueError('{} is not a valid stylus ID'.format(v))
        elif k == 'REC_CYCLE':
            v = int(v)
            if force or (v > 0 and v <= (record.config.cycle_count * (record.pat_hand_cnt or 2))):
                record.cycle = v
            else:
                raise ValueError('{} is not a valid cycle count'.format(v))
        elif k == 'PAT_TYPE_ID':
            if force or not record.config.pat_types or v in record.config.pat_types:
                record.pat_type = v
            else:
                raise ValueError('{} is not a valid patient type'.format(v))
        elif k == 'PAT_HAND_CNT':
            v = int(v)
            if force or (v > 0 and v <= 2):
                record.pat_hand_cnt = v
            else:
                raise ValueError('{} in not a valid hand count'.format(v))
        elif k == 'PAT_HAND':
            if force or (v in Data.PAT_HAND.values()):
                record.pat_hand = Data.PAT_HAND.keys()[Data.PAT_HAND.values().index(v)]
            else:
                raise ValueError('{} in not a valid hand'.format(v))
        elif k == 'PAT_HANDEDNESS':
            if force or (v in Data.PAT_HANDEDNESS.values()):
                record.pat_handedness = Data.PAT_HANDEDNESS.keys()[Data.PAT_HANDEDNESS.values().index(v)]
            else:
                raise ValueError('{} in not a valid handedness'.format(v))
        elif k == 'PROJ_ID':
            record.config.project_id = v
        elif k == 'PROJ_NAME':
            record.config.project_name = v
        elif k == 'DRW_DSC':
            record.drawing.str = v
        elif k == 'COMMENTS':
            record.comments = v
        elif k == 'OPERATOR':
            record.oid = v
        elif k == 'TZ':
            record.tz = int(v)
        else:
            raise ValueError('{} cannot be set'.format(k))

        # update timestamp
        record.ts_updated = datetime.datetime.now()
