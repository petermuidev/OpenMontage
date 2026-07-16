# Voice Selection Contract

Voice is a production decision, not a language default. This contract adapts
the useful MoneyPrinterTurbo pattern—mode, provider, voice, preview—without
adopting its application or making another UI the system of record.

## Required order

```text
voiceover mode
→ narration language
→ desired delivery/tone
→ provider capability and cost
→ maximum three compatible voices
→ bounded preview
→ owner selects one voice
→ full synthesis
→ transcribe the actual audio
→ word-timed captions and scene alignment
```

Voiceover modes are separate decisions:

- `automatic`: synthesize through a selected provider and voice.
- `uploaded`: use owner-supplied narration; never regenerate it silently.
- `music-only`: no narration; captions may still be present.
- `silent`: intentional no-audio output for a specific delivery requirement.

## Agent command

Run from the controlled OpenMontage environment:

```bash
.venv/bin/python scripts/voice_select.py select \
  --language en-US \
  --tone luxury
```

Preview an explicit choice without provider substitution:

```bash
.venv/bin/python scripts/voice_select.py preview \
  --selected-voice edge_tts:en-US-ChristopherNeural \
  --text "Welcome to Koh Samui." \
  --output projects/example/assets/audio/voice-preview.mp3
```

The selector returns at most three ranked choices. It does not generate audio
in `catalog` or `select` mode. After the owner selects a voice, submit its
qualified `selection_id` (for example
`edge_tts:en-US-ChristopherNeural`) as `selected_voice_id` with
`operation=generate`. An unavailable selected provider
blocks; it never causes a silent provider or voice substitution.

## Provider truth

- Azure Speech `th-TH-PremwadeeNeural` has a live Thai probe in the owner truth
  inventory. Other Azure voices remain candidates until previewed.
- DashScope Qwen Jennifer is a verified English route. Qwen3 TTS is not the
  Thai route.
- Edge TTS is the free preview/default-cost lane. OpenMontage exposes the same
  provider contract used by the established social-automation narration flow;
  this does not replace that URL-native workflow.
- Unknown account pricing is never represented as free. Azure is still a paid
  provider call and requires the normal owner approval gate.

## Acceptance

- The chosen voice matches the approved language and intended register.
- Names and local place names are pronounced acceptably.
- The preview is approved before a full paid synthesis.
- Captions are timed from the generated or uploaded audio, not estimated from
  the script.
- Narration and every scene have a sentence-to-scene mapping.
- Provider, voice ID, language, rate, output hash, cost evidence and approval ID
  are recorded in the job artifacts.
