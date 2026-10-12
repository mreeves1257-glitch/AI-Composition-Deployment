"""A4 reference tuning at the instrument renderer; rhythm stays unchanged."""
import ctypes
import math

def validate_reference(value=440):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value not in (440, 432):
        raise ValueError('TUNING_REFERENCE_MUST_BE_440_OR_432')
    return float(value)

def apply_fluid_tuning(library, synth, channels, reference=440):
    reference = validate_reference(reference)
    if reference == 440:
        return
    pitches = (ctypes.c_double * 128)(*(note * 100 + 1200 * math.log2(reference / 440) for note in range(128)))
    create = library.fluid_synth_activate_key_tuning
    create.restype = ctypes.c_int
    create.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    activate = library.fluid_synth_activate_tuning
    activate.restype = ctypes.c_int
    activate.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    if create(synth, 0, 0, b'A4=432Hz', pitches, 0) != 0:
        raise ValueError('TUNING_SCALE_CREATION_FAILED')
    for channel in channels:
        if channel != 9 and activate(synth, channel, 0, 0, 0) != 0:
            raise ValueError('TUNING_CHANNEL_ACTIVATION_FAILED')
