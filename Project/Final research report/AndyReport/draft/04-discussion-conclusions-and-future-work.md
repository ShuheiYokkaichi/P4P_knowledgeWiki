# Part 4 — Discussion, conclusions and future work

## 6. Discussion

### 6.1. Progress towards a credible inlet-condition model

The investigation established capabilities for testing inlet effects: separate phase-inlet regions, controlled loading, numerical collection and wall-film transport. These enabled comparisons of liquid retention, removal and sensitivity to numerical choices. The contribution is both the tested model components and the evidence needed to judge their predictions. Each comparison is interpreted against its own conservation, storage and convergence checks.

Figure 6 locates the additional wall and base enrichment, complementing the approximately 37% greater retained liquid in the split-inlet reconstruction at matched 10,000-iteration endpoints. The comparison demonstrates sensitivity to the prescribed distribution under matched phase feeds and the same startup procedure. It was limited to the imposed outer-wall liquid arrangement, without stationary inventories or an upstream pipe calculation establishing the regime. Its contribution is therefore a demonstrated change in predicted distribution and retention; its effect on physical separation efficiency remains unestablished.

The baseline mesh study explained why the investigation had to extend beyond the inlet. Liquid inventory and pressure continued to change with iteration, while the inherited domain omitted a separate brine-removal path. A model intended to predict useful separation had to account for the liquid after it reached the wall and base. This motivated testing removal and transport, alongside the numerical checks needed to interpret their effects.

<!-- Sources: review/project-findings-and-report-claims.md F01–F02, F05–F07, F13; Project/experiments/phase-08-storyline-reconstruction/stage-01-60k-storyline/f2-split-inlet/results.md. -->

### 6.2. Collection and startup procedures made wall studies practical

The collector and staged preparation supplied a developed field from which roughness and film treatments could be compared. This was a practical advance: the study could introduce additional wall processes and examine their response from controlled starting conditions. Preparation and Coupled/Global Time Step treatment changed together, so the improved numerical behaviour cannot be assigned to ramping alone.

The full-feed balance also revealed a restriction of the throughput-based collector. Because the sink already removed the whole liquid feed, additional liquid leaving through the steam outlet produced excess removal. Correct source delivery verified implementation but could not remove that restriction. The separate full-geometry depletion collector responded to its local-content law without establishing global balance (Appendix G.1); these different outcomes do not identify one common cause for every configuration.

The modelling lesson is to assess collection rate, storage and liquid destination together. Selected particle cases had small bulk-boundary gaps while sending nearly all water through the steam outlet. Conversely, a removal source could operate correctly while the total liquid account remained inconsistent. Reports therefore need to identify whether they include sources, count each transfer once and use the stated phase or mixture denominator. This also applies to film release already included in a net source.

<!-- Sources: master claims F08–F09, F13; phase-07b-full-geometry-liquid-removal/convergence-investigation/shuhei-audit.md; phase-07b-full-geometry-liquid-removal/closure.md; phase-08-storyline-reconstruction/stage-01-60k-storyline/results.md. -->

### 6.3. Film modelling separated local drainage from continued accumulation

EWF extended the study from liquid distribution in the vessel to transport and storage on its walls. Figure 8 shows the resulting insight: drainage can become sustained while liquid continues to accumulate. At 500 ms, drainage remained below accretion and the difference entered storage. The film representation made that distinction measurable instead of treating arrival at the wall as completed collection.

The direct-drain comparison then showed how removal changed the film locally. It reduced the lower-wall store by 70.32%, but total film by only 1.70% relative to the undrained case; some direct removal replaced existing edge outflow. The drain controlled a small local store without controlling the whole inventory. Assessing collection therefore requires following liquid supply and transport towards the removal region, as well as checking the drain itself.

Selected windows passed local film-balance and inner-iteration checks with the bulk equations active. These passes support the ability to calculate and account for film transport over those windows. They do not establish complete separator conservation or a stationary operating state. Likewise, the longer frozen-bulk runs isolate film development under fixed forcing: growing film can conserve mass, but fixed bulk inventory cannot establish coupled stationarity, and film time is not elapsed fully coupled separator time. Even bulk-active stages of the later enhanced model omitted reciprocal film–bulk momentum coupling.

The 195 ms mesh comparison tested whether the coarse-mesh response persisted with finer resolution. Finer states had lower film inventory and drainage, and the finest completed case broke the similarity between the intermediate meshes. This established sensitivity of the developed film response to mesh and preparation. Lower supply, different release or different transport histories could contribute; the available endpoints cannot distinguish them. Each mesh retained its own bulk forcing, so the comparison is not an isolated discretisation-error estimate. The available design endpoints likewise did not establish an isolated design benefit.

<!-- Sources: master claims F10–F12, F17–F18; phase-07-2a-wall-liquid-routing/stage-04-ewf-wall-parameters/{commercial-steel,staged-finalisation,ewf-only-drain}/results.md; stage-03-shortened-reconstruction/early-ewf-startup/inlet-speed-500ms/results.md. -->

### 6.4. Sensitivity tests defined what performance comparisons must resolve

The mesh and particle tests showed why detailed solution evidence was needed alongside summary performance estimates. Similar mean velocities concealed spatial field differences, while changes within a run matched or exceeded differences between meshes. The saved-field comparisons therefore identified continuing numerical development that prevented an isolated discretisation-error estimate.

The particle test supplied a second example. Increasing the tracking allowance more than doubled the small escaped-mass estimate while most unresolved particle mass remained unresolved. Meanwhile, counting incomplete particles as separated produced efficiencies within 0.019 percentage points of the project's July estimates. The useful finding is that a near-100% efficiency can conceal material uncertainty in liquid destination. Particle-fate distributions and their sensitivity to tracking are therefore needed to interpret apparent agreement.

The measured computational savings remain specific to the compared cases (Appendix G.4). The historical efficiency comparison also has limits related to software provenance and the unrecovered tracking cap, detailed in that appendix. These limits identify what a matched follow-up comparison must control; the current evidence does not establish physical separation performance, an optimum geometry or a validated operating range.

<!-- Sources: master claims F19–F21; phase-10-single-inlet-mesh-convergence/{predivergence-mesh-sensitivity,replication1600-dpm-limit-test,replication-enthalpy-results,replication1600-tet-results}.md. -->

The resolved-outlet investigation added a verified resistance law and short conservative discharge tests (Appendix F). It did not produce a sustained full-separator operating state, but that outcome does not prove that a physical steady solution is impossible or identify one cause for all failed tests. Together, the studies provide tested components, observed sensitivities and specific requirements for assessing them as a complete separator model.

## 7. Conclusions and future work

### 7.1. Conclusions against the project objectives

The project developed and tested inlet, collection and wall-film models for investigating inlet conditions. The tests showed how the prescribed inlet distribution changed retention, and assessed the transport and removal processes needed to interpret that change. They also identified the numerical checks still required for credible performance predictions. The four original objectives were addressed to different degrees:

1. **Reproduce the existing model and establish a validated baseline.** Model settings, inlet loading and particle calculations were reconstructed, and conditional historical-output agreement was obtained. Mesh and iteration studies exposed continuing inventory, pressure and particle-fate dependence. A traceable comparison baseline was developed, but a numerically adequate and independently validated operating baseline was not established.

2. **Implement realistic two-phase inlet conditions across flow regimes.** Separate liquid and vapour regions implemented an imposed stratified inlet with liquid on the outer-wall side. Comparisons demonstrated an effect on retention and routing. The work did not extend to a validated range of annular, slug and other inlet regimes; the implemented distribution remains a prescribed approximation.

3. **Assess inlet effects on internal flow, pressure and separation across operating conditions.** Loading, enthalpy and inlet-representation studies produced field, pressure, inventory and outlet comparisons. Wall-film modelling added explicit transport and removal routes, with useful local accounting passes. Continuing numerical development and unresolved particle fates prevented these observations from establishing physical separation-efficiency or pressure-loss predictions.

4. **Identify influential parameters and inform optimisation.** The studies identified sensitivity to startup, solver treatment, collection strength, wall treatment, outlet resistance and tracking horizon. Controlled drainage and analytical resistance tests verified useful components. The evidence informs further model development, but does not establish a universal parameter ranking or an optimum separator design.

The central finding is that changing where liquid enters and providing a local removal route are only parts of the collection problem. The tests demonstrated inlet sensitivity, improved startup, correctly applied sources, locally conservative film transport and functional drainage, while revealing continued storage and unresolved liquid destinations. This provides an evidence-based route for further model development. A stationary, fully accounted, mesh-independent and physically validated separator solution remains to be established before these capabilities can support performance optimisation.

### 7.2. Priorities for future work

The next stage should build on the developed film cases to determine whether sustained drainage can eventually balance supply without continued storage. This requires a complete liquid mass balance. Bulk, particle and film inventories must use compatible transfer definitions, counting each internal transfer once and identifying all external removal. Extend selected meshes beyond the available 195 ms snapshots while recording film supply, release, storage and drainage histories, to test whether the differing responses approach one another. Assess bulk-active extensions separately. Establish whether removal approaches inflow without inventory drift, then test sensitivity to reciprocal film–bulk momentum coupling. If physical transient behaviour is required, all stores must evolve on a compatible physical clock; frozen-bulk film time cannot supply that evidence.

If resolved brine drainage is pursued, use the verified resistance component with independently constrained downstream head and compatible hydrostatic initialisation. Appendix F identifies the remaining startup and operating-state limits; a pressure adjustment alone is not an established remedy.

Particle work should locate incomplete trajectories, separate inlet escape from steam-outlet escape, and test tracking sensitivity before assigning physical fates. Mesh-cost comparisons also require matched parcel workloads and tracking settings.

Further mesh and runtime comparisons should use matched domains and workloads (Appendix G.4). Once a sufficiently settled, conservative reference exists, repeat matched mesh and applicable timestep comparisons using pressure, routing and field quantities. Neither mesh study established mesh independence, so this remains a required numerical verification step.

Physical validation should compare compatible measurements of carryover, brine discharge and pressure loss, with uncertainty reported for both measurements and predictions.

Once a numerically verified and physically validated reference is available, broader inlet-regime comparisons can extend beyond the imposed stratified arrangement. The following three geometry proposals can then be assessed against the original optimisation objective:

- **Vertical film blocker:** intercept circulating wall liquid before it meets the inlet steam again, limiting its return to the bulk flow.
- **Angled film ramp:** direct circulating wall liquid downward towards the lower collection region.
- **External collection channel:** collect wall liquid through an opening in the vessel shell and route it downward through an external drain, reducing its repeated circulation inside the vessel.

The blocker and ramp already have completed 150 ms basic-EWF calculations (Appendix G.3), but these remain exploratory and do not establish improved performance. After the reference model passes the checks above, repeat their assessment against the unmodified separator. The external channel remains an untested proposal. Compare the three concepts using matched inlet conditions, wall and film settings, comparable mesh resolution and preparation, and sufficient development time. Assess steam-outlet liquid carryover, collected liquid, continuing film storage and pressure loss together. A thinner local film or lower inventory alone is insufficient evidence of improved separation.

<!-- Geometry proposal sources: ../../../Poster/A1 Landscape — Geothermal Separator Poster — Working Draft.pptx, slide 1; ../../../meetings/otter/2026-09-21-separator-simulation-progress-update.md, lines 109–129; ../../../meetings/otter/2026-10-05-separator-liquid-film-and-roughness-analysis.md, 17:11–19:51 and 25:55–27:45. Completed runs and interpretation limits: ../../../experiments/phase-10-proposed-design/results.md and inlet-comparison-50ms.md. -->
