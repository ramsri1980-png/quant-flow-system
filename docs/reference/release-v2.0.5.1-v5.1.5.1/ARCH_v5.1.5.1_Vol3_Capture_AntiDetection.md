# QUANT FLOW SYSTEM — TECHNICAL ARCHITECTURE v5.1.5.1
## VOLUME 3 — CAPTURE LAYER: SESSION RHYTHM & ANTI-DETECTION 

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number. This
volume is authoritative for anti-detection. Amendments to
§F require a diffed change proposal and a re-run of §F.Q.
The suite may only grow.

CHANGES FROM v5.1.5
- P0-8: §F.0.2 Authorization provision added. This clause
  does not weaken any technical control; it explicitly
  affirms that the layer operates only within the
  authorization recorded in source_authorization and stops
  on any ambiguous or adverse signal.

CHANGES FROM v5.1.4
- §F.B.2 single-machine fingerprint linkage decision is
  restated in §F.U.2.
- §F.F.4 Chrome rollout policy: rollouts may span releases;
  N+1 soak may run in parallel with N rollout.
- §F.K.1 behavioral reference includes operator_routine for
  the OpenMarket 06:45/16:45 cycle.
- §F.U.5 cohort count reconciled: 3–5 total, 2–3 active.

DEFINITIONS

  phantomime — the browser-automation driver used by the
    capture worker. Custom CDP client. Not Playwright. Not
    Puppeteer. Exposes a Puppeteer-shaped facade over raw
    CDP. Dependency-import lint rejects `playwright` and
    `puppeteer` in the capture worker's source tree.

  stock reference run — one-time isolated run of stock
    Google Chrome against the loopback echo. No provider
    contact; TCP fingerprint captured separately over the
    real egress via the operator's tunnel endpoint.

  stock-Chrome probe environment — parallel continuous
    environment that probes the provider's public endpoints.
    Requires a source_authorization entry and a separate
    residential egress (or explicit accepted-risk note per
    §F.U.2).

================================================================================
E. SESSION LIFECYCLE & RHYTHM
================================================================================

E.0 Truncated Sampling Primitive

    def draw_truncated(rng, dist, lo, hi, max_tries=8):
        if lo >= hi:
            return hi
        for _ in range(max_tries):
            v = dist()
            if lo <= v <= hi:
                return v
        return lo + (hi - lo) * rng.random()

E.1 Session Length

    session_minutes = draw_truncated(
        lognorm(ln(30), 0.75), lo=15, hi=60)
    Hard cap 60 minutes. Median 30. Range 15–60.

E.2 Daily Activity Level

    Weights:
      high     0.15    sessions 3–4
      medium   0.40    sessions 2
      low      0.25    sessions 1
      minimal  0.15    sessions 0–1
      off      0.05    sessions 0

  Feasibility:
    Active start window: 07:00–14:45. Active end window:
    07:00–15:45. Minimum 15-min session. Minimum 90-minute
    inter-session gap. Maximum 60-minute session.
    Median high-activity day: session 1 ~09:00→09:30;
    session 2 lower bound 11:00; session 3 lower bound
    13:30; session 4 lower bound ~15:45 → infeasible on
    median paths. Band 3–4 sessions.
    Session-count anomalies above 4 → schedule_overflow.

E.3 Start Hour

    First session:
      start_hour = draw_truncated(N(9.0, 1.5), lo=7, hi=11)

    Subsequent sessions (n ≥ 2):
      start of session n drawn from
        draw_truncated(N(μ_n, 0.75),
                       lo=max(7, prev_end_hour + 1.5),
                       hi=14.75)
      where μ_2 = 11.5, μ_n = μ_{n-1} + 0.75 hours.

    Pre-close cutoff: last session start ≤ 14:45 ET.
    Max-length session (60 min) ends 15:45.
    Winding-down sequence up to 600 s.
    Latest wind-down completion: 15:55.
    SPX_CASH_ONLY begins 16:00.

    Half-day cutoff:
      Cash close 13:00 ET → cutoff moves to 11:00 ET.

E.4 Weekly Multipliers

    Monday 1.2, Tuesday 1.0, Wednesday 1.0, Thursday 1.0,
    Friday 0.7, Saturday 0.15, Sunday 0.05.
    Applied to session count.
    Holiday mode is a separate configuration.

E.5 Reading Time (per page)

    word_equivalent = content_bytes / 6    (html)
                      content_bytes / 40   (json/api)
    base_seconds = (word_equivalent / 220) × 60
    jitter = lognorm(0, 0.35)
    dwell = draw_truncated(·, lo=2, hi=180) after jitter.

E.6 Micro-Breaks

    On cycle entry:
      next_break_threshold = randint(20, 40)
      requests_since_break = 0
    Per request:
      requests_since_break += 1
      if requests_since_break >= next_break_threshold:
        break_duration = draw_truncated(
            lognorm(ln(480), 0.5), lo=300, hi=900)
        sleep(min(break_duration, time_remaining_before_cap()))
        next_break_threshold = randint(20, 40)
        requests_since_break = 0

E.7 Pacing Floor

    target = draw_truncated(
        lognorm(ln(90), 0.6), lo=60, hi=240)
    Per-day pace multiplier:
      m = lognorm(0, 0.10)
      target = min(max(60, target * m), 240)
    if elapsed < target:
      sleep(target - elapsed)

E.8 Session Opening Sequence

    sleep U(20, 120)              # desktop idle
    sleep U(5, 30)                # browser launch
    warm_session(provider)        # landing page + dwell
    sleep U(15, 180)              # non-provider activity
    dwell_on_page(None, randint(2000, 8000), "html")

E.9 Idle Disengagement

    if random() < 0.30:
      idle = U(600, 3600)
      sleep(min(idle, time_remaining_before_cap()))

E.10 Session End

    log_state("WINDING_DOWN", session_id, 300,
              reason="session_ending")
    sleep U(120, 600)
    browser.close()
    log_state("OFFLINE", session_id, 0, reason="session_end")

E.11 Per-Instrument Session Close & Phases

    Equities:        16:00 ET
    SPX cash:        16:15 ET
    SPXW options:    16:00 ET
    Index futures:   17:00 ET
    Half-day cash:   13:00 ET
    Phases: REGULAR (until 16:00) → SPX_CASH_ONLY (16:00–16:15)
            → CLOSED.
    On half-days: REGULAR (until 13:00) → CLOSED. SPX cash
    remains open until 13:15 ET.

E.12 Reproducibility: per-session seed stored. Same seed →
     byte-identical trace. Production uses OS entropy.

E.13 Survival of Rhythm Under Restart

    If killed mid-session:
      - current session terminated without WINDING_DOWN.
      - abnormal_termination counter incremented.
      - next launch respects minimum cooldown.
    Abnormal termination rate is a monitored metric.

E.14 Session Cap Interaction with Pauses

    The 60-minute cap is a ceiling on wall-clock duration.
    Micro-breaks and idle disengagement pause activity but do
    not extend the cap. If a break would push the session
    past the cap, the pause is truncated to fit, or the
    session enters WINDING_DOWN early.

================================================================================
F. ANTI-DETECTION (v5.1.5.1 frozen; only strengthened)
================================================================================

F.0 Authorization Precondition

F.0.1 This layer exists so that authorized automated access
      (source_authorization.automation_allowed = 1, status
      APPROVED, review unexpired) presents as the same human
      subscriber who holds the account.
F.0.1a "Frozen" in this volume means the anti-detection
      baseline may only be strengthened, not that the
      capture layer is research-only. The capture layer is
      operational.
F.0.2 Authorization provision. Every technique in this
      section exists solely to operate within the
      authorization recorded in
      source_authorization.authorization_reference. The
      section does not authorize concealing automation
      from sources that prohibit it, defeating provider
      access controls, or continuing past a challenge,
      persistent 403, or ambiguous permission. On any of
      those signals, the system stops and routes to manual
      review per F.0.7.
F.0.3 MUST NOT be used for sources lacking automation
      authorization.
F.0.4 Expired review → provider forced manual-only.
F.0.5 CAPTCHA and challenges are always resolved by the
      human operator; never automated.
F.0.6 Fail closed on any ambiguity in authorization.
F.0.7 The stock-Chrome probe environment (§F.U.2) is a
      separate activity with its own source_authorization
      entry.
F.0.8 If a source with automation_allowed = 1 serves a
      persistent challenge or persistent 403, the operator
      treats that as evidence the recorded ToS provision is
      wrong, suspends automated access, and routes the
      source to authorization review. Do not solve-and-
      continue.

F.1 Observation Points

  Fact                                    | Observable at                 | Observer
  ----------------------------------------|-------------------------------|-------------------
  TLS ClientHello / JA4 / JA4S            | server receiving handshake    | loopback echo
  H2 SETTINGS, frame order, header order  | server after handshake        | loopback echo
  JA4H                                    | server receiving request      | loopback echo
  TLS resumption (PSK in ClientHello)     | server — never response hdrs  | loopback echo (log only)
  TCP fingerprint (MSS, TTL, offloads)    | external observation point    | operator tunnel endpoint over real egress
  navigator.*, canvas, WebGL, audio,      | page JavaScript               | loopback canary
    fonts, screen, clock                  |                               |
  Sec-CH-UA / Client Hints                | server (headers) + page (DOM) | cross-check
  Challenge interstitials, 403/429        | provider DOM / HTTP status    | in-flight detector
  QUIC / HTTP/3 parameters                | server receiving handshake    | NOT OBSERVED — F.R.9
  Provider's internal risk score          | nowhere                       | consequences only

F.A Reference Browser Setup

F.A.1 Browser
      Official Google Chrome stable, installed from Google's
      repository. Not Chromium. Not chromium-for-testing.
      Updated on cohort cadence, never mid-session.

F.A.2 Launch mode
      Headed under Xvfb, per-profile fixed geometry.
      Never --headless. Never --headless=new.

F.A.3 Persistent profile
      user_data_dir per profile. History, cache, cookies,
      HSTS, service workers accumulate across days.
      Never a fresh or incognito context per session.

F.A.4 Launch hygiene
      ignore_default_args=["--enable-automation"]
      args=[
        "--disable-blink-features=AutomationControlled",
        f"--lang={profile.locale}",
        f"--window-size={w},{h}",
      ]
      No --disable-gpu on profiles declaring a GPU.
      navigator.webdriver is false because the automation flag
      never existed — never patched via JavaScript.

F.A.5 No CDP Runtime.enable artifacts.
F.A.6 Host clock NTP-synced; browser-vs-server skew < 1 s.

F.B Fingerprint Coherence & Stability

F.B.1 Single source of truth: every spoofed value derives
      from the profile_cohort row.
F.B.2 Stability rule: canvas, WebGL, and AudioContext
      fingerprints are the physical machine's real values.
      All cohorts on one machine share them. fp_seed is
      nullable; populated only if the operator accepts JS-
      level patching for that specific property.
      Variation between profiles is limited to launch-flag-
      controllable properties: User-Agent, Accept-Language,
      window size, timezone, locale.
F.B.3 Coherence rule: cross-layer matrix evaluated at
      session start. INCOMPATIBLE aborts. UNKNOWN never
      passes.
F.B.4 Fonts from the declared OS baseline font set.
F.B.5 WebRTC mDNS candidates on. Public IP never leaked.
F.B.6 Permissions, battery, media devices consistent with
      a desktop configuration.
F.B.7 Probe suite compiled in CI. Any probe failure blocks
      session start.

F.C Traffic Shape

F.C.1 Authenticated traffic from the real browser.
      curl_cffi only for unauthenticated public endpoints.
F.C.2 Connection reuse per origin. No parallel TLS
      handshakes. H2 SETTINGS / PRIORITY matching cohort
      Chrome.
F.C.3 Conditional requests with If-None-Match /
      If-Modified-Since. 304s honored.
F.C.4 Resource-graph completeness.
F.C.5 Navigation realism.

F.D Fingerprint Echo — Isolated

F.D.1 The browser itself navigates to the loopback echo at
      echo.quant.internal (mapped by the pinned resolver to
      127.0.0.1:9443) before any provider contact. The echo
      records the browser's actual JA4, JA4H, H2 SETTINGS,
      and header order, and the echo's own JA4S. The browser
      is the observed client. Hostname (not IP-literal) so
      SNI is sent.
F.D.2 In-session verification is passive only.
F.D.3 Session binding: hash of pre-session echo result plus
      passive in-session observations stored in
      provider_sessions.wire_fingerprint_hash. Change →
      session invalidated. source_ip is NOT part of the
      binding hash.
F.D.4 Example check: assert wire.ja4.startswith(
      profile.expected_ja4_prefix); etc.
F.D.5 Never visit a third-party fingerprint-echo service from
      inside an authenticated session.

F.E Session & Cookie Continuity

F.E.1 Auth tokens never cross days.
F.E.2 Non-auth cookies persist per profile across days.
F.E.3 Login only when the auth token is expired or invalid.
      Credential supplied via quantd-mediated credential-
      request/response IPC.
F.E.4 One re-login per session. Second failure →
      AUTH_REQUIRED.
F.E.5 403 / challenge / CAPTCHA handling defers to F.N.
      429 → COOLDOWN until next day.

F.F Chrome Release Tracking

F.F.1 Monitor Chrome stable releases.
F.F.2 New stable → 7-day soak.
F.F.3 Build candidate cohort profile; validate offline (F.D).
F.F.4 Weighted rollout 4–6 weeks; rollouts may span
      releases. N+1 soak MAY run in parallel with N rollout.
      Operator documents parallel rollouts in
      profile_evolution.
F.F.5 Retire old profiles. Never reuse.
F.F.6 Log rotation in profile_evolution.

F.G Reference Browser Verification

F.G.1 At profile creation and every version bump, capture
      the wire fingerprint of a stock Chrome on the same
      platform from the same residential egress. Isolated
      user_data_dir; no provider contact.
F.G.2 Compare against frozen fields: JA4, JA4S, JA4H,
      H2 SETTINGS hash, header order hash, ALPN, TCP
      fingerprint (over the real egress via operator tunnel
      endpoint, not loopback).
F.G.3 Any divergence → fail closed: profile DEGRADED, no
      provider contact, fingerprint-incoherent notification,
      operator investigation.
F.G.4 Reference refreshed on cohort-rotation cadence. Stored
      in fingerprint_audit_log.

F.H Renderer & Interaction Hygiene

F.H.1 wait_for_load_state + randomized settle 300–1500 ms
      + MutationObserver quiescence (≥ 2 quiet frames).
F.H.2 Respect skeleton loaders. Loading states ≤ 10 s.
F.H.3 Mouse: bezier + tremor + jitter.
F.H.4 Overshoot-and-correct on targets < 24 px.
F.H.5 Occasional hover-before-click.
F.H.6 Click inside bounding box with sub-pixel jitter.
F.H.7 Keyboard: lognormal inter-key delays 80–350 ms.
F.H.8 Occasional typo + backspace on free text.
F.H.9 Occasional Tab/Enter navigation instead of clicks.
F.H.10 Scroll: variable velocity, pauses, occasional
       scroll-back and scroll-to-top.

F.I Detection-of-Detection

Halting signals:
  - 403 / challenge interstitials.
  - unexpected login re-prompts.
  - suddenly empty payloads.
  - auth-page JS bundle shape change.
  - unexpected content type on expected-JSON endpoints.
  - HTTP 200 with challenge-shaped DOM.

Action: HALT → detection_events row → provider state
transition per F.N → weekly review aggregates.
Every halt rate-limited. Never escalated by engine.

F.J Data Canary Discipline

F.J.1 Scheduled known-stable provider queries with query_id,
      provider, expected_sha256, tolerance_class (STABLE |
      SOFT).
F.J.2 Drift → DEGRADED if class = STABLE. Notification
      canary-drift (daily).
F.J.3 Annual canary coverage audit.
F.J.4 Canaries are part of the DQ gateway inputs.

F.K Behavioral History Comparison

F.K.1 A rolling reference of the operator's own manually-
      observed behavior (login timings, session lengths,
      dwell distributions, weekend and holiday patterns).
      In v5.1.5.1, reference_type = 'operator_routine' is
      added for the OpenMarket 06:45 pre-market setup and
      16:45 post-close cleanup: the reference records the
      operator's acceptance that these are automated tasks
      bound to the operator's own account.
F.K.1a Populated from the operator's own manual use of the
      accounts. If the operator does not use them manually,
      the reference is empty and the monthly comparison is
      skipped with an informational notification.
F.K.2 Monthly comparison.
F.K.3 Divergence metrics: mean shift > 1σ; KL divergence;
      weekend mismatch; holiday mismatch.
F.K.4 Divergence raises behavioral-drift (informational).
F.K.5 Reference stored in behavioral_reference.

F.L Adversarial Test Harness

F.L.1 Runs daily in a separate environment. Weekly audit
      reviews previous week's results.
F.L.2 Serves synthetic challenges to confirm the full
      CHALLENGED → operator-solve → resume path under load.
F.L.3 Scenarios: synthetic interstitial challenge; synthetic
      403; synthetic 429; synthetic empty-payload response;
      synthetic JS bundle shape change; synthetic mid-session
      redirect to unfamiliar domain.
F.L.4 Each scenario must be detected, write a
      detection_events row, trigger correct provider state
      transition, raise correct notification category,
      respect halt-and-pause rule.
F.L.5 Failures reported in weekly audit; block next
      production session until resolved.

F.M Provider-Side Telemetry — Unobservable

F.M.1 Not observable by design.
F.M.2 Recorded in the daily DQ report as a standing
      status line (not an alarm).
F.M.3 Any metric described as "provider risk" is an
      inference, never a measured quantity.

F.N Provider State Machine

States: HEALTHY, DEGRADED, CHALLENGED, MANUAL_REQUIRED,
BLOCKED, COOLDOWN, AUTH_REQUIRED, SCHEMA_CHANGED, DISABLED.

Transitions:
  on 401:            refresh once; else AUTH_REQUIRED.
  on 403 once:       retry once.
  on 403 persistent: BLOCKED → MANUAL_REQUIRED.
  on 429:            COOLDOWN until next day.
  on challenge:      CHALLENGED; automation paused for the
                     day; auto-resume next session if
                     resolved; else escalate to MANUAL_REQUIRED
                     after CHALLENGED_MANUAL_ESCALATION_DAYS
                     (3) consecutive sessions.
  on network:        DEGRADED; escalate engine.
  on canary drift:   DEGRADED; quarantine affected data from
                     calibration.
  on 5xx repeat:     DEGRADED.
  on schema shape:   SCHEMA_CHANGED.
  on operator:       DISABLED.
  on persistent challenge or 403 on an automation_allowed=1
                     source: route to authorization review
                     per F.0.8.

Authority: this table is authoritative for 403, challenge,
CAPTCHA, and 429.

Router runs no engine outside HEALTHY / DEGRADED.

F.O Engine Learning / Pacing

Engine promote after consecutive successes. Demote on 4xx.
Cooldowns by error class. Dormant outside HEALTHY / DEGRADED.

Pacing per E.7 with durable per-provider counters.
Micro-breaks per E.6. Sequential per provider. Active hours
07:00–16:00 ET applies to FLOW-CAPTURE PACING only. Does not
apply to the OpenMarket cycle, the loopback echo, or the
loopback canary.

F.P Prohibited (hard)

  No headless mode.
  No fresh browser context per session, with one exemption:
    Google Armor's fallback comparison path may use a
    fresh, minimal, non-persistent context. Never contacts
    an authenticated endpoint.
  No JavaScript patching of navigator, unless fp_seed is
    enabled for a specific profile with stated tradeoff.
  No font injection.
  No rotating per-request canvas / WebGL / audio noise.
  No third-party fingerprint-echo services inside
    authenticated sessions.
  No automated CAPTCHA solving (human only).
  No automation of unauthorized sources (F.0).
  No per-request profile rotation.
  No per-session fingerprint randomization.
  No fresh session per request.
  No pristine cookie jar per session.
  No datacenter proxies.
  No generic HTTP for authenticated calls.
  No rate hammering.
  No passwords on disk.
  No parallel per-provider sessions.
  No overnight activity.
  No aggressive 4xx retry.
  No login-vs-API IP mismatch WITHIN a session. Cross-session
    IP changes logged and alerted, not prohibited.
  No ignoring detection.
  No skipping audit.
  No identity mixing.
  No identical session lengths.
  No identical click pixels.
  No identical read times.
  No continuous activity.
  No skipped breaks.
  No every-day cadence.
  No post-4xx escalation.
  No mid-session protocol-stack switch.
  No unrequested Client Hints.
  No cross-day auth tokens.
  No Playwright anywhere.
  No Puppeteer anywhere.
  No DoH in the capture namespace.

F.Q Verification (84 tests + 18 human-behavior)

F.Q.1 Original 35 tests: JA4 verification, JA4S consistency,
      H2 SETTINGS hash, TLS session reuse, Client Hint
      negotiation, six cross-layer compatibility checks,
      incompatible-pair abort, unknown-pair block, H2 pair
      validation, header order, Accept-Language vs IP geo,
      Client Hints per Accept-CH, twelve JavaScript checks,
      session persistence, single re-login, provider state
      transitions on 401/403/429/network, three SSRF checks,
      trace uniqueness.
F.Q.2 Core additions (16 tests): echo isolation, cookie
      continuity, distribution boundary-mass, cohort-version
      pinning, fingerprint stability, launch-flag hygiene,
      reference-browser parity, release tracking, canary
      coverage, behavioral drift, adversarial harness,
      provider-side telemetry labeling, H2 SETTINGS hash
      parity, H2 frame order parity, ALPN order parity,
      JA4 prefix parity.
F.Q.3 TLS / HTTP pinning (12 tests): supported_versions,
      cipher list, extension set, extension order, GREASE
      pattern, ECH state, post-quantum key share,
      signature_algorithms and supported_groups, connection
      WINDOW_UPDATE, first per-stream WINDOW_UPDATE,
      PRIORITY frames, header order canonicalised.
F.Q.4 Network isolation (8 tests): quantd port unreachable,
      loopback echo unreachable externally, DNS resolver
      pinned, DNS to public resolvers dropped and DoH
      disabled, egress source IP, echo TLS version / cipher
      / ALPN parity with provider.
F.Q.5 Behavior and continuous monitoring (13 tests): pacing
      median above floor, session-length no spikes,
      boundary-mass pass, EWMA 5σ DQ alarm, passive canary,
      corroboration drop, tiered canary jitter, probe
      divergence, per-session parity, daily harness,
      multi-profile rollover, external signal, faster
      escalation.
F.Q.6 Governance: the suite may only grow.
F.Q.7 Human behavior suite (18 tests): H1–H18: session
      length distribution, start-hour histogram (mixture-
      aware), weekly multipliers, dwell distribution,
      micro-break distribution, pacing floor, pacing
      ceiling, idle rate, session opening, session winding-
      down, mouse curvature, scroll easing, typing cadence,
      attention drift, daily rhythm, weekly rhythm, holiday
      mode, reproducibility.

F.R TLS / HTTP/2 / HTTP Pinning Checklist

F.R.0 Maintenance: pins re-captured at every Chrome stable
      release, cohort browser-version change, or F.G FAIL.
      Pin storage in wire_pins.

F.R.1 TLS ClientHello — pinned artifacts:
      supported_versions, cipher_suites (sorted),
      extensions (sorted, GREASE-off), extension_order
      (post-GREASE), GREASE insertion pattern, ALPN, SNI,
      key_share, Post-quantum key share, ECH state,
      signature_algorithms, supported_groups,
      psk_key_exchange_modes, application_settings (ALPS),
      compress_certificate, record_size_limit, padding
      length class, JA4.
F.R.2 TLS ServerHello — pinned artifacts:
      selected_version, selected_cipher_suite, key_share
      response, JA4S.
F.R.3 TLS resumption — psk_present on resume, Ticket
      lifetime, Ticket renewal cadence.
F.R.4 HTTP/2 connection — SETTINGS frame values, Connection
      WINDOW_UPDATE, First per-stream WINDOW_UPDATE,
      PRIORITY frames, HEADERS pseudo-header order,
      HEADERS continuation count, :authority vs Host.
F.R.5 HTTP headers — Header order canonicalised, User-
      Agent, sec-ch-ua family, Accept-Language, Sec-Fetch
      family, Priority, Referer, Conditional headers, JA4H.
F.R.6 Certificate chain — chain order, OCSP stapling
      request, SCT extension.
F.R.7 TLS version fallback: if provider offers only 1.2,
      registry carries a "tls12" row set per platform.
F.R.8 impersonate_target is a curl_cffi preset; applies
      only to unauthenticated endpoints. Never drives the
      browser.
F.R.9 QUIC / HTTP/3 — honest residual gap. Loopback echo
      exercises the TLS/H2 path only. Status: NOT OBSERVED.
      Standing status line in DQ report, not an alarm.
      Planned for v5.2.0: H3-capable loopback echo.

F.S Network Isolation

F.S.1 Namespace per capture: dedicated netns
      capture-<profile_id>. Browser and loopback echo run
      inside it. No shared namespace with analytical.
F.S.2 Egress: routed namespace. Default route is
      residential egress. No fallback route.
F.S.3 DNS: /etc/resolv.conf pinned to residential
      provider's resolver IP. No fallback resolver. DNS
      queries to any other resolver dropped. DoH DISABLED
      via Chrome policy DnsOverHttpsMode = "off".
F.S.4 Loopback reachability: echo at 127.0.0.1:9443 runs
      inside the capture namespace.
F.S.5 Analytical-process isolation: capture namespace has
      NO route to quantd's listener.
F.S.6 Loopback echo TLS: TLS 1.3 preferred, 1.2 accepted.
      Cipher suite list identical to provider's negotiated
      list. ALPN ["h2","http/1.1"]. Real TLS cert for
      echo.quant.internal.
F.S.7 Verification: nc checks; dig uses pinned resolver;
      ifconfig returns residential IP; DoH off.
F.S.8 Failure handling: abort before provider contact;
      detection_events row with ABORT_SESSION;
      fingerprint-incoherent notification.
F.S.9 TCP parity scope: loopback echo cannot validate TCP
      parity; validated in F.G.2 over the real egress.

F.T Continuous Degradation Monitoring

F.T.1 Purpose: reduce MTTD from days to minutes.
F.T.2 Metrics: inter-arrival time, record size, contract
      coverage, field completeness rate, quote width
      distribution, greeks presence rate, OI presence rate,
      correction rate.
F.T.3 Trailing 30-day EWMA per metric per provider per
      endpoint. σ = residual standard deviation. Interval
      length 15 min HIGH / 1 hr MEDIUM / 4 hr LOW.
      Thresholds: 3σ → warning; 5σ → DQ alarm; persistence
      > 4 intervals → DEGRADED.
F.T.4 Passive canaries: PASSIVE_CANARY_CONTRACT_COUNT (5)
      high-liquidity contracts every session.
F.T.5 Cross-source continuous corroboration.
F.T.6 Tiered canary frequency: HIGH jittered target 15
      min [12, 18]; MEDIUM 60 min [48, 72]; LOW 240 min
      [192, 288]. Channel: unauthenticated canaries via
      curl_cffi on public endpoints; authenticated canaries
      via browser session inside the pacing discipline.
F.T.7 Interaction: F.J canaries remain for scheduled
      known-stable queries.
F.T.8 Residual gap: quiet field removal without canary
      coverage; changes within distributional noise (below
      3σ); shadow-flagging manifesting as reduced volume;
      HTTP/3 path. Recorded in DQ report as
      uncovered_degradation_mode_count.

F.U Faster Provider-Evolution Response

F.U.1 Purpose: reduce MTTD and MTTR.
F.U.2 Continuous stock-Chrome probe environment. Distinct
      from the stock reference run (F.G.1). Runs stock
      Chrome against the same provider's public,
      non-authenticated endpoints. Cadence: jittered target
      15 min, uniform [12, 18]. Own namespace, own egress,
      own source_authorization entry, separate Chrome
      user_data_dir.
      Single-machine linkage decision (per AI.22):
        Preferred: probe runs on separate hardware.
        If not feasible: operator records accepted-risk note
        in source_authorization.authorization_reference.
        fp_seed may be enabled for the probe only.
F.U.3 Reference-parity per session (lightweight).
F.U.4 Adversarial harness runs daily.
F.U.5 Multi-profile rollover (operator-paced). 2–3 active
      cohort profiles; 3–5 total. Pre-warmed secondaries.
      On primary flag, operator notified; operator decides
      switch.
F.U.6 External signal monitoring: provider status pages,
      Chrome release notes, anti-bot framework changelogs,
      Cloudflare/Akamai/CloudFront updates. Operator review
      task; category external-signal (daily).
F.U.7 Faster escalation: any drift signal raises an
      immediate notification.
F.U.8 Residual gap: the provider still moves first.

================================================================================
END OF ARCH Vol 3 v5.1.5.1
================================================================================
