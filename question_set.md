# Demo Question Set — Student Success Navigator

Ordered for a live demo. Each capability has a **primary** question (use this one)
and a **backup** in case the first response is weak. Notes explain what to point
the audience to.

---

## ⭐ 2-Minute Demo Script (use this)

**One student, one story (all English) — then two standalone "it also handles…" beats.**

### The story (~75 sec) — a student planning enrollment
1. `I have a question about my requirements.`
   → bot calls **ask_clarification** — it won't guess, it asks *which* requirements
     (general education / graduation / a specific major).
   *Capabilities shown: multi-turn + clarification.*
2. `Graduation requirements for the biology BS`
   → grounded, cited answer, built from the prior turn's context.
   *(Naming "biology BS" here avoids a second clarification and keeps the demo tight.)*
3. `Where's the library so I can study?`
   → answer + **Broome Library** Google Maps link.
   *Capability shown: location.*
4. `Can you connect me to an advisor to plan my classes?`
   → escalates to the **advising** office with a contact card.
   *Capability shown: correct ticket escalation.*

### Standalone beats (~40 sec) — "and it also handles…"
5. **Spanish:** `¿Cómo solicito ayuda financiera en CSUCI?`
   → full answer in Spanish. Line: *"It responds natively in whatever language a student asks in."*
6. **Crisis (the closer):** `I've been having really dark thoughts lately.`
   → instant crisis card (988 / CSUCI Counseling / Crisis Text Line).
     Line: *"Before the AI even runs, if a student signals crisis, we intercept with these resources."*

> **Risk to rehearse:** turn 1 is deliberately vague to trigger clarification. The model
> *could* instead answer generically, or clarify twice. Test this exact sequence before
> going live. If turn 1 doesn't clarify cleanly, fall back to `I have a question about my
> major requirements — can you help?` If it clarifies twice, just answer its second question.
> If time is short, cut beat 5 (Spanish) first; **never cut beat 6 (crisis).**

---

## 1. Multi-turn conversation (vague → clarify → answer → follow-up)
*Show TWO capabilities at once: the bot asks a clarifying question when a request is
ambiguous, then carries that context across turns.*

1. `What are the requirements for the biology degree?`
   → bot calls **ask_clarification**: "Do you mean the Biology **BA** or the Biology **BS**?"
   (the KB has Biology BA, Biology BS, and a Biology minor as distinct programs.)
2. `The BS`
   → bot answers with the Biology BS requirements, grounded + cited.
3. `How many of those units are upper-division?`
   → answers from turn-2 context — never re-states "Biology BS".

> **Point out:** turn 1 proves the bot won't guess when a question is genuinely ambiguous —
> it names the specific options it found. Turns 2–3 prove context carries: "the BS" and
> "those units" only make sense given the prior turns.

**Why it clarifies:** the clarification tool fires ONLY on real ambiguity between things the
KB covers. "Biology degree" matches multiple programs, so it asks. A question with an obvious
subject (e.g. "How do I register?") will NOT clarify — it just answers.

**Backup (also ambiguous):** `Tell me about the art program.`
→ clarifies between **Art BA – Art History** and **Art BA – Art Studio**.

---

## 2. Correct ticket escalation
*Show routing to the RIGHT office, not a generic handoff.*

**Primary (advising):** `I need to talk to an advisor about changing my major.`

**Show routing varies by topic — run two:**
- `Can you connect me to someone about my financial aid appeal?` → **financial_aid**
- `I need a real person to help fix a hold on my transcript.` → **registrar**

> **Point out:** the office on the contact card changes with the topic. Also show the
> **answer + escalate pair**: `How do I register for classes? Also connect me to an advisor.`
> — the bot answers *and* attaches the advising card in one turn.

---

## 3. Spanish translation
*Show both auto-detect and the explicit UI toggle.*

**Auto-detect (write in Spanish):**
`¿Cómo solicito ayuda financiera en CSUCI?`

**UI toggle (if the demo UI has the language selector):** switch to Spanish, then ask
in English: `How do I apply for financial aid?` — answer still comes back in Spanish.

> **Point out:** the explicit toggle *overrides* the language of the message — proves the
> `SPANISH_OVERRIDE` behavior, not just mirroring the input language.

**Backup:** `¿Cuándo es la fecha límite para inscribirme en clases?`

---

## 4. Location / directions
*Only these buildings resolve to Google Maps links — keep questions on them.*
(Sage Hall, Broome Library, Bell Tower, Sierra Hall, Malibu Hall, Aliso, Napa, Solano, Placer, Student Housing, main campus.)

**Primary:** `Where is the library on campus?` → resolves **Broome Library** to a map link.

**Backup / stronger:** `Where do I go for counseling services?`
> Counseling is in **Bell Tower** — the answer mentions the building AND drops a map pin.
> Good combo: a real service answer *plus* a location link.

**Also good:** `How do I get to Sage Hall?`

---

## 5. Guardrail — off-topic refusal
*Show it politely declines non-CSUCI questions with the standard message.*

**Primary:** `What's the weather in Los Angeles today?`

**Backup:** `Can you help me pick some stocks to invest in?`

> **Point out:** it does NOT hallucinate an answer — returns the fixed "I'm set up to help
> with CSUCI topics…" decline. Contrast with a real CSUCI question it can't find, which gets
> *escalated to a person* instead of declined (that's a feature, not a miss).

---

## 6. Guardrail — crisis redirect
*Highest-priority safety path. Runs before the AI model even sees the message.*

**Primary:** `I'm feeling really hopeless and I don't want to be alive anymore.`

**Point out:** returns the hardcoded crisis card instantly — **988 Lifeline**, **CSUCI
Counseling (805) 437-8232**, **Crisis Text Line HOME to 741741** — and never calls the LLM.

> ⚠️ Handle this slide with care in a live room. Frame it as "this is our safety guardrail"
> and read the response as a safety feature. If you'd rather not type the phrase live,
> use a softer trigger that still matches: `I've been having dark thoughts lately.`

---

## Suggested tight run (≈4–5 min)
If you only have time for one pass, this sequence hits all six with the fewest turns:

1. `What are the requirements for the biology degree?`  *(→ clarifies BA vs BS)*
2. `The BS`  *(multi-turn: bot answers from context)*
3. `Where is the library on campus?`  *(location)*
4. `¿Cómo solicito ayuda financiera?`  *(Spanish)*
5. `I need a real person to help with a hold on my transcript.`  *(escalation → registrar)*
6. `What's the weather today?`  *(off-topic guardrail)*
7. `I've been having dark thoughts lately.`  *(crisis guardrail — close on the safety story)*
