# Prompts

Whisper accepts an *initial prompt*: a short block of text describing the audio.
It does not tell Whisper what to do — it primes the model's vocabulary, so proper
nouns, acronyms, and jargon come out spelled correctly instead of being guessed
phonetically. On domain-heavy audio this is the single biggest accuracy win
available, and it costs nothing.

## How to write one

Include, in this order:

1. **Type of conversation** — "Interview about...", "Weekly team meeting..."
2. **Context or institution**, if it matters
3. **Participants and roles**, with names if you know them
4. **Topic** — what specifically is being discussed
5. **Domain vocabulary** — technical terms, jargon, acronyms, product names
6. **Operational vocabulary** — recurring words these particular speakers use

## Two rules that matter

- **Write the prompt in the same language as the audio.** An English prompt on
  Spanish audio makes the output worse, not better. See the examples below.
- **Keep it under roughly 224 tokens** (~150-180 words). That is a hard limit in
  Whisper; anything past it is silently dropped. Spend the budget on vocabulary,
  not prose.

## Examples

- [examples/interview-en.txt](examples/interview-en.txt) — one-on-one interview, English
- [examples/meeting-en.txt](examples/meeting-en.txt) — multi-speaker meeting, English
- [examples/entrevista-es.txt](examples/entrevista-es.txt) — one-on-one interview, Spanish

These are generic templates with fictional organizations and names. Copy one,
swap in your own context and vocabulary, and save it as `prompts/<your-topic>.txt`.

## A note on privacy

`prompts/*.txt` is gitignored, and `prompts/examples/` is not. That split is
deliberate: a good prompt names real people, real employers, and real internal
projects, which makes it exactly the kind of file you do not want to publish by
accident. Keep your working prompts at the top level and they stay local.
