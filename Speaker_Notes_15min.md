# Speaker Notes — Oral Project Report

**Real-Time Anomaly Detection in an IoT Setting**
DLBDSMTP01 · Task 1 (Stream processing) · Amash Mohamed

**Total target: 15:00.** The recording stops at 20:00, so you have a 5-minute safety
margin — but the rubric rewards *appropriate time management*, so aim for 15.
Slides 17 and 18 (list of figures, reference list) are not narrated; flip through them
on your way to slide 19.

**Slide order:** 1 title · 2 outline · 3–15 main aspects · 16 conclusion ·
17 list of figures · 18 reference list · 19 reproduce the code · 20 thank you.

---

## Before you record — checklist

- [ ] Replace `[DD Month YYYY]` on slide 1 with the recording date.
- [ ] Replace both `[ PASTE YOUR GITHUB REPOSITORY URL HERE ]` boxes (slides 19 and 20).
- [ ] Drop your four screenshots into the dashed placeholders (slides 10, 11, 12, 13),
      delete the placeholder text boxes, and **keep the Figure 3/4/5/7 captions** —
      the list of figures on slide 17 points at them.
- [ ] Delete the leftover `generate_date.py` from the project folder. The correct
      `generate_data.py` is now there; the deck and README both use that name.
- [ ] Export the finished deck to **PDF** — the guideline requires PDF format.
- [ ] Do one dry run with a timer. If you overrun, cut from slides 14 and 15 first.

---

## Slide 1 — Title · 0:00–0:30 (30 s)

Good morning. My name is Amash Mohamed and this is my oral project report for the
module *Project: From Model to Production*.

I chose Task 1 — anomaly detection in an IoT setting, with the spotlight on stream
processing.

The short version of what I built: a machine-learning model that scores factory sensor
readings for anomalies, wrapped in a REST API, fed by a continuous stream, and logged
so it can be monitored. The panel on the right is the idea in miniature — readings
flowing in, and the occasional one flagged.

> *Pause here for a beat before moving on. Don't rush the opening.*

---

## Slide 2 — Outline · 0:30–1:00 (30 s)

I'll take you through six sections: the problem and who it's for; how I planned and
worked through the project; the architecture I designed; the data and the model; the
model running as a live service — which I'll show you with screenshots from the running
system; and finally my reflection on what worked and what I'd change.

---

## Slide 3 — The problem · 1:00–2:00 (60 s)

The scenario: a factory producing machine components for wind turbines. It's already
well instrumented — sensors track every production cycle and managers can see the
numbers in a BI dashboard.

But — and this is the whole point of the project — a dashboard only *shows* values.
Nobody is watching it continuously, and nobody can eyeball three sensor channels for
every single item and spot the moment the pattern goes wrong.

In consultation with the shop-floor employees, who have years of domain knowledge, it
was established that three signals matter: temperature, humidity and sound volume.
That domain input is what defined my feature set — I didn't pick those three because
of anything in the data.

So the requirement is a decision-support system: score every item as it's produced, in
real time, and raise an alert when it looks abnormal.

*(Point at the stakeholder panel.)* Four groups have a stake in this. Worth noting the
third one — IT and operations. They have to run and maintain whatever I hand over.
That shaped a lot of my design decisions.

---

## Slide 4 — Goal and requirements · 2:00–3:00 (60 s)

My goal statement. Note the emphasis: build a *simple* model — the brief says so
explicitly — and then put it into production so it can be fed by a continuous stream
over a standardised API.

The task set four requirements, and I treated them as non-negotiable design
constraints rather than nice-to-haves.

**Monitorable** — I can see what the service is doing.
**Maintainable** — someone else can understand and change it.
**Scalable** — it can handle more load without a redesign.
**Adaptable** — the model can be replaced as the data changes.

I'll come back to each of these and show you concretely how the design satisfies it.

And the scope decision at the bottom, which I want to be transparent about: I
deliberately did not spend my time optimising model accuracy. The brief said don't,
and the marks in this module are for the production path. So the effort went into the
API, the stream and the monitoring.

---

## Slide 5 — Five phases · 3:00–4:00 (60 s)

How I actually worked. Five phases.

Phase one, design — I drew the architecture before writing a single line of code.
Phase two, generate the data. Phase three, train the model. Phase four, wrap it in the
API. Phase five, build the stream that feeds it.

Phase four is highlighted because the brief predicted it would be the most
work-intensive step, and it was — roughly two thirds of my time.

The important point is *why* I did design first. Because I'd fixed the interfaces up
front, each script ended up with exactly one job and a defined handover to the next
one. That meant I could build and test them independently — and, crucially, that
retraining the model later doesn't require touching the API at all. That's the
maintainability requirement being satisfied by the process, not by an afterthought.

---

## Slide 6 — Architecture · 4:00–5:30 (90 s)

This is the conceptual architecture. Take a moment with it — I'll walk left to right.

**Bottom left, offline training.** `generate_data.py` produces the sensor dataset;
`create_model.py` trains the detector and writes it to `model.pkl`. This happens once,
before anything is serving. It is completely separated from the live path.

**Centre, the model service.** `app.py` is a Flask REST API. When it starts up it loads
`model.pkl` once into memory. It then exposes two endpoints — `POST /predict` and
`GET /health`.

**Top left, data ingestion.** `stream_simulator.py` stands in for the factory sensors.
It generates a reading roughly every second and POSTs it to the API as JSON.

**Top right, decision support.** The API returns an anomaly score. If the score crosses
the threshold, the item is flagged and an alert is raised — that's the actual product
the factory managers asked for.

**Bottom right, monitoring.** Every single request, with its inputs, its score and its
verdict, is appended to `predictions.log`.

The sentence at the bottom is the whole design in one line: trained offline, frozen to
a file, loaded once by a stateless API, served over REST, consumed by a continuous
stream, with every prediction logged.

---

## Slide 7 — Three design decisions · 5:30–6:30 (60 s)

Three decisions in that diagram are worth calling out, because they're what separate a
notebook from a service.

**One — train offline, serve frozen.** The API never trains. It only loads. That means
a prediction costs milliseconds, and the expensive part is paid once at start-up rather
than on every request. My first version actually reloaded the pickle per request and
was noticeably slower — fixing that was a real lesson.

**Two — one pipeline object, not two artefacts.** The scaler and the detector are
bundled into a single scikit-learn `Pipeline` and pickled together. This matters more
than it sounds: it means training and serving apply *identical* preprocessing by
construction. Training-serving skew is the classic way these systems silently break,
and this removes the possibility entirely.

**Three — a stateless REST contract.** JSON in, JSON out, nothing remembered between
calls. That's what makes it replicable, restartable and replaceable.

---

## Slide 8 — Data · 6:30–7:30 (60 s)

On data, the task offered three routes. I used fictional sample data, which it
explicitly permits — and I want to justify that rather than have it look like the lazy
option.

Because I generate the data, I plant the anomalies myself, which means I have a known
ground truth. That lets me actually verify that the detector catches the faults I put
in. With a Kaggle set I'd be guessing.

The generator produces just over two thousand readings — roughly two percent of them
faulty, which is the rate the domain experts said to expect.

*(Point at the scatter plot.)* That's the dataset. Normal operation is the blue cloud
around 65 degrees and 70 decibels; the planted faults are the orange points sitting
clearly outside it. Hold that picture — it's exactly why my metrics on the next-but-one
slide look as good as they do.

The generator is seeded, so the dataset and the trained model are fully reproducible.

On storage: readings arrive as small JSON messages and go to an append-only,
timestamped log. That's deliberate — the same store serves two purposes, audit after an
alert, and the corpus for the next retraining.

For the stream itself I used option one: an application on my machine emitting one
reading per second, with about ten percent faults so the demo is lively.

And the honest caveat at the bottom, which I'll return to at the end: synthetic data
gives me reproducibility, but it cannot reproduce how messy real sensors are.

---

## Slide 9 — Why Isolation Forest · 7:30–8:30 (60 s)

Why this model, and why unsupervised?

The practical argument first. In a real factory, labelled faults are rare and expensive
— someone has to physically inspect items and record the verdict. A supervised
classifier would need those labels for every new fault type that emerges. That's a
maintenance burden the factory would have to carry forever.

Isolation Forest sidesteps this. It's unsupervised: it learns what normal looks like
and flags points that are easy to isolate from the rest. Note that I fit it on the
features alone — the ground-truth column exists in my data, but the model never sees
it. I only use it afterwards to score myself.

It also has one intuitive parameter — contamination — which I set to two percent, the
fault rate the shop floor expects. And it returns a continuous score rather than a bare
yes/no, which means the alert threshold can be re-tuned later without retraining
anything.

On the right is what actually gets pickled: scaler, then detector, then out comes a
score and a flag. One object, one file.

---

## Slide 10 — Evaluation · 8:30–9:30 (60 s)

The task asks for basic statistical measures, so here they are.

Precision 0.93 — of the items the model flagged, 93 percent really were faulty.
Recall 0.95 — it caught 38 of the 40 anomalies I planted. F1 0.94.

The confusion matrix underneath: three false alarms, two missed faults, out of 2,040
items.

*(Gesture at the screenshot.)* And this is that output coming straight out of
`create_model.py`, so you can see I'm not quoting numbers from memory.

Now — I'd rather be the person who contextualises their own metrics than the one who
gets asked about it. These numbers are good because my synthetic anomalies are cleanly
separated from normal operation — you saw that separation on the scatter plot two
slides ago. On real sensor data, where a developing fault looks almost normal for a
while, they would be considerably worse. What this result tells you is that the
pipeline works end to end, not that the model is excellent.

---

## Slide 11 — The API · 9:30–10:45 (75 s)

This was the heart of the project.

Two endpoints. `POST /predict` takes either a single reading or a JSON list for a
batch, and returns an anomaly score plus a boolean flag. `GET /health` returns a status
and a timestamp — that's what an uptime monitor or a load balancer polls to know the
service is alive.

The contract is at the bottom left: three numbers in, and back comes the echoed input,
a score to four decimals, and a verdict. That JSON schema is a promise. Once callers
depend on it, changing it breaks them — which is exactly why versioning matters, and
I'll come back to that.

*(Gesture at the screenshot.)* Here's the service actually running and answering. On the
left the API in one terminal; on the right a call to `/predict` with a clearly
anomalous reading, and you can see it comes back flagged with a high score.

One detail I'm quietly pleased with: the endpoint accepts a list as well as a single
object. That was five lines of code, and it means the same service can handle a
real-time stream and an overnight batch without a second implementation.

---

## Slide 12 — Stream in action · 10:45–12:00 (75 s)

This is the system doing its actual job.

One reading per second goes to the API. The response comes back, the score is compared
against the threshold, and a flagged item raises an alert immediately.

*(Gesture at the screenshot.)* You can see normal readings passing through with low
scores, and then the flagged lines — temperature in the eighties, sound over ninety —
coming back with an alert. That's the decision-support system the factory managers
asked for, working.

*(Point at the chart.)* And this is that entire run plotted — every one of the 281
readings, with its anomaly score. The scores oscillate in a normal band and spike
whenever a fault comes through; the orange points are the 39 that crossed the alert
threshold. This is also the drift signal I'll describe on the next slide: watch that
orange density over days rather than minutes and you can see the process changing.

One caveat I want to state myself: the stream simulator is not seeded, so this is one
recorded run, not a reproducible figure. The training metrics are reproducible; these
are illustrative.

39 flagged out of 281 is about fourteen percent, against the ten percent fault rate I
was injecting. The model is flagging slightly more than is strictly faulty. For a
warning system that's the safer direction to err in — a false alarm costs an
inspection, a missed fault ships a defective turbine component. But it isn't free, and
I'll come back to it, because the right answer is to choose that trade-off with the
shop floor rather than accept a library default.

---

## Slide 13 — Monitoring · 12:00–13:00 (60 s)

The task asks specifically what monitoring components a predictive model needs to run
reliably. Three, in my design.

**Liveness.** The `/health` endpoint. Trivial to build, and it's the difference between
knowing the service died and finding out when someone complains.

**Traceability.** Every request is appended to `predictions.log` — the inputs, the
score, the verdict, timestamped. *(Gesture at the screenshot.)* This matters for a very
practical reason: when the shop floor asks "why was item 4,412 flagged?", there's an
answer. A prediction you can't explain after the fact is a prediction people stop
trusting.

**Drift watch.** This is the one that actually protects the model. The share of items
flagged over time is an early-warning signal. If that rate suddenly jumps, either the
sensors have changed or the process has — and the model is now scoring against a world
that no longer exists. It needs retraining. You don't need anything sophisticated to
detect that; you need the log and something watching the ratio.

---

## Slide 14 — Challenges and constraints · 13:00–13:40 (40 s)

The module description asks what was hard about integrating a model into a service, and
what constraints that imposes. Left column, what was hard.

Keeping preprocessing consistent — solved with the single pipeline. Loading the model
once instead of per request — I got that wrong first and fixed it. And turning a raw
score into a decision, which is a design question, not a modelling one.

The third bullet is one I want to own rather than hide. Input validation is a gap I did
not close: send a request with a missing field and the handler raises, so the caller
gets a bare 500 instead of a clean 400 telling them what was wrong. It's a five-line
fix and I know exactly where it goes — I ran out of time before I ran out of
understanding.

Right column, the constraints those impose. Stateless. Fixed contract. Fast enough to
keep up. Versioned, so a new model can go in without downtime.

The line at the bottom is my honest summary: the model was the easy part. Everything
difficult lived at the boundary between the model and the system around it.

---

## Slide 15 — Critical reflection · 13:40–14:20 (40 s)

Four things I'd do differently.

**Data.** As I said — synthetic data flatters the model. 0.94 F1 means the plumbing
works, not that the model is excellent.

**Threshold.** Currently the library default. It should be chosen with the shop floor,
explicitly trading false alarms against missed faults. An alarm people learn to ignore
is worse than no alarm at all.

**Storage.** A log file demonstrates monitorability but doesn't scale. The next step is
a message queue in front of the API and a time-series database behind it.

**Automation.** Retraining is manual — the glue code and manual steps Sculley and
colleagues identify as hidden technical debt. Wire the drift signal to a scheduled
retrain and the loop closes. And containerising the API for a cloud host is the
extension I'd take next; I chose depth on the local system over breadth into the cloud.

---

## Slide 16 — Conclusion · 14:20–14:40 (20 s)

Against the five requirements: continuous stream — yes. Standardised API — yes.
Monitorable, maintainable and adaptable, scalable — yes, by design rather than by
accident.

The part the brief called most work-intensive, putting the model into production, is
the part that's fully delivered. The model itself is deliberately simple, exactly as
asked.

---

## Slides 17–18 — List of figures, reference list · 14:40–14:45 (5 s)

*(Don't narrate. Advance through both while saying the first line of slide 19.)*

---

## Slide 19 — Reproduce the code · 14:45–15:00 (15 s)

Everything is in this repository — five commands from a clean checkout, and because the
data generator is seeded you'll get the identical dataset, model and metrics I showed
you.

*(Leave this slide up for a beat so the URL is readable, then advance.)*

Thank you for your attention. I'm happy to take questions.

---

## Delivery reminders

- **Pause between sections.** Silence reads as confidence; filler words read as nerves.
- **Vary your pace.** Slow down on slide 6 (architecture) and slide 10 (results) —
  those are the two the examiner is assessing hardest.
- **Point deliberately** at the screenshots when you reach them. The rubric explicitly
  credits demonstrating the product.
- **Don't read the slides.** The bullets are your cues; these notes are the sentences.
- **If you're running long at slide 13,** compress slides 14 and 15 to their bold
  headings only. Never cut the conclusion.

## Likely questions

**Why not a supervised model?** Labels are rare and expensive in this setting, and each
new fault type would need new labels. Unsupervised generalises to faults nobody has
seen yet.

**Why Flask and not mlflow?** Flask gives full control over the request contract with
minimal machinery, which suited a service this small. mlflow would be the better choice
once model versioning and a registry become requirements — which is exactly the
adaptability step I described.

**How would this scale to thousands of sensors?** The API is stateless, so horizontally:
containerise it and run replicas behind a load balancer. The bottleneck moves to
ingestion, which is where a message queue like Kafka comes in.

**Why is the live flag rate 14% when you inject 10%?** The contamination parameter was
set from the training distribution, and the stream is deliberately more anomalous than
the training data. The model is therefore slightly over-flagging — cautious rather than
wrong, and correctable by tuning the threshold.

**Isn't the ground-truth column leakage?** No — it is never passed to `fit()`. Isolation
Forest is fitted on the three features only. The labels are used purely for the
evaluation on slide 10.

**What happens if I send a malformed request?** Right now you get a 500 rather than a
400 — I flagged that on slide 14. The fix is a validation guard at the top of
`/predict` that checks the three keys are present and numeric and returns a 400 with a
message naming the missing field.

**Why is there no data store in your architecture diagram?** The append-only prediction
log *is* the store in this implementation, and it's shown as the monitoring node. In a
production version it would be an explicit time-series database, which is the storage
point on my reflection slide.
