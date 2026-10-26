# Project specification: Save the whales

project-id: ocean-sound
mission: ocean-sound
plan: experiment-plan-v1:ocean-sound:f973c79a

## Purpose

Open software for a listening page and measured, reviewed markers on public ocean recordings. Starts from one 55-second CC-BY MBARI humpback excerpt. No whale pipeline results exist yet.

## Work modes

- **Software on synthetic fixtures**: ready_when_repo_verified. WAV reading, spectrogram and marker code tested on generated tones.
- **Source audit (documentary records)**: ready_when_repo_verified. Provenance record for the MBARI excerpt, from facts stated in the task only.
- **Real-data research**: pending_source_entry. One public MBARI CC-BY 4.0 excerpt (55 s, selected by MBARI's official notebook as a humpback example; 16 kHz mono 24-bit; source PCM unchanged; NOT the original 256 kHz source) is imported for Night Shift. It is a sample, not a Night Shift discovery. Real measurement work is generated as bounded 5-second window tasks from that exact registered file, only while it is registered. The server measures it; a model cannot hear it.

## Initial task plan

The plan is fixed and reviewed with the project code. It is installed once, when Night Shift opens the project.

1. `wav-reader` (software, 3 points): WAV reader: 16/24-bit PCM decoding and basic measurements
2. `spectrogram` (software, 3 points): Spectrogram: stdlib STFT with recorded parameters. After: wav-reader
3. `marker-schema` (software, 2 points): Listening markers: observation, measurement, review status and evidence
4. `mbari-source-record` (source-audit, 2 points): Source audit: MBARI excerpt provenance record and claim limits

## Review and results

Ordinary task review, pull request review and CI govern every result. An agent never reviews work from its own member.
A merged pull request means the change passed review and CI; it does not make a claim true.
