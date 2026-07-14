---
name: dashscope-media
description: Use Alibaba Cloud Model Studio HappyHorse image-to-video and Qwen3 TTS without inventing provider capabilities or bypassing cost and quality gates.
---

# DashScope media

Use this skill before calling `happyhorse_video` or `qwen_tts`.

## Region and credentials

The API key, model, and endpoint must belong to the same region. OpenMontage
supports `beijing` and `singapore`. Never print or persist an API key in a
project artifact. Prefer a workspace-specific endpoint through
`DASHSCOPE_BASE_URL` when the owner supplies one; the legacy regional endpoints
remain functional.

## HappyHorse first-frame image-to-video

- Use `happyhorse-1.1-i2v` unless a test explicitly targets 1.0.
- Exactly one first-frame image is required.
- Accept JPEG, PNG, or WEBP only; maximum 20 MB.
- Both image dimensions must be at least 300 pixels.
- Aspect ratio must be between 1:2.5 and 2.5:1.
- Duration is an integer from 3 through 15 seconds.
- Use 720P for the first bounded quality test. Move to 1080P only after the
  motion and composition pass review.
- Use a fixed seed for comparable prompt revisions, but do not promise byte-for-
  byte reproducibility.
- Poll the existing task. Never resubmit merely because generation takes time.
- Download a successful result immediately because task and result URLs expire.
- Generated motion is a creative insert, not evidence that an operator, room,
  view, facility, animal, product, or event really behaved that way.

Prompt order:

1. Preserve the source subject and geometry.
2. Describe one restrained physical motion.
3. Describe one restrained camera movement.
4. State what must remain unchanged.
5. Exclude text, logos, new objects, warping, and scene replacement unless the
   approved brief requires them.

For property and tourism source images, prefer subtle motion over spectacle.
Reject geometry drift, newly invented facilities, moving architecture, duplicate
objects, face deformation, broken boats, broken food, or implausible water.

## Qwen3 TTS

- Use non-real-time `qwen3-tts-flash` for production files.
- Set `language_type` to the script's actual single language; use `Auto` only for
  genuinely mixed-language input.
- Qwen3 TTS does not list Thai. Do not route Thai narration to it.
- Audition real output. Do not select a voice from its name alone.
- For English Samui editorial or commercial samples, begin with Jennifer
  (cinematic female), Ryan (dramatic male), and Aiden (younger American male),
  then approve one based on the actual script.
- Keep the first audition to one or two short lines.
- Transcribe the output and compare it with the approved script before using it.
- Do not time-stretch a poor read into alignment. Revise punctuation or choose a
  better voice, then regenerate one bounded sample.

## Required provenance

Record provider, model, region, voice or seed, request/task ID, estimated cost,
duration, dimensions, output hash, and QA disposition. Never record the signed
temporary output URL or API key.

Official references:

- https://www.alibabacloud.com/help/en/model-studio/happyhorse-image-to-video-api-reference
- https://www.alibabacloud.com/help/en/model-studio/qwen-tts-api
- https://www.alibabacloud.com/help/en/model-studio/qwen-tts-voice-list
- https://www.alibabacloud.com/help/en/model-studio/model-pricing
