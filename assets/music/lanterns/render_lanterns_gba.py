#!/usr/bin/env python3
"""Render the approved original Lanterns score as a small GBA-style PCM palette.

Only Python's standard library is needed. Source event data remains untouched.
Synthesis is additive and partials are bounded below Nyquist for both rates.
Each note retains its MIDI gate; finite timbral releases wrap into the start of
the cycle. Every export is therefore a periodic steady-state loop, not a file
with an appended tail or silence. No recordings or external soundbanks are used.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
import wave
from fractions import Fraction

DEFAULT_SOURCE = Path(__file__).resolve().parent / 'source'
TAU = math.tau
ROLES = ('melody', 'bass', 'inner')
PALETTE = (
    dict(name='soft pulse / triangle reed', gain=0.70, attack=0.0075,
         release=0.092, harmonics=((1,1.0),(2,0.105),(3,0.205),
         (4,0.032),(5,0.070),(7,0.034),(9,0.013)),
         vibrato_delay=0.260, vibrato_ramp=0.180,
         vibrato_rate=4.9, vibrato_cents=6.0),
    dict(name='rounded triangle bass', gain=0.43, attack=0.004,
         release=0.078, harmonics=((1,1.0),(2,0.018),(3,-1/9),
         (5,1/25),(7,-1/49),(9,1/81)),
         vibrato_delay=0.0, vibrato_ramp=0.0,
         vibrato_rate=0.0, vibrato_cents=0.0),
    dict(name='warm plucked inner voice', gain=0.30, attack=0.0022,
         release=0.058, harmonics=((1,1.0),(2,0.19),(3,0.085),
         (4,0.035),(5,0.016)),
         vibrato_delay=0.0, vibrato_ramp=0.0,
         vibrato_rate=0.0, vibrato_cents=0.0),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def midi_events(path):
    """Small strict SMF parser, independent of the approved JSON manifest."""
    data = path.read_bytes()
    if data[:4] != b'MThd' or len(data) < 14:
        raise ValueError('not a MIDI file')
    header_length, format_id, track_count, ppq = struct.unpack('>IHHH', data[4:14])
    if header_length != 6 or format_id != 1 or ppq & 0x8000:
        raise ValueError('expected format-1 PPQ MIDI')
    offset = 8 + header_length
    note_tracks, tempos, ends = [], [], []

    def vlq(buf, pos):
        value = 0
        for _ in range(4):
            byte = buf[pos]
            pos += 1
            value = (value << 7) | (byte & 127)
            if not byte & 128:
                return value, pos
        raise ValueError('invalid VLQ')

    for _ in range(track_count):
        if data[offset:offset+4] != b'MTrk':
            raise ValueError('missing MIDI track')
        size = int.from_bytes(data[offset+4:offset+8], 'big')
        buf = data[offset+8:offset+8+size]
        if len(buf) != size:
            raise ValueError('truncated MIDI track')
        offset += 8 + size
        pos, tick, running = 0, 0, None
        active, notes, controllers, programs = {}, [], [], []
        while pos < len(buf):
            delta, pos = vlq(buf, pos)
            tick += delta
            status = buf[pos]
            if status & 128:
                pos += 1
                if status < 240:
                    running = status
            else:
                if running is None:
                    raise ValueError('missing running status')
                status = running
            if status == 255:
                meta_type = buf[pos]
                pos += 1
                length, pos = vlq(buf, pos)
                payload = buf[pos:pos+length]
                pos += length
                if meta_type == 81:
                    tempos.append(int.from_bytes(payload, 'big'))
                if meta_type == 47:
                    ends.append(tick)
            elif status in (240,247):
                length, pos = vlq(buf, pos)
                pos += length
                running = None
            else:
                kind, channel = status & 240, status & 15
                a = buf[pos]
                pos += 1
                b = None
                if kind not in (192,208):
                    b = buf[pos]
                    pos += 1
                if kind == 144 and b:
                    if (channel,a) in active:
                        raise ValueError('overlapping identical MIDI note')
                    active[channel,a] = (tick,b)
                elif kind == 128 or (kind == 144 and not b):
                    start, velocity = active.pop((channel,a))
                    notes.append([start,tick-start,a,velocity])
                elif kind == 176:
                    controllers.append([tick,a,b])
                elif kind == 192:
                    programs.append(a)
        if active:
            raise ValueError('unterminated MIDI note')
        if notes:
            note_tracks.append(dict(notes=sorted(notes), programs=programs,
                                    controllers=controllers))
    if offset != len(data):
        raise ValueError('unexpected data after final MIDI track')
    return dict(ppq=ppq, tracks=note_tracks, tempos=tempos, end=ends)


def body_envelope(role, seconds):
    if role == 0:
        return (0.84 + 0.16 * math.exp(-seconds/0.038)) * math.exp(-0.08*seconds)
    if role == 1:
        return (0.76 + 0.24 * math.exp(-seconds/0.05)) * math.exp(-0.32*seconds)
    return math.exp(-seconds/0.180)


def render_note(role, note, rate, tick_seconds):
    onset_tick, duration_tick, pitch, velocity = note
    patch = PALETTE[role]
    gate = float(duration_tick*tick_seconds)
    total = math.ceil((gate + patch['release'])*rate)
    frequency = 440.0 * 2.0**((pitch-69)/12.0)
    # A shared 5.5 kHz spectral ceiling keeps the cheaper 16 kHz option close
    # to the 32 kHz one. Partial taper above 4 kHz avoids a hard spectral edge.
    ceiling = min(5500.0, rate*0.42)
    partials = []
    for harmonic, weight in patch['harmonics']:
        hz = harmonic*frequency
        if hz >= ceiling:
            continue
        taper = 1.0 if hz <= 4000 else 0.5*(1+math.cos(math.pi*(hz-4000)/(ceiling-4000)))
        partials.append((harmonic,weight*taper))
    # Spectral weight normalization compensates for the pitch-dependent upper
    # partial taper; velocity still multiplies the resulting tone linearly.
    partial_norm = sum(abs(w) for _,w in partials)
    gain = patch['gain']*(velocity/127.0)/partial_norm
    attack = patch['attack']
    gate_level = body_envelope(role,gate)
    samples = array.array('f')
    phase = 0.0
    max_step = TAU*frequency/rate
    for index in range(total):
        seconds = index/rate
        if seconds < gate:
            envelope = body_envelope(role,seconds)
            if seconds < attack:
                envelope *= math.sin(0.5*math.pi*seconds/attack)**2
        else:
            release_fraction = (seconds-gate)/patch['release']
            if release_fraction >= 1:
                envelope = 0.0
            else:
                envelope = gate_level*math.cos(0.5*math.pi*release_fraction)**2
        vibrato = 0.0
        if role == 0 and seconds > patch['vibrato_delay']:
            progress = min(1.0,(seconds-patch['vibrato_delay'])/patch['vibrato_ramp'])
            progress = progress*progress*(3-2*progress)
            vibrato = progress*patch['vibrato_cents']*math.sin(TAU*patch['vibrato_rate']*(seconds-patch['vibrato_delay']))
        tone = 0.0
        for harmonic, weight in partials:
            brightness = 1.0
            if role == 2 and harmonic > 1:
                brightness = math.exp(-seconds/0.095)
            tone += weight*brightness*math.sin(harmonic*phase)
        samples.append(gain*envelope*tone)
        phase += max_step*2.0**(vibrato/1200.0)
        if phase >= TAU:
            phase -= TAU
    return samples, frequency, [h for h,w in partials]


def render(source,rate):
    tick_seconds = Fraction(source['tempos'][0],source['ppq']*1_000_000)
    period = source['end'][0]*tick_seconds
    count = round(period*rate)
    stems = [array.array('f',[0.0])*count for _ in ROLES]
    sample_events, wrap_counts, max_error = [], [0,0,0], 0.0
    max_gate_end_error = 0.0
    for role,track in enumerate(source['tracks']):
        events = []
        for note in track['notes']:
            start = round(note[0]*tick_seconds*rate)
            nominal_gate_end = round((note[0]+note[1])*tick_seconds*rate)
            release_start = start + math.ceil(note[1]*tick_seconds*rate)
            error = abs(float(Fraction(start,rate)-note[0]*tick_seconds))
            max_error = max(max_error,error)
            gate_error = abs(float(Fraction(release_start,rate)-(note[0]+note[1])*tick_seconds))
            max_gate_end_error = max(max_gate_end_error,gate_error)
            samples,frequency,partials = render_note(role,note,rate,tick_seconds)
            if start+len(samples) > count:
                wrap_counts[role] += 1
            # Periodic accumulation includes previous cycle's final releases
            # at sample 0 without changing the first note's attack.
            for j,sample in enumerate(samples):
                stems[role][(start+j)%count] += sample
            events.append(dict(onset_tick=note[0],duration_tick=note[1],
                pitch=note[2],velocity=note[3],onset_sample=start,
                nominal_gate_end_sample=nominal_gate_end,
                envelope_release_start_sample=release_start,
                envelope_release_start_error_seconds=gate_error,
                equal_tempered_hz=frequency,
                active_harmonics=partials,release_seconds=PALETTE[role]['release']))
        sample_events.append(dict(role=ROLES[role],events=events))
    mixed = array.array('f',(sum(stem[i] for stem in stems) for i in range(count)))
    # One static master gain per render. No compressor, limiter, velocity
    # remapping, extra attacks, or change to source event timing.
    gain = 0.60/max(abs(x) for x in mixed)
    for i in range(count):
        mixed[i] *= gain
    return mixed,stems,sample_events,dict(sample_rate=rate,sample_count=count,
        exact_midi_cycle_seconds=float(period),actual_cycle_seconds=count/rate,
        cycle_rounding_error_seconds=float(Fraction(count,rate)-period),
        maximum_note_onset_rounding_error_seconds=max_error,
        maximum_envelope_release_start_rounding_error_seconds=max_gate_end_error,
        final_releases_wrapped_by_role=wrap_counts,static_gain=gain,
        direct_sound_asset_bytes=count,stream_bytes_per_second=rate,
        suggested_ping_pong_work_buffer_bytes=2048,
        period_alignment_bytes=count%16,
        asset_padding_policy='No padding is playable; streaming must wrap at sample_count.')


def db(value):
    return 20*math.log10(max(1e-12,value))


def measurements(samples,rate):
    n = len(samples)
    peak = max(abs(x) for x in samples)
    rms = math.sqrt(sum(x*x for x in samples)/n)
    differences = [abs(samples[i]-samples[i-1]) for i in range(1,n)]
    seam = abs(samples[0]-samples[-1])
    near_count = round(0.005*rate)
    near = list(samples[-near_count:])+list(samples[:near_count])
    sorted_differences = sorted(differences)
    return dict(peak_linear=peak,peak_dbfs=db(peak),rms_linear=rms,rms_dbfs=db(rms),
        dc_mean=sum(samples)/n,seam_adjacent_sample_difference=seam,
        seam_adjacent_sample_difference_dbfs=db(seam),
        seam_local_max_adjacent_difference=max(abs(a-b) for a,b in zip(near,near[1:])),
        ordinary_max_adjacent_difference=sorted_differences[-1],
        ordinary_99_9_percentile_adjacent_difference=sorted_differences[min(len(differences)-1,math.floor(len(differences)*0.999))],
        exact_two_cycle_recurrence=True,
        clipping_sample_count=sum(abs(x)>=1.0 for x in samples))


def wav(path,samples,rate,cycles=1):
    pcm = array.array('h',(round(max(-1,min(1,x))*32767) for x in samples))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(path),'wb') as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(rate)
        for _ in range(cycles):
            file.writeframesraw(pcm.tobytes())


def quantize_s8(samples):
    # Deterministic, first-order error feedback moves low-level quantization
    # noise upward. The error state is cycled to settle the periodic boundary;
    # the tiny TPDF dither itself repeats once per musical cycle. Both 8-bit
    # quantization and the finite-cycle nature are also exposed as WAV files.
    generator = random.Random(10496)
    dither = array.array('f',(0.35*(generator.random()-generator.random()) for _ in samples))
    error = 0.0
    result = bytearray(len(samples))
    for _ in range(3):
        for i,sample in enumerate(samples):
            value = sample*127 + 0.80*error + dither[i]
            quantized = max(-128,min(127,round(value)))
            error = value-quantized
            result[i] = quantized & 255
    decoded = array.array('f',((v if v<128 else v-256)/128.0 for v in result))
    return bytes(result),decoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=DEFAULT_SOURCE)
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--rates',type=int,nargs='+',default=[32768,16384])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    midi_path = args.source_dir/'lanterns_by_the_footbridge.mid'
    manifest_path = args.source_dir/'performance-manifest.json'
    source = midi_events(midi_path)
    expected = json.loads(manifest_path.read_text())
    assert source == expected,'MIDI differs from approved event manifest'
    assert source['ppq'] == 480
    assert source['tempos'] == [576923]
    assert source['end'] == [46080]*4
    assert [len(t['notes']) for t in source['tracks']] == [108,48,144]
    for track in source['tracks']:
        assert all(a[0]+a[1]<=b[0] for a,b in zip(track['notes'],track['notes'][1:])), 'source gate overlap'
    source_hashes = {p.name:sha256(p) for p in (midi_path,manifest_path)}
    report = dict(title='Lanterns by the Footbridge — original GBA-style palette',
        source_hashes=source_hashes,source_midi_equals_approved_manifest=True,
        source_note_count=300,track_note_counts=[108,48,144],source_ppq=480,
        source_tempo_microseconds=576923,nominal_tempo_bpm=104,
        source_tempo_bpm=60_000_000/576923,cycle_beats=96,bars=24,
        all_source_pitches_onsets_durations_and_velocities_preserved=True,
        palette=PALETTE,source_note_events=source['tracks'],
        source_controller_interpretation='Piano damper controllers are retained as provenance only; finite synthesizer release defines this palette.',
        synthesis='Original additive oscillators; no external samples; 5.5kHz partial ceiling and tapered upper partials; no drum or added notes.',
        auditory_review_performed=False,emulator_test_performed=False,
        physical_hardware_test_performed=False,
        limits='These signal and event checks do not establish audible balance, click-free playback, or gameplay integration approval.',
        renders={})
    for rate in args.rates:
        assert rate in (16384,32768),'supported rates are matched to GBA timer divisors'
        samples,stems,events,info = render(source,rate)
        base = f'lanterns-gba-{rate}'
        single = args.output_dir/(base+'-s16.wav')
        two = args.output_dir/(base+'-two-cycles-s16.wav')
        raw = args.output_dir/(base+'-s8.raw')
        quantized_wav = args.output_dir/(base+'-dma-audition-s16.wav')
        quantized_two = args.output_dir/(base+'-dma-two-cycles-s16.wav')
        wav(single,samples,rate)
        wav(two,samples,rate,2)
        raw_bytes,decoded = quantize_s8(samples)
        raw.write_bytes(raw_bytes)
        wav(quantized_wav,decoded,rate)
        wav(quantized_two,decoded,rate,2)
        noise_rms = math.sqrt(sum((a-b)**2 for a,b in zip(samples,decoded))/len(samples))
        event_path = args.output_dir/(base+'-events.json')
        event_path.write_text(json.dumps(dict(sample_rate=rate,tracks=events),indent=2)+'\n')
        info.update(s16=measurements(samples,rate),s8=measurements(decoded,rate),
            quantization_error_rms_dbfs=db(noise_rms),
            role_rms_dbfs_before_master_gain={ROLES[i]:db(math.sqrt(sum(x*x for x in stem)/len(stem))) for i,stem in enumerate(stems)},
            output_sha256={p.name:sha256(p) for p in (single,two,raw,quantized_wav,quantized_two,event_path)})
        report['renders'][str(rate)] = info
        print(f'{rate} Hz: {len(samples)} samples, {len(raw_bytes)} ROM bytes, peak {info["s8"]["peak_dbfs"]:.2f} dBFS, RMS {info["s8"]["rms_dbfs"]:.2f} dBFS, seam step {info["s8"]["seam_adjacent_sample_difference"]:.7f}',flush=True)
    # Verify that read-only original source files still have their initial hashes.
    assert source_hashes == {p.name:sha256(p) for p in (midi_path,manifest_path)}
    (args.output_dir/'render-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
