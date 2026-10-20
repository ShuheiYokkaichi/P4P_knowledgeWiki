# References and appendices

## References

Ansys. (2025a). *Ansys Fluent Theory Guide*, Release 2025 R1, §23.3.1, Spatial discretization. [Source](https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/flu_th/flu_th_SolveDiscretization_spatial.html).

Ansys. (2025b). *Ansys Fluent Theory Guide*, Release 2025 R2, §17.2.1.5, Secondary phase accretion. [Source](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_th/flu_th_ewf_sec_film_submodels.html).

Arifien, B. N., & Zarrouk, S. J. (2015, November 18–20). Moisture removal systems in geothermal power systems. In *Proceedings of the 37th New Zealand Geothermal Workshop*, Taupo, New Zealand.

Bangma, P. (1961, April 11). *The development and performance of a steam-water separator for use on geothermal bores* [Summary, E/CONF.35/G/13/Summary]. United Nations Conference on New Sources of Energy, Rome. United Nations. [UN record](https://digitallibrary.un.org/record/3833604?ln=en).

Foong, K. C. (2005, April 24–29). Design concept for a more efficient steam-water separator. In *Proceedings of the World Geothermal Congress 2005* (Paper 1338, pp. 1–7), Antalya, Turkey. [Conference record](https://pangea.stanford.edu/ERE/db/IGAstandard/record_detail.php?id=1066).

Gimbun, J., Chuah, T. G., Fakhru’l-Razi, A., & Choong, T. S. Y. (2005). The influence of temperature and inlet velocity on cyclone pressure drop: A CFD study. *Chemical Engineering and Processing: Process Intensification, 44*(1), 7–12. [DOI](https://doi.org/10.1016/j.cep.2004.03.005).

Lazalde-Crabtree, H. (1984, September). Design approach of steam-water separators and steam dryers for geothermal applications. *Geothermal Resources Council Bulletin*, 11–20. [Publisher PDF](https://publications.mygeoenergynow.org/grc/7000229.pdf).

McKibbin, R. (1998). Fluid flow in a flashing cyclone separator. In *Proceedings of the 20th New Zealand Geothermal Workshop* (pp. 221–226). [Conference paper](https://pangea.stanford.edu/ERE/pdf/IGAstandard/NZGW/1998/McKibbin.pdf).

Mubarok, M. H., & Zarrouk, S. J. (2016, November 23–25). Steam-field design overview of the Ulubelu geothermal project, Indonesia. In *Proceedings of the 38th New Zealand Geothermal Workshop* (pp. 1–6), Auckland, New Zealand.

National Aeronautics and Space Administration. (2021a, February 10). *Examining iterative convergence*. NPARC Alliance CFD verification and validation tutorial. [Source](https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html).

National Aeronautics and Space Administration. (2021b, February 10). *Validation assessment*. NPARC Alliance CFD verification and validation tutorial. [Source](https://www.grc.nasa.gov/www/wind/valid/tutorial/valassess.html).

Purnanto, M. H., Zarrouk, S. J., & Cater, J. E. (2013). CFD modelling of two-phase flow inside geothermal steam–water separators. *IPENZ Transactions, 40*, 1–10. [Author-uploaded full text](https://www.researchgate.net/publication/269519626_CFD_MODELLING_OF_TWO-PHASE_FLOW_INSIDE_GEOTHERMAL_STEAM-WATER_SEPARATORS).

Rizaldy, Zarrouk, S. J., & Morris, C. (2016, November 23–25). Liquid carryover in geothermal steam–water separators. In *Proceedings of the 38th New Zealand Geothermal Workshop*, Auckland, New Zealand.

Umanzor, C., & Zarrouk, S. J. (2022, November 23–25). The steamfield process design and optimisation tool (SPDOT). In *Proceedings of the 44th New Zealand Geothermal Workshop* (pp. 1–9), Auckland, New Zealand. [Conference paper](https://www.worldgeothermal.org/pdf/IGAstandard/NZGW/2022/053.pdf).

Umanzor, C., Zarrouk, S. J., & Rodríguez, A. (2021, November 23–25). Steam purity troubleshooting: The Berlin geothermal steam field, El Salvador. In *Proceedings of the 43rd New Zealand Geothermal Workshop* (pp. 1–8), Wellington, New Zealand.

Yokkaichi, S. (2026). *Development of a geothermal separator CFD model: liquid transport, collection and wall-film behaviour* [Unpublished draft Part IV Research Project Report; repository version consulted 18 October 2026]. The University of Auckland.

Zarrouk, S. J., & Purnanto, M. H. (2015). Geothermal steam–water separators: Design overview. *Geothermics, 53*, 236–254. [Publisher record](https://www.sciencedirect.com/science/article/abs/pii/S0375650514000637). [DOI](https://doi.org/10.1016/j.geothermics.2014.05.009). The supplied PDF prints 2014, which is retained in the reproduced literature citations and figure credits; the publisher lists the same article in the January 2015 issue. Both dates here identify this DOI.


## Appendix A. Project evidence register

The research compendium is available in the [project GitHub repository](https://github.com/Shuhei-uni/P4P_knowledgeWiki). The `Project` folder contains experiment methods, results and claim limits; `PyAnsys` contains the supporting implementation. The records below identify the evidence used in this report.

The [project-wide findings reference](<../review/project-findings-and-report-claims.md>) records the evidence reviewed on 16 October 2026. Its finding identifiers F01–F21 provide stable links between this report and the source assessment. Table A.1 selects the owning records for each finding; the findings reference retains additional sources and qualifications. The report combines both development routes, while keeping differences in domains, model packages and numerical clocks explicit.

| **Finding** | **Owning evidence** | **Use and boundary** |
|:---|:---|:---|
| F01: reconstructed baseline | [Reconstructed split-inlet baseline](<../../../experiments/phase-02-parity-reset-and-pre-v2-qualification/purnanto-08b-parity-split-inlet/results.md>); [Inlet-loading continuation](<../../../experiments/phase-02-parity-reset-and-pre-v2-qualification/purnanto-08c-inlet-loading-sensitivity/results.md>) | High apparent outlet quality coexisted with imbalance and iteration dependence. These are reconstructed cases. |
| F02: historical mesh study | [Seven-mesh study and continuation](<../../../experiments/phase-02-parity-reset-and-pre-v2-qualification/purnanto-08b-parity-split-inlet/mesh-convergence-checkpoint-20260803.md>) | Within-run pressure and inventory drift limited cross-mesh interpretation. |
| F03: historical DPM | [Twelve-case reconstruction](<../../../experiments/phase-03-dpm-carryover-and-coupling/historical-andy-studies/enthalpy-dpm-replication.md>); [feed-partition control](<../../../experiments/phase-03-dpm-carryover-and-coupling/purnanto-09cV2-dpm-partition-control/results.md>) | Injection categories were accounted for; incomplete trajectories remained unresolved. |
| F04: early film mechanisms | [Mechanism comparison](<../../../experiments/phase-04-ewf-wall-film-mechanisms/observations/04-010v2-ewf-mechanism-comparison.md>); [continuation](<../../../experiments/phase-04-ewf-wall-film-mechanisms/observations/06-010v2-iteration-continuation.md>) | Deposition and release were represented; event counts did not establish separation efficiency. |
| F05: full-geometry outlet | [Boundary screen](<../../../experiments/phase-05-full-geometry-v2/full-geometry-02e-mixture-outlet-characterization/stage-01/results.md>); [loading controls](<../../../experiments/phase-05-full-geometry-v2/full-geometry-03a-mixture-08b-parity-baseline/stage-03/results.md>) | Adding a brine boundary did not by itself establish stable operating discharge. |
| F06: pool feedback | [Phase 6 results](<../../../experiments/phase-06-full-geometry-with-brine-pool/results.md>) | Local inventory feedback worked, but its proxy was not a measured pool level. |
| F07: simplified sink | [Applied-source check](<../../../experiments/phase-07a-simplified-purnanto-liquid-removal/cell-zone-treatment-family/p7-e5-cz-g025/results.md>); [interpretation](<../../../experiments/phase-07a-simplified-purnanto-liquid-removal/interpretation.md>) | Liquid-only numerical withdrawal was implemented; report reduction and units mattered. |
| F08: inlet ramp and smooth-wall control | [Preparation](<../../../experiments/phase-07-1a-absorber-convergence/roughness-family/r0-smooth-control/provenance.md>); [control window](<../../../experiments/phase-07-1a-absorber-convergence/roughness-family/r0-smooth-control/control-window.md>); [source account](<../../../experiments/phase-07b-full-geometry-liquid-removal/convergence-investigation/shuhei-audit.md>) | Lower residuals and exact sink-command tracking did not close the steady liquid account. |
| F09: full-domain collectors | [Closure](<../../../experiments/phase-07b-full-geometry-liquid-removal/closure.md>); [collector-rate comparison](<../../../experiments/phase-07b-full-geometry-liquid-removal/convergence-investigation/coupled-nphase-weaker-sink/results.md>) | Liquid reached the collector, but controlled changes did not remove global imbalance. |
| F10: wall treatment | [Roughness](<../../../experiments/phase-07-2a-wall-liquid-routing/roughness-family/results.md>); [EWF family](<../../../experiments/phase-07-2a-wall-liquid-routing/ewf-family/results.md>) | Lower outlet liquid flux was accompanied by changes in bulk and film stores. |
| F11: startup and local checks | [Early EWF startup](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-03-shortened-reconstruction/early-ewf-startup/results.md>); [commercial steel](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/commercial-steel/results.md>); [Staged film development](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/staged-finalisation/results.md>) | Selected active-bulk film accounts and inner solves passed; whole-system acceptance remained separate. |
| F12: film drainage | [Reference 500 ms](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-03-shortened-reconstruction/early-ewf-startup/inlet-speed-500ms/results.md>); [direct-drain comparison](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/ewf-only-drain/results.md>) | Film reached a drain and could be removed; storage persisted elsewhere. |
| F13: inlet/model comparison | [Split inlet](<../../../experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/f2-split-inlet/results.md>); [Matched coupled-DPM comparison with and without EWF](<../../../experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/results.md>) | Computed retention and routing changed. Small bulk-boundary gaps did not establish useful separation. |
| F14: short resolved drainage | [Historical resolved-outlet tests](<../../../experiments/phase-09-steady-vof-pool/historical-andy-studies/resolved-brine-outlet.md>) | Short conservative rest/drainage checks passed; longer operating holds did not retain the required behaviour. |
| F15: drain-law verification | [Corrected benchmark](<../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/drainage-boundary-verification/results.md>); [full-separator extension](<../../../experiments/phase-09-steady-vof-pool/results.md>) | The simple pressure–flow implementation passed; full-separator stationarity and balance did not. |
| F16: pressure and gravity | [Diagnostic index](<../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/index.md>); [pressure–gravity closure](<../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/pressure-gravity-initialization/closure.md>) | Separate controls narrowed possible explanations without establishing a unique cause. |
| F17: EWF mesh development | [Selected states](<../../../experiments/phase-09-mesh-convergence/results.md>); [Staged film-development procedure](<../../../experiments/phase-09-mesh-convergence/ewf-plan-v1.md>); [679,970-cell mesh local accounts](<../../../experiments/phase-09-mesh-convergence/server1-680k/results.md>) | Four selected 195 ms states show film-storage and drain-rate sensitivity; continuous histories and full numerical/whole-system qualification remain incomplete. |
| F18: proposed designs | [Design comparison](<../../../experiments/phase-10-proposed-design/results.md>); [vertical continuation](<../../../experiments/phase-10-proposed-design/vertical-slit154k/planv1-500ms/results.md>) | Both basic-EWF designs reached 150 ms. A 500 ms design completion or isolated design advantage was not established. |
| F19: single-inlet mesh family | [Results](<../../../experiments/phase-10-single-inlet-mesh-convergence/results.md>); [saved-field assessment](<../../../experiments/phase-10-single-inlet-mesh-convergence/predivergence-mesh-sensitivity.md>) | Spatial and iteration differences remained substantial despite similar selected scalar outputs. |
| F20: reconstructed particle outputs | [Carrier assessment](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-carrier-results.md>); [tracking cap](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-dpm-limit-test.md>); [five enthalpies](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication-enthalpy-results.md>) | Historical estimates were reproduced conditionally; incomplete mass and carryover sensitivity remained. |
| F21: computational cost | [Tetrahedral comparison](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-tet-results.md>) | Fixed-horizon cost was measured; intended geometry parity and equivalent accuracy were not demonstrated. |

*Table A.1. Evidence register for the integrated project findings.*

Historical records preserve reported observations from original notes. Not every remote or archived raw history was available for reanalysis. The review checked selected local machine summaries, including the corrected drain benchmark, the pool-feedback window and the five-enthalpy particle comparison. A completed record or saved case establishes execution evidence; it does not automatically establish scientific acceptance.

## Appendix B. Scope of selected successful numerical checks

The following checks support specific implementation or local-accounting claims. Their different denominators, clocks and system boundaries must be retained when comparing them.

| **Check** | **Reported result** | **Scope of the pass** |
|:---|:---|:---|
| Historical DPM accounts, F03 | All twelve cases met the 0.2% per-injection mass-accounting tolerance. | Reconciliation of particle categories, including the unresolved category; not proof that incomplete droplets were captured. |
| Selected steel-wall roughness, F11 | Continuity mean 0.00184594; film-account error 0.009931% of integrated accretion. | Selected active-bulk window; inner-film residuals unavailable; complete bulk–film–particle closure unverified. |
| Staged film development, F11 | After 35 ms additional film development, at iteration 36,020, 1000/1000 inner solves passed; source-accounting discrepancy 0.252404% of the summed magnitudes of integrated net-phase and DPM sources. | Active-bulk film checks passed; bulk/outlet/collector acceptance did not. The later 1.16832% trial did not pass its 1% film limit. |
| Vertical-blocker film, F11/F18 | At iteration 5290 and film time 7.75 ms, checked inner solves all passed; film mass-balance error 0.000009% of integrated phase accretion. | Bulk was frozen. Accretion 76.003567 kg/s was mostly stored in the film (75.990820 kg/s), so this was not a stationary-film result. |
| Short resolved drainage, F14 | Pool-depletion test at 0.2 ms: storage-aware error 0.4601% of feed; 0.05%-feed test over 1.28 ms: total remainder about $-9.11 \times 10^{-8}$ kg/s at its ten-step check. | Distinct short transient checks; neither establishes sustained full-load operation. |
| Corrected drain-law repeat, F15 | Four cases passed analytical, conservation, residual and stability criteria over iterations 401–500, with no speed/nonfinite guard breach over all 500. | Single-liquid frictionless duct; not calibration of the separator drain. |

*Table B.1. Selected successful checks and their inference limits. Sources are listed under the corresponding findings in Table A.1; the vertical-slit check is recorded in the [early film-development result](<../../../experiments/phase-10-proposed-design/vertical-slit154k/startup-stage3/film-development/results.md>).*

For the corrected duct benchmark, the analytical relation was $U=\sqrt{2\Delta p/[\rho(1+K)]}$. The tested $(K,\Delta p)$ pairs were (0, 200 Pa), (0, 800 Pa), (9, 200 Pa) and (9, 800 Pa), with terminal speeds 0.673523, 1.347046, 0.212987 and 0.425973 m/s, respectively. The [corrected-repeat results and terminal guard assessment](<../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/drainage-boundary-verification/results.md>) distinguish this successful corrected repeat from the earlier startup-guard violations.

### Numerical criteria and assessment windows

These are recorded study tolerances, not universal CFD criteria or estimates of physical accuracy. Residuals retain the solver's scaling. Passing one row does not qualify a different model family.

| **Assessment** | **Window and selected numerical criteria** |
|:---|:---|
| [Full-geometry collector](<../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md>) | Compare iterations 4001–4500 and 4501–5000. Final-window mean absolute source-inclusive phase/mixture imbalance ≤1% of respective measured feed; all active residuals ≤$10^{-3}$. Liquid-volume window-mean change ≤1%, divided by the larger mean with a $10^{-6}$ m$^3$ floor. |
| [Steady VOF pool](<../../../experiments/phase-09-steady-vof-pool/setup.md>) | Final 1000 iterations, split into 500-iteration halves. Phase/mixture mean absolute imbalance ≤0.5%, maximum ≤1% of respective feed. Total and lower-region inventory range ≤1%; half-mean change ≤0.25%, both divided by the complete-window mean. All active residuals ≤$10^{-3}$. Additional routing and two-start requirements below. |
| [Single-inlet carrier](<../../../experiments/phase-10-single-inlet-mesh-convergence/setup.md>) | Final 500 iterations: maximum sampled phase/mixture flux error ≤1% of respective feed; inventory change ≤1%; pressure-drop drift ≤0.5%; mean velocity/vorticity drift ≤1%. Continuity ≤$10^{-4}$ and other active residuals ≤$10^{-3}$. Sampling details for the reconstruction are below. |
| [Corrected single-liquid duct](<../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/drainage-boundary-verification/setup.md>) | Iterations 401–500: analytical flow error ≤2%; maximum mass imbalance ≤0.1% of outlet mass flow; flow range/mean ≤0.1%; pressure range/driving pressure ≤0.1%; active residuals ≤$10^{-6}$. Speed >20 m/s and nonfinite-value guards applied over all 500 iterations. |

*Table B.2. Principal numerical thresholds. The pool and carrier rows are completed by the definitions below; film-window criteria are stated with Table 4.*

The pool also required no systematic inventory drift, stable interface and occupancy, and interface-height change ≤0.02 m or one local vertical cell spacing, whichever was larger. At least 99% of liquid feed had to leave through brine and 99% of vapour through steam, with reverse-phase inflow below 0.1% of its feed. Both starts had to pass jointly and agree within 1% in inventory, 0.5% of feed in outlet phase flux, and 2% in pressure drop. Phase-summed versus native-mixture discrepancies above 0.1% of total feed required audit. Persistent clipping, saturation, divergence or nonfinite fields were unacceptable; persistence after save/reopen was also required.

For the 1500-iteration carrier reconstruction, residuals were checked over iterations 1001–1500; boundary reports sampled iterations 1010–1500 every ten iterations. Inventory change used endpoints 1000 and 1500, divided by the iteration-1000 inventory. The prescribed horizon was completed despite failed numerical qualification, as documented in the [carrier assessment](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-carrier-results.md>).

### Pressure differences and historical drift

The separator studies used static-pressure differences, with the surface definitions in Table B.3. These differ from the total-to-static driving pressure in the single-liquid duct test. No pressure-loss comparison across these model families is inferred from differently weighted quantities.

| **Study** | **Reported pressure difference** |
|:---|:---|
| Historical split-inlet mesh study, Section 5.1 | Fluent's combined mass-weighted static pressure over the liquid and vapour inlet faces, minus mass-weighted static pressure over the steam outlet. The combined inlet value is not an arithmetic average of the two face means. |
| Later mixed/split inlet study | Area-weighted static pressure over the vapour inlet face, minus area-weighted static pressure over the steam outlet. The liquid strip is excluded from this pressure measure, even in the mixed-feed case. |
| Later single-inlet mesh and reconstruction studies | Area-weighted static pressure over the single inlet, minus area-weighted static pressure over the steam outlet. |

*Table B.3. Pressure surfaces and averaging conventions retained from each study.*

For the historical mesh study, sampled pressure-drop values $q_i$ gave percentage drift as $100(\max q_i-\min q_i)/(\frac{1}{n}\sum_i|q_i|)$. The initial final-500-iteration assessment sampled iterations 2500, 2750 and 3000. The continuation used 5500, 5750 and 6000: 33.5908, 35.1713 and 34.0494 kPa, respectively. These give the reported 4.612% drift. It is a sampled range, including the intermediate peak, rather than the change between the first and last samples; it does not bound unsampled fluctuations.

Sources: [historical mesh study and continuation](<../../../experiments/phase-02-parity-reset-and-pre-v2-qualification/purnanto-08b-parity-split-inlet/mesh-convergence-checkpoint-20260803.md>), [later mixed/split comparison](<../../../experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/results.md>) and [single-inlet definitions](<../../../experiments/phase-10-single-inlet-mesh-convergence/setup.md>). The historical metric was checked against its recovered extraction code and monitor history; the pressure weights above are retained rather than retrospectively made uniform.

## Appendix C. Unresolved evidence and claim limits

| **Item** | **Treatment in this report** | **Evidence needed for a stronger statement** |
|:---|:---|:---|
| Current tetrahedral/poly-hexcore geometry | Intended equality is recorded; inferred volumes remain 27.9610 and 22.7930 m³. Cost is reported for the two cases. | Direct volume and boundary/domain comparison before claiming a mesh-only saving. |
| Phase 5 disputed continuations | Claimed outcomes for the disputed turbulence-model, full-load progressive-loading and later diagnostic tests are excluded. | Terminal records or raw histories confirming execution and results. |
| EWF mesh qualification | Four selected 195 ms endpoint comparisons are available; frozen and supplementary bulk-active states remain distinct. Final whole-separator closure is unverified. | Continuous bulk, film, particle, source and inventory histories, inner-film residuals and comparable preparation. |
| Proposed-design continuation | Verified 150 ms basic-EWF endpoints are reported; later 500 ms completion is not claimed. | Verified terminal results from the later continuation, with matched preparation and settings. |
| Historical reconstruction | Incomplete-as-separated convention; unrecovered July binary/tracking cap; Fluent 2024 R2 versus 2025 R2. | Matched settings, boundary-specific escape rates and resolved fates before exact-replication or physical-efficiency claims. |

*Table C.1. Evidence gaps that affect the strength of the final claims.*

Case-specific numerical controls, boundary definitions and mesh statistics remain in the linked records. Appendix E reproduces the principal nine-group injection inputs used in the historical-output comparison. The [reconstruction settings audit](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-settings-audit.md>) provides the traceable injection and model settings for the later DPM comparison. Missing settings are not assumed to be software defaults. Reused figures require creator/source credit in their captions, even where the surrounding scientific account presents the work as one project.

## Appendix D. Model assumptions and their purposes

| **Choice** | **Purpose and limit** |
|:---|:---|
| Inherited material and turbulence settings | Preserve a comparison basis for the reconstructed model. They were not independently validated for the resulting liquid distributions. Steady RANS tested a stationary mean-flow assumption; failure to converge does not prove physical unsteadiness. |
| Collector and pool parameters | The 10 µm continuum diameter, 200 kg feedback target, depletion times and film capture time were modelling or control choices, not measured plant properties. Selected paired changes tested numerical response; these choices did not calibrate a physical drain. |
| Roughness | The 8 mm case was a sensitivity test, not a manufacturing recommendation. The later 0.045 mm steel-wall value was assumed, not measured on the separator. |
| Macroscopic VOF pool | Fixed properties and omission of phase change/surface tension isolated bulk pool and outlet behaviour. Thermal response, capillary wetting and interfacial breakup were outside that assessment. The 620,431-cell domain volume was 27.0631 m$^3$. |
| Poly-hexcore construction | Curvature/proximity sizing with 12 requested wall layers and growth factor 1.15. Local stair-stepping warnings remained; requested layers did not establish achieved or matched wall resolution. |
| Historical enthalpy reconstruction | Total feed was 197.61 kg/s. Steam/liquid feeds at 1440, 1520, 1600, 1680 and 1760 kJ/kg were respectively 64.85/132.76, 72.77/124.84, 80.69/116.92, 88.61/109.00 and 96.52/101.09 kg/s. These were prescribed operating inputs, not predictions from an energy balance. |

*Table D.1. Why the main assumptions were used and what they do not establish. Source settings: [collector](<../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md>), [pool feedback](<../../../experiments/phase-06-full-geometry-with-brine-pool/results.md>), [steady pool](<../../../experiments/phase-09-steady-vof-pool/setup.md>), [film and roughness](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/commercial-steel/setup.md>), [direct drain](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/ewf-only-drain/setup.md>), [mesh family](<../../../experiments/phase-10-single-inlet-mesh-convergence/setup.md>) and [enthalpy reconstruction](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication-enthalpy-sweep.md>).*


### Spatial definitions for the principal comparisons

The nominal reference dimensions below describe the intended reconstruction basis. They do not prove that every supplied mesh has the same geometry. Coordinates belong to the named family and are not plant elevations.

| **Configuration or feature** | **Spatial definition and evidence limit** |
|:---|:---|
| Nominal spiral-inlet reference | Vessel diameter 2.134 m; square inlet 0.724 × 0.724 m; nominal steam passage diameter 0.876 m; nominal brine pipe diameter 0.508 m. These reference dimensions do not resolve the tetrahedral/poly-hexcore volume discrepancy. |
| Later truncated meshes | The inspected 342,609-cell mesh has a closed bottom at approximately $y=0$ m. The 60,964-cell contact-collector model uses the existing 715-cell lower zone selected by cell-centre $y\leq0.10$ m. Its separating-face vertices span $y=0.03211$–0.18477 m; this is a stepped mesh boundary, not a fitted plane. |
| Direct film drain | Lower outer-wall segment in the truncated model: 34 faces with centres at $y=0.043964$–0.047341 m. Vertices extend to 0.118351 m. The sink acts on film on these faces; its extent is not identical to the bulk-cell selection. |
| Full-geometry collector comparison | On the 620,431-cell mesh, the numerical lower datum is $y=-1.484584$ m. The mapped historical truncation is $y=+0.020$ m. The matched 0.02/0.10 s depletion-time comparison selects all fluid cell centres up to $y=-0.882750$ m, with no horizontal crop: 41,258 cells over the lower 40% of that vertical span. This is a height fraction, not a volume fraction. |
| Matched mixed/split inlet comparison | On the 60,964-cell mesh, outer-strip area 0.0048899165 m$^2$ and remaining-face area 0.51928608 m$^2$; the strip is 0.93288% of total area. Mixed feed gives 26.81 m/s on both faces. Pure-phase split commands give 27.13795 m/s liquid and 26.80691 m/s vapour. Both configurations retain the same face geometry and per-face turbulence inputs. |

*Table D.2. Reference dimensions and recorded extents used to interpret the central comparisons. Sources: [reference geometry](<../../../technical/purnanto-spiral-inlet-geometry.md>), [truncated-mesh inspection](<../../../experiments/phase-07a-simplified-purnanto-liquid-removal/mesh-inspection.md>), [contact collector](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-02-combined-ewf-roughness/ewf-absorber/setup.md>), [direct film drain](<../../../experiments/phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/ewf-only-drain/setup.md>), [full-mesh mapping](<../../../experiments/phase-07b-full-geometry-liquid-removal/geometry-proof.md>), [matched collector setup](<../../../experiments/phase-07b-full-geometry-liquid-removal/convergence-investigation/coupled-nphase-weaker-sink/setup.md>) and [inlet parity audit](<../../../experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/baseline-lineage-audit.md>).* 

The available spatial checks do not establish complete CAD parity across all families. Dimensioned as-built views of the proposed blocker and ramp are not supplied here; those cases support only the reported development endpoints, not a reproducible geometric design comparison.


## Appendix E. Particle inputs for the historical enthalpy reconstruction

Each group was an inert, uniform-diameter surface injection over the mixed inlet boundary, in the stationary global frame. Release positions were not randomised. The prescribed velocity was normal to each inlet face, with the same magnitude for all nine groups at a given enthalpy (Table E.2). Turbulent dispersion was disabled. The recorded Stokes–Cunningham drag law with Cunningham factor 1.0 was retained to reproduce the historical settings; its applicability over this diameter range was not established by the reported evidence. These inputs define the numerical reconstruction, not a measured inlet droplet population or a qualified drag model for performance prediction.

| **Group** | **Mass weight (%)** | **1440** | **1520** | **1600** | **1680** | **1760** |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.1625 | 7.149 | 6.2979 | 5.6214 | 5.0712 | 4.616 |
| 2 | 0.6675 | 35.745 | 31.489 | 28.107 | 25.356 | 23.08 |
| 3 | 0.8300 | 71.49 | 62.979 | 56.214 | 50.712 | 46.16 |
| 4 | 1.6700 | 142.98 | 125.96 | 112.43 | 101.42 | 92.32 |
| 5 | 1.6700 | 214.47 | 188.94 | 168.64 | 152.14 | 138.48 |
| 6 | 20.0000 | 443.23 | 390.47 | 348.52 | 314.42 | 286.19 |
| 7 | 25.0000 | 714.89 | 629.79 | 562.14 | 507.12 | 461.6 |
| 8 | 25.0000 | 1072.3 | 944.68 | 843.2 | 760.68 | 692.4 |
| 9 | 25.0000 | 2073.2 | 1826.4 | 1630.2 | 1470.7 | 1338.6 |

*Table E.1. Diameters in µm for each enthalpy column (kJ/kg), rounded to five significant figures. Group weights are percentages of represented injected liquid mass and sum to 100%; they are not parcel-count fractions. The recorded six-decimal mass-flow inputs produce only rounding-level differences in the first two weights at 1760 kJ/kg.*

| **Enthalpy (kJ/kg)** | **Face-normal injection speed (m/s)** | **Total represented particle flow (kg/s)** |
|---:|---:|---:|
| 1440 | 21.591272 | 132.76 |
| 1520 | 24.228170 | 124.84 |
| 1600 | 26.865069 | 116.92 |
| 1680 | 29.501968 | 109.00 |
| 1760 | 32.135537 | 101.09 |

*Table E.2. Prescribed particle speed and represented mass-flow basis. Multiply a Table E.1 mass fraction by the corresponding total here to recover each group's mass-flow weight, subject to the stated rounding.*

The carrier retained the full Eulerian phase feeds listed in Table D.1. Because this reconstruction used one-way diagnostic tracking, the particle weights in Table E.2 were not added as an extra physical liquid feed. Enthalpy changed the prescribed phase feeds, particle diameters and injection speed; it did not activate energy or phase-change calculations. Particle boundary fates and tracking controls are stated in Section 3.6. The exact July case binary and original tracking cap remain unrecovered, so these recovered inputs do not establish byte-identical historical replication.

Sources: [recovered settings audit](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-settings-audit.md>), [enthalpy reconstruction protocol](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication-enthalpy-sweep.md>), [1600 kJ/kg reconstruction results](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-dpm-results.md>) and [enthalpy-sweep results](<../../../experiments/phase-10-single-inlet-mesh-convergence/replication-enthalpy-results.md>). The completed result records verify that the saved injection readbacks matched those inputs.

## Appendix F. Explicit brine-outlet and pool investigations

This branch tested whether resolving the lower vessel and controlling brine discharge could supply a reliable operating liquid inventory. It included Mixture and VOF calculations, outlet and feedback treatments, and separate implementation/startup tests. The studies established selected short-duration and component-level successes, but not a sustained stationary separator state. The detailed evidence is retained here to support the main-text summary without treating each diagnostic as a separate project outcome.

### F.1. Domain, properties and boundary treatment

The full-geometry Mixture collector used Manninen slip, Schiller–Naumann drag and a 10 µm continuum liquid diameter; its properties are included here because it shared the fixed-property basis of the later steady-pool model. Its closed-brine collector comparison is retained separately in Appendix G.1.

Resolved-pool calculations used VOF with shared velocity. Historical transient tests used explicit VOF, whereas the later steady-pool campaign used implicit VOF. Table F.1 gives the fixed properties of the full-geometry collector and steady-pool models. Energy, phase change, DPM and EWF were disabled in those families. Surface tension was omitted in the steady macroscopic-pool model. These assumptions differ from the later film configurations and recovered particle properties.

| **Property** | **Liquid** | **Vapour** |
|:---|:---|:---|
| Density (kg/m$^{3}$) | 881.77 | 5.73 |
| Dynamic viscosity (Pa·s) | 145.96 × 10$^{-6}$ | 15.188 × 10$^{-6}$ |

*Table F.1. Properties for the full-geometry collector and steady VOF pool families.*

The full-geometry collector and steady-pool cases imposed liquid and vapour inlet velocities of 27.118 m/s, with nominal phase feeds of 116.921 and 80.690 kg/s. Inlet turbulence intensity was 2.11%, with hydraulic diameters of 0.01338 m for liquid and 0.72061 m for vapour. Steam-outlet gauge pressure was 1.12 MPa at zero operating pressure. Gravity acted downwards at 9.81 m/s$^{2}$; walls were stationary and no slip. Steam-outlet backflow was vapour, while VOF brine backflow was liquid. Reverse flow was retained with its sign.

The steady-pool outlet represented an ideal reservoir with external liquid level 0.10 m and height-dependent pressure. Initial pools of 0.10 and 0.30 m tested starting-state dependence under the same external head. Separate pressure and resistance studies changed the discharge condition. Earlier feedback calculations used liquid mass below y=0.10 m as a pool proxy and adjusted brine pressure towards an assumed 200 kg target; they did not control a measured liquid height.

The full-geometry collector and steady VOF family used 620,431 cells; earlier outlet/control work used a separate 231,376-cell mesh.

The main full-geometry Mixture baseline used SIMPLE, PRESTO pressure, second-order momentum/turbulence and QUICK volume fraction. Later controlled cases used Coupled; the steady-pool model used compressive volume-fraction reconstruction and implicit body force. Each comparison retained its actual pseudo-time and relaxation settings. Global Time Step in these steady calculations was numerical pseudo-time, not elapsed physical time.

<!-- Evidence: ../../../experiments/phase-01-purnanto-baseline-and-inlet-exploration/interpretation.md; ../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md; ../../../experiments/phase-09-steady-vof-pool/setup.md; ../../../experiments/phase-09-steady-vof-pool/historical-andy-studies/resolved-brine-outlet.md. -->

<!-- Evidence: ../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md; ../../../experiments/phase-09-steady-vof-pool/setup.md; ../../../experiments/phase-06-full-geometry-with-brine-pool/results.md; ../../../experiments/phase-02-parity-reset-and-pre-v2-qualification/purnanto-08b-parity-split-inlet/mesh-convergence-checkpoint-20260803.md; ../../../experiments/phase-09-mesh-convergence/setup.md; ../../../experiments/phase-10-single-inlet-mesh-convergence/setup.md; ../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-tet-results.md. -->

### F.2. Outlet response and pool feedback

Including the lower vessel and a brine boundary supplied a route for separated liquid to leave. The resulting discharge nevertheless depended strongly on outlet treatment and initialisation. Of twelve initial full-geometry boundary tests, four completed the selected 500-iteration horizon and eight failed numerically. Pressure, vent and prescribed-withdrawal treatments produced distinct phase-routing responses, so an open lower boundary alone did not determine an acceptable operating state.

Two targeted vent cases illustrate the unresolved steady account. Their brine liquid discharge reached 661.98 and 596.65 kg/s against approximately 116.921 kg/s liquid feed, while total liquid inventory continued increasing over the final iteration window. Because these were steady calculations, the iteration history could not be interpreted as physical depletion of an initial pool. Reduced-load and numerical-control tests sometimes produced much smaller discrepancies, but those improvements did not consistently persist at full loading.

The subsequent feedback study controlled the liquid mass below a fixed elevation rather than a directly measured free-surface height. The target mass of 200 kg and the permitted outlet-pressure range were numerical assumptions. Increasing feedback strength reduced the local inventory-proxy drift from 0.0337 to 0.00620 kg per iteration and reduced the total-feed-normalised mismatch from 10.18% to 5.11% in the short comparison windows. The feedback therefore changed the measured inventory in the intended direction, but outlet pressure reached its imposed lower bound before the target could be maintained.

In the longer test, final-1000 mean liquid input was 116.85 kg/s, brine liquid output was 94.47 kg/s and steam-outlet liquid was 6.28 kg/s. The remaining positive rate was 16.10 kg/s, or 13.8% of liquid feed. The separately reported 8.12% used total mixture feed as its denominator. The long test therefore retained a material discrepancy after the short-window control improvement. It did not establish a stationary pool or a calibrated relation between outlet pressure and physical liquid level.

<!-- Evidence: master findings F05–F06; ../../../experiments/phase-05-full-geometry-v2/full-geometry-02e-mixture-outlet-characterization/stage-01/results.md; stage-02/results.md; ../../../experiments/phase-06-full-geometry-with-brine-pool/stage-04-stronger-feedback-hypothesis/results.md; stage-06-long-horizon-surrogate-hypothesis/results.md. Phase 5 transient records remain bounded tested failures, not a resolved universal cause. -->

### F.3. Outlet-resistance verification and full-domain controls

A frictionless single-liquid duct independently checked the outlet-resistance implementation. For $K=0$ or 9 and driving pressure 200 or 800 Pa, the analytical velocity was

$$U=\sqrt{\frac{2\Delta p}{\rho(1+K)}}.$$

Here, $\Delta p$ is inlet total pressure minus external static pressure, $\rho$ is liquid density and $K$ specifies added outlet resistance. The unit term accounts for outlet kinetic head. The corrected test used a modest nonzero starting velocity and 500 iterations per case. Numerical acceptance used the final 100 iterations; speed and finite-value guards covered all 500. This isolated a boundary-law implementation, not multiphase separator hydraulics. Separate hydrostatic, sealed-boundary, interface and pressure-datum controls examined startup disturbances under their own conditions.

<!-- Evidence: ../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md; ../../../experiments/phase-09-steady-vof-pool/setup.md; ../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/drainage-boundary-verification/results.md; ../../../experiments/phase-09-steady-vof-pool/follow-on-diagnostics/index.md. -->

The full-vessel drainage studies tested liquid discharge through an explicit brine outlet. Short transient VOF tests supplied positive results under restricted conditions. At 0.2 ms in one test, brine discharge reached 4692.87 kg/s against 116.92 kg/s feed, yet the storage-aware balance error was only 0.4601% of feed. Pool depletion supplied the difference. This was not controlled operating drainage, but showed why an inlet–outlet difference alone cannot diagnose transient nonconservation. A zero-feed hydrostatic test remained bounded for ten steps (10 µs). At 0.05% nominal feed, another ten-step test covered 1.28 ms with pure-liquid brine discharge and total imbalance near $-9.11\times10^{-8}$ kg/s. Longer holds did not retain the required balance.

The outlet-resistance implementation was then verified in a simpler single-liquid duct. Four tests combined loss coefficients $K=0$ and 9 with pressure differences of 200 and 800 Pa. With the corrected nonzero initial velocity, all four reproduced the analytical velocities and passed residual, balance and stability criteria over the final 100 iterations. Speed and finite-value guards passed throughout all 500 iterations. Appendix B gives the velocities and criteria. This verified the forward-flow resistance implementation for the simple duct.

That component result did not resolve the full-separator behaviour. Both initial pool levels in Figure F.1 lost liquid and failed the joint conservation and stationarity assessment. An unchanged higher-pool extension from iteration 1000 to 2000 lost another 15.56% of inventory and retained a mean absolute liquid imbalance of 401.18% of feed. Separate full-domain resistance and solver changes did not resolve both problems together: one set of solver settings reduced late liquid imbalance by about 60% while increasing inventory loss from 4.15% to 32.91%.

![Steady VOF comparison from two initial pool levels, showing continuing numerical development.](../figures/two-start-comparison.png)

*Figure F.1. Steady VOF calculations from two initial pool levels, plotted against solver iteration. Grey lines mark 0.5% liquid imbalance and $10^{-3}$ scaled continuity residual; Appendix B gives the full acceptance criteria. Neither calculation established a stationary operating pool. Source: the audited two-start comparison in the project records.*

Controlled startup tests narrowed possible explanations. An equivalent pressure-datum change removed drift in a zero-gravity control, but gravity-on motion persisted after sealing the brine boundary and in a separate homogeneous-liquid case without an interface. Thus neither outlet leakage nor the presence of an interface was necessary for every observed disturbance. These tests assessed preservation of the prepared rest state; they did not test eventual convergence after that disturbance or establish a unique numerical cause.

<!-- Evidence: master F14–F16; ../../../experiments/phase-09-steady-vof-pool/historical-andy-studies/resolved-brine-outlet.md; follow-on-diagnostics/drainage-boundary-verification/results.md (corrected repeat); results.md; follow-on-diagnostics/steady-vof-solver-method/results.md; follow-on-diagnostics/pressure-gravity-initialization/closure.md. -->

### F.4. Interpretation and remaining limits

The corrected single-liquid duct benchmark reproduced the analytical response for four pressure/resistance combinations and passed the final-100 residual, balance and stability criteria. Speed and finite-value guards passed over all 500 iterations. This verifies the forward-flow resistance law for that simple problem; it does not determine a real separator's resistance or downstream head. Applying the treatment to the full domain did not establish a conservative stationary pool.

Transient checks over microseconds to milliseconds nevertheless showed that conservative discharge could be represented. In one, brine outflow greatly exceeded feed while the storage-aware balance remained small: the pool supplied the difference. Low-feed tests achieved clean drainage briefly but failed longer holds. These outcomes establish short transient accounting, not sustained operating control. Inventory change over steady solver iterations cannot serve as a physical storage term. Conversely, failure to find a steady solution does not establish physical unsteadiness; numerical treatment, model assumptions and boundary conditions remain competing explanations.

The numerical controls narrowed possible explanations. A changed set of solver settings reduced late liquid imbalance by about 60% while increasing inventory loss from 4.15% to 32.91%. Separate startup tests showed motion without operating feed, with the brine boundary sealed in a two-phase case, and in homogeneous liquid with open hydrostatic outlets. A pressure-datum change removed one zero-gravity drift but did not cure gravity-on motion. These observations justify further pressure–gravity and initialisation tests; they do not identify one cause for every failure or prove that an eventual steady solution is impossible.

<!-- Sources: master claims F14–F16; phase-09-steady-vof-pool/historical-andy-studies/resolved-brine-outlet.md; follow-on-diagnostics/{drainage-boundary-verification,steady-vof-solver-method}/results.md; follow-on-diagnostics/pressure-gravity-initialisation/closure.md. -->

## Appendix G. Supporting development, mesh and runtime comparisons

These results retain the detailed checks behind the main findings. They distinguish implementation response, numerical development and conditional output agreement from physical separator performance. Their internal configurations and observation windows remain separate.

### G.1. Source integration and full-geometry collector response

Alongside the full-vessel outlet work, a lower-cell-zone sink provided an alternative liquid-removal mechanism in the truncated model. Its liquid-phase mass source was addressable independently of the vapour phase, and the applied removal could be checked against the command. An apparent early mismatch was traced to the extraction operation: summing the already integrated source gave −28.272494 kg/s, consistent with the intended command. The earlier volume integral had applied an additional volume weighting. Correcting this account established source application, although the surrounding solution still accumulated liquid.

In the separate full-geometry depletion-collector study, the brine face was closed and removal followed the local-content law in Section 3.4. Collector thickness, depletion time and solver treatment were examined separately where tests could share a starting field. The final matched strength comparison changed the depletion time from 0.02 to 0.10 s while holding the Coupled solver and phase-volume-fraction settings fixed.

The study also distinguished source response from global balance. Increasing depletion time fivefold, from 0.02 to 0.10 s, raised mean collector liquid volume from 0.006259 to 0.030844 m$^3$, while removal remained similar at 275.962 and 272.028 kg/s. Mean absolute liquid imbalance remained 144.369% and 148.213% of feed. This controlled response did not identify collector strength alone as a solution to the full-domain problem.

<!-- Evidence: master findings F07–F09; ../../../experiments/phase-07-1a-absorber-convergence/roughness-family/r0-smooth-control/provenance.md and results.md; ../../../experiments/phase-07b-full-geometry-liquid-removal/convergence-investigation/shuhei-audit.md; coupled-nphase-weaker-sink/results.md. Figure: ../../Shuhei Report/figures/results-described-early-development.provenance.json; low-feed minimum reported in ../../Shuhei Report/draft/03-results.md. -->

<!-- Evidence: ../../../experiments/phase-07-1a-absorber-convergence/dynamic-thin-outer-ring/setup-v2-corrected-absorber.md; ../../../experiments/phase-07-1a-absorber-convergence/roughness-family/r0-smooth-control/provenance.md; ../../../experiments/phase-07b-full-geometry-liquid-removal/s040-collector/setup.md; ../../../experiments/phase-07b-full-geometry-liquid-removal/convergence-investigation/coupled-nphase-weaker-sink/results.md; ../../../experiments/phase-07-2a-wall-liquid-routing/stage-03-shortened-reconstruction/early-ewf-startup/setup.md. -->

### G.2. Roughness, early film and particle-partition screens

The developed control allowed wall treatments to be compared from a common starting field. Roughness changed liquid outlet flow non-monotonically. A roughness height of 0.05 mm increased the tail mean by 21.21%, whereas 8 mm reduced it from 24.3715 to 13.6253 kg/s, a 44.09% decrease. The latter case also lost 187.11 kg of bulk liquid from the shared starting solution. Its lower outlet flow therefore accompanied a substantially different retained inventory; it did not establish an optimum roughness or a corresponding gain in separation efficiency.

EWF supplied a separate liquid store and observable wall-transfer mechanisms. Early deposition, splash and release calculations developed film inventories of approximately 0.201–0.207 kg at iteration 5000. Later phase-accretion work produced film mass of 3.1112 kg at 30 ms, increasing to 5.842 kg during a further 5000-update continuation. Bulk inventory was then about 63 kg and liquid outlet flow about 1.734 kg/s. However, some combined roughness/EWF settings reached the configured thickness cap and developed extreme film velocities. Completing the calculation therefore did not show that the film solution met the required numerical limits.

Droplet partition was also made explicit. One control assigned 111.074 kg/s to Eulerian liquid and 5.846 kg/s to represented DPM liquid, preserving the total 116.920 kg/s feed. This resolved feed allocation, but approximately 51.77% of represented particle mass remained incomplete. The historical six-condition baseline and spiral-inlet sweeps likewise reconciled their reported particle categories within the 0.2% per-injection mass tolerance, without determining the eventual fate of incomplete tracks.

<!-- Evidence: master findings F04, F10–F11; ../../../experiments/phase-07-2a-wall-liquid-routing/roughness-family/results.md; ewf-family/results.md; stage-03-shortened-reconstruction/early-ewf-startup/results.md; stage-04-ewf-wall-parameters/commercial-steel/results.md and staged-finalisation/results.md; ../../../experiments/phase-10-proposed-design/vertical-slit154k/startup-stage3/film-development/results.md. -->

<!-- Evidence: master F03/F13; ../../../experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/results.md and f2-split-inlet/results.md; ../../../experiments/phase-03-dpm-carryover-and-coupling/purnanto-09cV2-dpm-partition-control/results.md; historical-andy-studies/enthalpy-dpm-replication.md. F3/F4 comparison: five matched pairs, final500 window ending N16000; not the full65-point matrix. -->

### G.3. Film-mesh endpoints and proposed geometries

The selected-state analysis compared four meshes at 195 ms, using saved film fields and endpoint reports. Table G.1 gives the quantities used in Section 5.5. The direct-drain rate is the source expression evaluated on the saved lower-wall film, not a cumulative collected mass or a time-window average.

| Cells | Total film (kg) | Bulk liquid through steam outlet (kg/s) | Instantaneous direct film drain (kg/s) |
|---:|---:|---:|---:|
| 60,964 | 7.489776 | 0.548691 | 22.716049 |
| 342,609 | 2.820786 | 0.495744 | 7.167794 |
| 679,970 | 2.950425 | 0.496423 | 6.777898 |
| 997,604 | 2.056433 | 0.477213 | 4.586771 |

*Table G.1. Selected 195 ms frozen-bulk states from the 17 October analysis. Values are reproduced at the precision of the project results table. Bulk outlet flow describes the held forcing; it does not supply a complete bulk–film–particle mass account.*

Starting film ages ranged from 0.700 to 0.900 ms. Each mesh retained its own bulk field, and the 342,609-cell starting pair preceded an additional bulk-active adjustment. No continuous selected-run film-inventory, source or drain histories were recovered, so the snapshots cannot establish late slopes, cumulative collection or integrated film closure. Film inner-residual histories and DPM fates were also unavailable. Saved stripping and edge-separation counter differences describe internal transfers; their receiving-phase and outlet fates were not verified. The 2.6-million-cell mesh had only an initial-state reference in this extraction.

Source: [selected-state analysis and history limits](<../../../experiments/phase-09-mesh-convergence/results.md#selected-starting-and-195-ms-states--17-october-2026>) and [figure/source-pair provenance](<../../../experiments/phase-09-mesh-convergence/figures/selected-mesh-response.provenance.json>).

<!-- Source audit: The analysis recorded nine case/data pairs: fourteen files matched shared reference hashes, while four 997k files had fresh hashes without an independent shared manifest. The values above are drawn from the committed analysis; this report update did not repeat its binary extraction. -->

The wall-film method was extended across five supplied meshes. Four reached the selected 195 ms frozen-bulk endpoint, and three also completed a supplementary 5 ms stage with bulk equations active (Table G.2). This was sustained film development under the staged procedure; film time did not represent an equivalent duration of fully coupled physical separator operation.

| Cells | Verified film-development endpoint | Supplementary bulk-active endpoint |
|---:|:---|:---|
| 60,964 | 195 ms | 200 ms |
| 342,609 | 195 ms | Later work supplementary; not used here |
| 679,970 | 195 ms | 200 ms |
| 997,604 | 195 ms | 200 ms |
| 2,596,657 | 58.350 ms saved and reopened | 195/200 ms completion unverified |

*Table G.2. Recorded endpoints for the staged EWF mesh family. Completion establishes the available development states, not a passed convergence criterion. The selected-state comparison is given in Table G.1; continuous histories and full numerical qualification remain incomplete.*

Selected intermediate film accounts were small. On the 679,970-cell mesh, discrepancies were 0.242% over 3.5–8.5 ms and 0.238% over 8.5–33.5 ms, below the recorded 1% criterion. Later windows gave 1.625% and 1.634%, and some film steps reached their inner-iteration cap. Development continued after numerical gates were disabled; the supplementary bulk-active 195–200 ms stage reached a peak film Courant number of 4.92. That warning belongs to the extension, not the selected 195 ms state. Earlier local balance passes therefore did not establish numerical acceptance at the final saved film times.

During initial vertical-blocker film development with bulk fields fixed, all checked inner-film solves passed and the film mass-balance error was $9 \times 10^{-6}$% of integrated phase accretion. Liquid nevertheless accumulated in film at 75.99 kg/s, so the film was not stationary.

Two proposed internal geometry changes, a vertical film blocker and an angled film ramp, tested whether these features changed liquid routing and outlet behaviour. The blocker was intended to intercept wall liquid before it returned to the inlet steam; the ramp was intended to guide that liquid downward. Both reached 150 ms using basic EWF and frozen bulk fields, on meshes of 154,063 and 213,232 cells respectively. Their basic film settings were matched, but mesh resolution and preparation histories differed.

A separate comparison used earlier snapshots: the vertical blocker at 50.9 ms with enhanced EWF and the angled ramp at 50.0 ms with basic EWF. In the selected inlet-wall region, the blocker snapshot had concentrated film storage, whereas the angled snapshot had a thinner film and a more downward mean film velocity. Area-weighted mean thicknesses were 388.69 and 24.92 µm respectively; wet-area mean vertical velocities were −2.549 and −4.123 m/s, with negative values directed downward. These quantities describe local storage and transport, not net drainage or separation efficiency. The different film models, meshes, selected wall areas and preparation histories prevent attributing the differences to geometry alone. These observations must not be presented as a comparison of the later 150 ms basic-EWF endpoints.

A later attempt to extend the vertical-design calculation to 500 ms failed while the bulk equations were active; a short recovery endpoint was verified, but the subsequent command outcome and 500 ms completion remained unconfirmed. The angled-design extension had not been completed. The completed 150 ms cases therefore supply developed film states for further assessment, without an isolated design-benefit comparison.

A third concept, an external collection channel, was proposed to remove circulating wall liquid through a shell opening and route it downward outside the vessel. The poster and 5 October meeting record identify it as future work; no completed test was identified in the available experiment records. Section 7.2 retains it alongside further controlled assessment of the two implemented designs.

<!-- Geometry evidence: ../../../experiments/phase-10-proposed-design/inlet-comparison-50ms.md (earlier enhanced-vertical/basic-angle comparison); vertical-slit154k/basic-ewf-10us/results.md and angled-slit213k/results.md (150 ms basic-EWF endpoints); ../../../Poster/A1 Landscape — Geothermal Separator Poster — Working Draft.pptx, slide 1; ../../../meetings/otter/2026-10-05-separator-liquid-film-and-roughness-analysis.md, 25:55–27:45. -->

<!-- Evidence: master F17–F19; ../../../experiments/phase-09-mesh-convergence/ewf-plan-v1.md and selected per-server results; ../../../experiments/phase-10-proposed-design/results.md and vertical-slit154k/planv1-500ms/results.md; ../../../experiments/phase-10-single-inlet-mesh-convergence/results.md and predivergence-mesh-sensitivity.md. -->

### G.4. Conditional enthalpy agreement and runtime comparison

Under the explicit convention that incomplete particles were separated, the five estimates from the poly-hexcore mesh differed from the project's July tetrahedral estimates by no more than 0.018449 percentage points (Table G.3), using 68.06% fewer cells. However, 16.78–33.29% of represented particle mass remained incomplete, and escaped mass was 1.55–2.30 times the historical estimates. Near-100% efficiency values compressed material differences in escaped and unresolved mass. The historical July results used Fluent 2024 R2, whereas the reconstruction used Fluent 2025 R2. This version difference and the unrecovered July tracking cap further limit the historical comparison.

| Enthalpy (kJ/kg) | Poly-hexcore assumed efficiency (%) | July tetrahedral estimate (%) | Poly-hexcore incomplete mass (% injected) |
|---:|---:|---:|---:|
| 1440 | 99.972936 | 99.984272 | 19.34 |
| 1520 | 99.965412 | 99.980647 | 16.78 |
| 1600 | 99.967397 | 99.985845 | 16.86 |
| 1680 | 99.967927 | 99.982606 | 21.27 |
| 1760 | 99.959215 | 99.973618 | 33.29 |

*Table G.3. Conditional enthalpy comparison. Incomplete particles are assumed separated in both reported estimates. The incomplete fraction is calculated from the recorded mass categories. The July project estimates are distinct from the fresh timing benchmark; the comparison does not establish physical capture of incomplete tracks.*

Only 1600 kJ/kg received a fresh tetrahedral repeat on the same computer and in the same Fluent version (2025 R2). Its assumed-capture estimate was 99.880431%, compared with 99.967397% for the poly-hexcore mesh; this was separate from Table G.3. Carrier calculation required 42.01 versus 86.17 min; DPM required 3.98 versus 7.06 min, excluding setup, saving and extraction. DPM workloads differed: 11,079 parcels on the poly-hexcore mesh versus 98,388 on the tetrahedral mesh. Equal step caps also need not give equal trajectory durations on different meshes. The measured savings describe the tested calculations, not equal-work tracking cost or time to equivalent accuracy.

The tetrahedral and poly-hexcore meshes were intended to represent the same fluid domain. However, initial vapour mass divided by the prescribed constant density implied volumes of 27.9610 and 22.7930 m$^3$, respectively. The cause of this difference remains unexplained. A direct comparison of fluid-region volumes, bounds, inlet and outlet dimensions, and included lower-vessel volume is needed before isolating the effect of mesh construction on output or runtime. This unresolved check and the different parcel workloads limit the cost comparison; they do not establish that the published domain could not be reproduced.

<!-- Evidence: master F20–F21; ../../../experiments/phase-10-single-inlet-mesh-convergence/replication1600-carrier-results.md; replication1600-dpm-limit-test.md; replication-enthalpy-results.md; replication1600-settings-audit.md; replication1600-tet-results.md; ../../../../PyAnsys/output/phase10-single-inlet-mesh-convergence/replication-enthalpy-M04/efficiency-comparison.csv. -->
