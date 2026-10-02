# Build brief: one chapter of "From a full buffer to BBR"

You are building **one chapter page** of a book-guided learning dossier. The "book" is a reading list of papers and articles. Chapter 1 (`ch01.html`) is finished and approved by the reader, and it is your **reference implementation**. Match its structure, components, voice, density and verification standard. A coordinator integrates your chapter into the hub afterwards.

Dossier folder: `~/workspace/repos/linux-networking-playground/queueing-to-bbr/`. Work from there.

## 1. Read first, in this order

1. The spec, **in full**: `~/workspace/learning/agent-directory/BOOK_GUIDED_BLOG_STYLE_LEARNING.md`. Every rule in it applies. The sections below only add to it or pin choices down.
2. `ch01.html`, the whole page, source and text. Copy its `<head>` (stylesheet, KaTeX CSS and scripts), the hero, the toc, the section skeleton, the card markup, the quiz-card prompt wording, the footer and the scripts block.
3. `NOTES.md`: the reader contract (including the 2026-10-02 rules), book facts (PDF→printed offsets), the errata list, "Since the sources", the bench, and the decisions log.
4. Your chapter's inventory, if one exists: `notes/inventory/inv-NN.md`. Inventories were written by other agents for planning. **Re-verify every page number, number and file:line you take from one.**
5. Every chapter already built (`ch0*.html`, `ch1*.html`): read their word lists and the learnings you will point back to.
6. Your sources, **in full**, from the files. Use `pdftotext -layout` for text, and open PDF pages with the Read tool to check figures, equations, tables and anything you quote. Extracted text garbles maths.

## 2. What you write, and what you must not touch

You write only:
- `chNN.html`, your page.
- `labs/chNN-<slug>/`: scripts, starter files, and `data/` holding the CSVs or transcripts from your real runs, with a `README.md` like `labs/ch01-aimd/data/README.md`.
- `notes/plots/chNN_plots.py`, if you have plots. Import `svgplot.py`, write `notes/plots/chNN-*.svg`, and splice each one into your page between `<!--PLOT:name-->` and `<!--/PLOT:name-->` markers inside `<div class="plot">`. See `notes/plots/ch01_plots.py`.
- `notes/chapters/chNN.md`, your chapter notes (section 9).

**Do not edit:**
- `assets/*`, `audit.py`, `notes/plots/svgplot.py`, `notes/katexify.py`, `labs/common/*`, `index.html`, `NOTES.md`.
- Any other chapter.

If you need a change in one of these, put it under "Requests" in your chapter notes and work around it locally. Example: copy a helper into your lab folder and extend it there. Other builders work in parallel.

## 3. Page rules on top of the spec

- **Skeleton:** `ch01.html`'s skeleton.
  - Hero crumbs: `chapter N of 14`.
  - `chnav`:
    - Left: `<a href="chPREV.html">← PREVIOUS TITLE</a>`.
    - Middle: `<a href="index.html">All chapters</a>`.
    - Right: `<span>NEXT TITLE → (not built yet)</span>`. The coordinator links it later.
  - Footer: name your reading(s) with edition and printed pages.
- **Maths is KaTeX, always** (reader request). Every formula, variable, Greek letter, sub/superscript and worked equation in prose uses inline `\( … \)`: body, captions, answers, hints, solutions, word lists. Write `\(552 \times 8 / 230{,}400 = 19.2\)` ms, `\(\rho\)`, `\(P_b\)`, `\(W/2\)`, `\(A + 4D\)`. Display maths uses `\[ … \]`; use `aligned` for anything wide, because the column is narrow. Never use `$`. Code, Mermaid labels, SVG text and quiz prompts stay plain text. Inside KaTeX in HTML, write `<` as `&lt;`.
- **Derivations** go in `<details class="deriv"><summary>Derivation · what it shows</summary> … </details>` (reader contract: "use it, derive in toggles"). The page must read without opening them. State each result in words and use it on real numbers in the visible text.
- **Diagrams:**
  - Every figure is `<figure class="dia">`, and its first child is `<div class="mermaid">` or `<div class="plot">`. The zoom bar attaches to that holder.
  - About three figures per chapter: one in the before half, at least one in the after half.
  - Captions start `Diagram N.M — <what it is>.` and continue with "Notice …".
  - Mermaid traps (spec §12.6): quote every label, no `&` `<` `>` in labels, no self-loops in `stateDiagram` (put the rule in the state box instead, as `ch01.html` Diagram 1.4 does).
- **Plots** follow `svgplot.py`:
  - 2px lines, hairline grid, text in ink colours, a legend for 2+ series, direct end labels, a hover layer.
  - Colours from the validated palette slots `SLOT[0..3]`.
  - Measured data comes from your own runs, with the CSV linked in the caption as the table view.
  - A model plot says "This is a model" in its caption.
  - Render each SVG with `rsvg-convert` and look at it before it ships.
- **Vocabulary** (spec §1.2):
  - Word list of 6–12 terms, `<dt id="w-SLUG">`. The coordinator copies it to the hub glossary as `g-SLUG`.
  - A term from an earlier chapter is used freely, but on its first use in your page link it as `<a href="index.html#g-SLUG">term</a>`. Slugs are in section 5. For built chapters, take the slug from their `<dt id="w-…">`.
  - A term from a **later** chapter must not appear in your page. Use plain words and describe the later chapter by what it does ("the chapter on departure timestamps"); the audit flags later terms even inside chapter names.
  - The audit's terms map lists later-chapter terms; run it.
- **Voice:** spec §6, plus the learner profile's bans (leak, hurt, bites, substrate). Simple spoken English, short sentences, compact. No "X, not Y" sentences. No em-dash prose. Name things; never use bare numbers ("the CoDel chapter (chapter 3)", not "chapter 3").
- **Page references:** printed page numbers, using the offsets in NOTES "Book facts". The pacing paper has no printed numbers, so use PDF pages. Cite man pages, LWN articles and slides by section name, slide number or message.
- **Since the paper** (`<p class="since"><b>Since the paper.</b> …`): dated, sourced, verified. Check the kernel tree at `~/workspace/repos/linux` (v7.2) for every `file:line` you cite, by grep.
- **Paper errors** (`<p class="erratum"><b>The paper's slip.</b> …`): only after you re-verify against the rendered page. Use errors from NOTES "Errata" or new ones you can prove.
- **URLs:** verify every one with `curl -sL -o /dev/null -w '%{http_code}'` (DOIs via Crossref `api.crossref.org/works/<doi>` when ACM blocks curl). Never invent a link.
- **Budget:** before half about 5–8 min. After half: aim ≤ 22 min (about 4,400 words). The audit flags over 25 min. State the measured minutes in `chmeta`.
- **Questions:** 5–7, covering the framing mix in spec §9.2.
  - At least one predict-the-value (with the arithmetic), at least one "here is a symptom", one choose-and-defend, and at most two recall.
  - Every answer has a `<details class="ans">` of at least 35 words that names the mechanism and the page.
  - Chapter 2 uses the textbook's problems (`.bookq`, spec §9.1).
- **Quiz cards:** the strand list must equal your `<h3 class="strand" id="s-…">` set. Prompts follow `ch01.html` word for word, with your chapter number, title, source and pages, and the map file `.alvar/maps/qbbr-chNN.md`.

## 4. Labs and the bench

- **Rootless bench:** `labs/common/qnet.sh` builds snd → rtr → rcv inside `unshare --user --map-root-user --net --mount`.
  - Defaults: netem rate 10mbit, limit 50, 20 ms each way, offloads off. Read its header for the options.
  - You can replace the bottleneck qdisc inside the lab with `tc -n rtr qdisc replace dev r1 root …`.
  - netem, tbf, htb, fq, fq_codel, codel, drr, hfsc, etf and cake all work rootless.
  - `flow.py` sends bulk traffic and samples `TCP_INFO` to CSV; `qwatch.py` samples a qdisc's backlog and drops.
  - Copy and extend them inside your lab folder when you need more: several flows, `TCP_CC_INFO`, `SO_TXTIME`, `SO_MAX_PACING_RATE`, a UDP sender. Do not edit `labs/common`.
- **Run every solution** and paste real output into the page, dated, with the CSV or transcript saved under `labs/chNN-*/data/`.
- **Cannot run without the reader's sudo:** bpftrace, loading tc BPF programs (`kernel.unprivileged_bpf_disabled = 2`), and `tcp_bbr` while it is not loaded. Check `cat /proc/sys/net/ipv4/tcp_available_congestion_control`; if `bbr` is missing, the reader has not run `sudo modprobe tcp_bbr` yet.
  - Write such labs so the reader can run them, and mark the solution **"not executed: needs sudo"**, with the expected shape described from the source code and the paper.
  - Also give the reader at least one lab that runs rootless.
- **Commands the reader pastes must be fish-safe:** no bare `VAR=value` lines, `for … end` loops only, `$HOME` instead of `~` inside `VAR=` prefixes. `cmd &`, `wait` and `sleep N; cmd` are fine. Start lab commands with `cd labs/common` or `cd labs/chNN-…`, "from the dossier folder"; never put the dossier folder's own name in a command.
- At least one lab per chapter needs no environment (paper and pencil). Two or three labs per chapter, each with a hint ladder, a solution, and a "Common wrong turn".
- Never install packages. `iperf3`, `ipvsadm`, `tshark` and `netperf` are absent: list them as optional prerequisites, never as requirements.
- Your runs share the CPU with other builders' runs. At 10 Mbit/s that does not matter. If you measure CPU cost, say the machine was shared.

## 5. Cross-chapter contracts

**Real systems.** These are the fixed full-card owners. Everyone else writes a back card linking to `chNN.html#sys-SLUG`. `data-system` is the slug.

| slug | system | full card in |
|---|---|---|
| linux-tcp | Linux TCP read through `ss -ti` | ch01 (done) |
| netem | netem, the kernel's network emulator | ch02 |
| fq-codel | the Linux qdisc layer and `fq_codel`, plus mac80211's built-in fq_codel on the reader's `wlan0` | ch03 |
| htb | HTB (and TBF) through `tc` classes | ch04 |
| sch-fq | `sch_fq`, the fair-queue and pacing qdisc | ch05 |
| bpftrace | bpftrace | ch05 |
| so-txtime | `SO_TXTIME` and the ETF qdisc | ch08 |
| tcp-bbr | Linux `tcp_bbr`, read through `ss -ti` | ch10 |
| cilium-bwm | Cilium Bandwidth Manager (EDT in BPF, plus BBR for pods), from the reader's fork | ch12 |
| cilium-maglev | Cilium's Maglev in kube-proxy replacement, from the reader's fork | ch13 |
| linux-gso | GSO/GRO size knobs (`gso_max_size`, `gro_max_size`) and BIG TCP | ch14 |

The reader's Cilium fork is at `~/workspace/neverinstall/cilium` (v1.19.6-vpc). Cite it by `file:line`. Cilium's 1.20 docs are saved in `~/Documents/Books/networking/routing-papers-bbr/extra/cilium-docs/`. The docs say the Bandwidth Manager does not work in kind. Never change the reader's live kind cluster.

**Glossary slugs.** Planned word lists, with the slug each term will have (`index.html#g-SLUG`). Chapter 1's slugs are real. The rest are the plan: use these slugs for your own terms where they match. Chapter-local wording may differ.

- ch01 (built): congestion-collapse, conservation-of-packets, bottleneck, ack-clock, cwnd (congestion window), slow-start, ssthresh, rto (retransmit timeout), mean-deviation, exponential-backoff, aimd (congestion avoidance), pipe-size (BDP).
- ch02: littles-law, utilisation, poisson-arrivals, mm1 (M/M/1 queue), md1 (M/D/1 queue), pk-formula (Pollaczek–Khinchine), kleinrock-power, operating-point (Kleinrock's optimal operating point; the BBR chapter reuses it), mathis-formula, buffer-sizing-rule (BDP/√n), jain-index (Jain's fairness index).
- ch03: bufferbloat, aqm (active queue management), red, standing-queue, good-bad-queue, sojourn-time, target, interval, control-law, codel, flow-queueing (fq_codel).
- ch04: token-bucket, arrival-curve, shaper, policer, work-conserving, htb-class (with ceil and borrowing), quantum, max-min-fairness, gps (GPS and WFQ), drr (deficit round robin).
- ch05: tsq (TCP small queues), tso-autosizing, pacing, pacing-rate, fq-flow (sch_fq's per-flow state), new-old-lists, throttled-tree, bql (byte queue limits).
- ch06: slow-start-burst, ack-compression, paced-reno, synchronized-drops, late-congestion-signal, desynchronization.
- ch07: traffic-shaping, flow-aggregate, timing-wheel, slot-granularity, horizon, release-time, deferred-completion, backpressure, hol-blocking, calendar-queue.
- ch08: afap, edt (earliest departure time), skb-tstamp, clock-tai, so-txtime, etf.
- ch09: rank, integer-priority-queue, bucketed-queue, ffs (find first set), hierarchical-ffs, cffs, pifo, single-shaper.
- ch10: btlbw, rtprop, inflight, delivery-rate, app-limited, pacing-gain, cwnd-gain, bbr-states, windowed-filter.
- ch11: shallow-deep-buffer, loss-cliff, policer-mode, inflight-cap, bbrv3.
- ch12: tenant, hose-model, admissible-traffic, rcp, mono-delivery-time, edt-rate-limiter, bandwidth-manager, bbr-for-pods.
- ch13: vip, ecmp, gre, dsr, five-tuple, conntrack-table, consistent-hashing, maglev-table, offset-skip, disruption.
- ch14: gso-max-size, jumbogram, max-skb-frags, big-tcp.

**Point-backs.** Make earlier chapters do visible work (spec §6.2): "this is the ack clock from the congestion-avoidance chapter, now replaced by a timer". The bench numbers from chapter 1 (10 Mbit/s, pipe ≈ 33 packets, 50-packet queue, Reno sawtooth 42–83, queue never below 8) are shared ground. Reuse them where they fit.

**Capstone spine** (do not build it; just keep your chapter compatible): one 100 MB upload from a Cilium pod to a service VIP over a 10 Mbit/s, 40 ms path. NOTES "Connecting spine" has one line per chapter.

## 6. Verification before you report

1. `python3 audit.py chNN.html` must print `0 problem(s)` for your page. Ignore hub problems; the coordinator fixes those. Fix every EARLY USE by rewording.
2. Mermaid: extract each block and run mermaid-cli, which is already on the machine:
   `PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable ~/.npm/_npx/668c188756b835f3/node_modules/.bin/mmdc -i X.mmd -o X.png -b white -q`
   Then look at the PNG.
3. Render the page:
   `google-chrome-stable --headless=new --disable-gpu --no-sandbox --virtual-time-budget=20000 --no-pdf-header-footer --print-to-pdf=/tmp/<you>/chNN.pdf file://$PWD/chNN.html`
   Then open several PDF pages with Read to check KaTeX, plots and diagrams. Work in your own `/tmp/qbbr-chNN/` scratch folder.
4. Re-read your prose once against the banned-word lists and banned shapes, and check that every diagram label uses only defined words.

## 7. Report (your final message, ≤ 350 words)

Report:
- What you built.
- The headline measured numbers.
- What was not executed and why.
- Errata found or confirmed.
- Before and after minutes.
- The audit result.
- Anything the coordinator must do: requests, cross-chapter terms you could not avoid, broken links to pages not built yet.

## 8. Writing order (spec §12.5)

Write the skeleton with `<!--APPEND-->` inside the after half. Then fill it in four or five edits, never one giant write:
1. The before half.
2. The carried answers, the one-screen summary and the learnings.
3. Systems and labs.
4. Questions, recap, go-deeper and the quiz card.

Remove the marker at the end.

## 9. Chapter notes file: `notes/chapters/chNN.md`

````markdown
# chNN — TITLE (built YYYY-MM-DD)
## Sources read            (files, printed pages, offset checks)
## Inventory               (sections with pages; core claims with pages; figures redrawn)
## Spine and strands
## Measured on the bench   (headline numbers; data files)
## Not executed            (and why)
## Errata and since-the-paper notes
## Systems                 (slug | one-line what | full or back)
## References used         (verified URL, layer tag, why and when)
## Budget                  (before / after words and minutes)
## Requests to the coordinator
## Terms
```json terms
{"term in lower case": "chNN", "...": "chNN"}
```
````

Every `<dt>` in your word list must contain each term you map to your chapter. Map multi-word terms of art, not everyday words.

## 10. Lessons from wave 1 (chapters 2–5, built 2026-10-02)

Chapters 1–5 are built and integrated: their glossary entries (`index.html#g-…`) exist, so the audit should give your page 0 problems, with no missing-anchor exceptions. Take earlier-chapter slugs from the hub glossary (`grep -o 'id="g-[^"]*"' index.html`), not from the plan in section 5.

- **netem on the sender's own egress hides the queue from TCP.** qnet puts `netem delay 20ms` as root on `s0`. netem orphans each skb at enqueue, so TSQ never sees it, fq never runs, and nothing paces (ch05 measured a 14.9 MB sender queue and an 8 s RTT). For anything on the sending host (TSQ, fq, pacing, departure times, `SO_TXTIME`), free `s0` and move its 20 ms onto the ack path, so the bottleneck on `r1` stays exactly qnet's (rate 10mbit, limit 50) and the RTT stays 40 ms:
  ```
  tc -n snd qdisc del dev s0 root
  tc -n snd qdisc add dev s0 root fq
  tc -n rcv qdisc del dev c0 root
  tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000
  ```
  Do **not** add the delay to the bottleneck netem (`netem delay 20ms rate 10mbit limit 50`): netem's `limit` counts the packets in its delay line too (`sch_netem.c:552`), so at 10 Mbit/s about 16 of the 50 slots hold packets that are only being delayed, and the real buffer is about 33 (found by the ch06 builder; ch05 lab 3 used that form).
- **`replace` on an existing netem keeps the parameters you did not name.** Delete and add instead. qnet's root on `r1` has handle `1:`, so `replace … root handle 1: tbf` fails; delete the root first.
- **`tc qdisc change … tbf` resets a pfifo child's limit** (`sch_tbf.c:443–444`). Re-set the child after any change.
- **netem with a child qdisc** keeps packets in its own tfifo, so it cannot host codel or fq as a child.
- **TCP paces by itself** when `SO_MAX_PACING_RATE` is set (or the congestion control asks for pacing) and no fq is present: its internal timer (`tcp_pacing_check()`, `tcp_output.c`) spaces packets, so pfifo and fq looked the same under a cap in ch05. Say which pacer runs in every pacing measurement.
- **Nested maths is now an audit problem.** Never put `\(` inside a `\( … \)`.
- **Budgets came in at 22–23 min.** Plan for about 4,400 words in the after half from the start; cutting 30% at the end costs more than writing to size.
- **Words already taken by built chapters** (do not redefine; link on first use): from ch02 utilisation, Little's law, Poisson arrivals, M/M/1, M/D/1, P-K formula, Kleinrock's power, operating point, Mathis formula, buffer-sizing rule, Jain's index; from ch03 bufferbloat, AQM, RED, standing queue, good/bad queue, sojourn time, target, interval, control law, CoDel, flow queueing; from ch04 token bucket, arrival curve, shaper, policer, work-conserving, HTB class, quantum, max-min fairness, GPS/WFQ, DRR; from ch05 TSQ, TSO autosizing, pacing, pacing rate, fq flow, new/old lists, throttled tree, BQL. Check the hub glossary for the exact wording.
- ch04 wrote "customers" instead of "tenants" (a pods-chapter term); keep "tenant" out until chapter 12. ch05 avoided bare "horizon" (chapter 7's term).
