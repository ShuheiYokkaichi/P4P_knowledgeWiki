# Model setup, methods and results

## 3. Starting model and setup

The literature review identified a gap between predicting liquid capture at the wall and predicting sustained collection (Section 2.7). To address that gap, this study extended the inherited Purnanto-based model, using its geometry and bulk-flow formulation as a starting point. The missing brine outlet and lack of a separate wall-film model were the main areas for development.

Section 3 defines the geometry, bulk-flow model, operating conditions and approach to comparisons. Section 4 describes the model development; Appendix A gives detailed settings.

### 3.1. Geometry and model scope

Based on Purnanto et al. (2013), the inherited geometry retained the spiral inlet, cylindrical separation vessel and internal steam outlet pipe needed to study liquid transport through the active separation region (Figure 7). In this simplified domain, the lower brine pool and its outlet pipe were excluded, leaving a closed bottom wall.

![Computational domain and split inlet](../figures/model-domain-overview.png)

*Figure 7. Simplified computational domain and inlet arrangement: (a) spiral inlet, vessel and internal steam outlet; (b) wall-side liquid strip and adjacent vapour inlet. The brine pool and discharge pipe are omitted. Panel (b) shows the split inlet introduced in Section 4.1; the absorber is introduced in Section 4.3.*

The split inlet shown in Figure 7(b), like the absorber, was introduced during development rather than inherited from the original mixed-feed arrangement. The closed base provided no physical liquid outlet. In the later liquid-removal studies, the absorber removed liquid from a defined lower region while the base kept steam on its intended path (Section 4.3).

### 3.2. Bulk-flow model and assumptions

The Mixture model carried forward Purnanto's modelling approach. Its algebraic-slip formulation followed that study's small-Stokes-number argument: sufficiently small dispersed droplets respond rapidly relative to the characteristic flow timescale ([Purnanto et al., 2013](https://www.researchgate.net/publication/269519626_CFD_MODELLING_OF_TWO-PHASE_FLOW_INSIDE_GEOTHERMAL_STEAM-WATER_SEPARATORS)). Initial volume of fluid (VOF) and turbulence trials did not establish Mixture with RNG $k$–$\varepsilon$ as the most accurate formulation. It was retained because solving mixture momentum with algebraic slip requires fewer equations than a full Eulerian formulation, making repeated inlet and wall-treatment studies practical ([Ansys, Inc., 2025d](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_th/flu_th_sec_drift_oview.html)).

<!-- Basis: recorded baseline rationale; executed VOF trial; turbulence screening. The small-Stokes-number rationale concerns dispersed liquid; applicability to concentrated wall liquid remains unverified. -->

A pressure-based solver with the Mixture model in Ansys Fluent 2025 R2 was used for bulk continuity, momentum, liquid fraction and algebraic slip, with steam as the primary phase and water as the secondary phase. The inherited setup carried forward Purnanto's SIMPLE pressure–velocity scheme, while Appendix A.1 identifies comparison cases that used the Coupled pressure–velocity scheme. Turbulence was represented by the RNG $k$–$\varepsilon$ model with swirl treatment and standard wall functions, and gravity acted downwards. With the energy equation disabled, flashing, condensation and temperature-dependent properties were excluded. Table 1 gives the material values, while Appendix A.1 records the controls ([Ansys, Inc., 2025d](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_th/flu_th_sec_multiphase_mixture.html)).

*Table 1. Fixed material properties used in the throughput-controlled absorber model.*

| Phase | Density (kg/m³) | Dynamic viscosity (Pa·s) |
| --- | ---: | ---: |
| Vapour | 5.79743 | $1.52062\times10^{-5}$ |
| Liquid water | 881.211 | $1.45544\times10^{-4}$ |

The bulk-flow formulation used Manninen slip, Schiller–Naumann drag and a liquid-phase diameter of 10 µm (Appendix A.1).

### 3.3. Inlet and boundary conditions

The model comparisons used Purnanto's reference feed condition: 197.61 kg/s at 1600 kJ/kg and 11.2 bar absolute. At this pressure, saturated liquid and vapour enthalpies, $h_f$ and $h_g$, gave the vapour mass fraction as $x=(h-h_f)/(h_g-h_f)=0.408323$. The inlet boundary conditions used Purnanto's rounded phase mass-flow rates of 116.92 kg/s liquid and 80.69 kg/s vapour; Appendix A.2 gives the calculation ([Purnanto et al., 2013](https://www.researchgate.net/publication/269519626_CFD_MODELLING_OF_TWO-PHASE_FLOW_INSIDE_GEOTHERMAL_STEAM-WATER_SEPARATORS)). Flashing was not solved within the domain. Enthalpy was therefore used to set the inlet steam–water composition for the model-development comparisons.

Stationary, no-slip walls confined the flow, and the steam outlet supplied the pressure boundary condition, so inlet pressure was calculated by the solver. With the operating pressure set to 0 Pa, outlet gauge and absolute pressures were equal. The reference feed condition defines full feed in the following sections; reduced-feed holds and ramps changed the inlet flow during startup, while the inlet comparison changed where the phases entered. Appendix A.1 gives the turbulence and backflow inputs and the differences between comparison setups.

### 3.4. Study plan and comparisons

The investigation progressed from liquid distribution and removal to wall-film transport, mesh sensitivity and proposed designs. The 60k poly-hexcore mesh supported repeated model development, followed by tests on finer meshes; the historical tetrahedral case provided context. Comparisons used shared starting fields and comparison intervals where possible, with preparation differences identified separately. Table A1a in Appendix A.1 summarises the meshes, settings and comparison limits.

Scaled continuity residuals, liquid inventories, removal rates and contours were assessed together to interpret each test. In the following sections, outlet liquid flow means the liquid mass-flow rate through the steam outlet and is positive outwards unless stated otherwise. Bulk-flow development is reported in solver iterations; film development is reported in accepted film time, the simulated time advanced by the film solver.

## 4. Model development and results

The results address the four research questions through inlet and mesh comparisons, numerical improvements, wall-liquid transport studies and initial design tests. Table A1a summarises the comparisons.

### 4.1. Split inlet and liquid distribution

The split inlet was introduced to represent the expected wall-side concentration of liquid as the upstream flow turned into the real separator. Using the geometry in Section 3.1 (Figure 7), the 0.724 m × 0.724 m inlet cross-section was divided into a 6.754 mm wall-side liquid strip and the remaining steam inlet. The reference feed defined in Section 3.3 supplied approximately 116.9 kg/s of liquid and 80.7 kg/s of steam through the liquid and steam inlet faces, respectively. Complete phase separation at entry was an idealisation of this expected distribution; Appendix A.2 explains how the strip width was chosen. With this physical intent represented in the inlet, the investigation then examined how the change affected liquid behaviour within the vessel.

Matched cases compared mixed and split inlets under the controls in Table A1a. Although boundary mass-flow rates changed little relative to mixed feed, with almost all incoming liquid still leaving through the steam outlet, the contours showed a clearer spatial difference. The split-inlet case has a more continuous liquid-rich band around the outer wall in Figure 8(b), while the vertical section in Figure 8(d) shows liquid concentrated beside the wall and in a deeper region near the base. The central bulk flow retains a low liquid volume fraction.

![Bulk-liquid fraction at inlet height and through the vessel height with mixed and wall-side split feed](../figures/results-inlet-spatial-comparison.png)

*Figure 8. Liquid volume fraction with mixed (a, c) and split inlets (b, d), at inlet height (a, b) and through the vessel centre (c, d).*

The closed base still had no liquid outlet, as expected from the simplified geometry. The contribution of the split inlet was to represent the intended wall-side liquid entry and show how it changed the liquid distribution inside the separator. The clearer wall band and deeper base accumulation gave a spatial basis for examining liquid retention on different meshes.

<!-- Rationale: 22 April spiral-inlet discussion, 03:41–04:39; 11 March initial two-phase inlet proposal, 02:08. Meeting records establish design intent, not measured inlet phase distributions. Evidence: matched inlet setup and numerical basis, mixed-feed results, split-feed spatial findings, and native inlet-plane exports. -->

### 4.2. Liquid accumulation on different meshes

The mesh investigation moved from the historical tetrahedral mesh to poly-hexcore meshes to improve the representation of swirling flow and liquid transport near the wall. The comparisons examined how this change affected liquid distribution and retention.

Poly-hexcore concentrated resolution near the wall through wall-following prism layers, connected by polyhedral cells to larger hexahedral cells in the core. This allowed small wall-normal spacing without requiring the same resolution throughout the vessel ([Ansys, Inc., 2020, pp. 1–2](https://www.ansys.com/content/dam/resource-center/white-paper/ansys-fluent-mosaic-technology-wp.pdf)).

Figure 9 compares mesh sections and liquid fields from the historical tetrahedral case and a 60k poly-hexcore case at iteration 10,000. The historical case shows a thin liquid-rich region near the wall. The poly-hexcore case shows a wider region with a higher liquid fraction, revealing a clear difference in wall-liquid retention.

![Mesh sections and liquid-fraction fields for the tetrahedral and poly-hexcore cases](../figures/results-mesh-spatial-comparison.png)

*Figure 9. Historical tetrahedral and poly-hexcore mesh sections (a–b) and liquid-volume-fraction fields (c–d).*

Separate split-inlet cases on the 342k, 680k and 997k meshes showed how retained liquid developed during calculation. Liquid accumulated near the wall and base, and its inventory continued to rise while little escaped through the steam outlet (Figure 10). With no separate liquid exit at the closed base, these cases retained liquid instead of reaching a steady inventory.

![Liquid inventory and outlet flow across the three finer absorber-free meshes](../../../experiments/phase-08-storyline-reconstruction/stage-02-fine-mesh-simple/direct-student-342k/n3000/figures/matched-mesh-checkpoints.png)

*Figure 10. Liquid inventory (left) and outlet liquid flow (right) on the 342k, 680k and 997k meshes.*

Continued calculation on the 680k mesh produced further accumulation before numerical divergence stopped the run, whereas the historical tetrahedral case had continued much further. Seen alongside the wider wall-liquid region in Figure 9, this contrast raised the possibility that the poly-hexcore meshes retained liquid that the earlier mesh had spread into the bulk flow.

Fluent's guidance links reduced numerical spreading to cell refinement and alignment with the flow. Wall-following layers do not automatically align with the spiralling liquid path, and tetrahedral meshes can also contain prism layers; cell spacing and orientation therefore matter more than the mesh label alone ([Ansys, Inc., 2025c, §7.1.3.3](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_ug/flu_ug_GridTypes.html)). Core resolution also matters because swirl and pressure gradients drive the surrounding flow ([Ansys, Inc., 2025l, §§10.3.2–10.3.3](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_ug/flu_ug_uns_sec_models_swirl.html)).

The comparisons do not isolate mesh construction from all other differences, so reduced spreading remains a possible explanation. What they did reveal was sustained wall and base accumulation that the earlier calculation had not shown as clearly. This gave a clearer view of where liquid remained within the separator and a basis for studying its removal in Section 4.3.

<!-- Development rationale: 17 August discussion of wall layers and coarse-mesh experimentation. That discussion concerns earlier full-geometry work, not a measured speed or accuracy comparison for the final simplified mesh. -->

<!-- Evidence: native mesh and liquid-field comparison, source pairs and export manifests; solved 60k topology and wall-resolution evidence in Appendix A.6. The separate 342k mesh illustration used elsewhere is not substituted for the 60k contour's mesh here. -->

### 4.3. Adding liquid removal

The next development added a destination for liquid retained near the base. Earlier trials included the lower geometry to model the brine pool and its outlet directly. Across the two sets of steady outlet tests, only six of 16 cases reached 500 iterations, and completed cases retained large liquid mass-balance errors (Appendix A.7). These difficulties led to a simpler test: provide liquid removal while studying transport separately from pool behaviour and discharge control.

The absorber removed liquid reaching the lower region, while the closed bottom diverted steam towards its outlet. The rigid, no-slip bottom remained an approximation to the real steam–brine interface, and pool motion and control of liquid outflow were not modelled. This arrangement supplied a liquid destination near the base while preserving the steam's turn towards its outlet, allowing liquid transport towards the removal region to be tested.

<!-- Modelling rationale: Phase 7A interpretation. -->

The absorber removed liquid through a mass sink in a defined cell region near the base. Its first form targeted the incoming liquid throughput and was used for the startup in Section 4.4. The selected contact-based absorber instead made removal depend on liquid reaching the absorber, using local liquid content and a specified depletion time:

$$
S_L=-\frac{\rho_L\alpha_L}{\tau},\qquad \tau=10^{-5}\ \mathrm{s}.
\tag{3}
$$

Here, $\rho_L$ is liquid density, $\alpha_L$ is liquid volume fraction and $\tau$ is the depletion time; $S_L$ is the mass sink per unit volume, in kg/(m³·s). The depletion time set the rate of liquid removal, and tests of removal strength guided its selection. Associated momentum and turbulence sources represented liquid removal without a direct steam mass sink. Appendix A.3 gives the source laws, mass-balance checks and depletion-time test results ([Ansys, Inc., 2025a](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_ug/flu_ug_bcs_sec_cell_zones.html)).

<!-- Evidence: matched finer-mesh checkpoints, 997k spatial result, 680k accumulation and failed continuation, mixed-inlet Coupled account and full-geometry scope decision. -->

### 4.4. Starting at reduced feed

The inlet was held at 25% of the reference feed with liquid removal active, allowing the continuity residual to fall before more model features were added. This earlier startup used the 60k mesh, Hybrid Initialisation, smooth walls and no wall-film model, together with a throughput-controlled absorber. In this absorber, total removal targeted the inlet liquid mass flow and was distributed according to liquid content in the absorber region. Table 2 gives the reduced and full-feed boundary conditions.

*Table 2. Main boundary conditions. Reduced feed was 25% of full feed, with the phase mass ratio retained.*

| Boundary | Condition | Full feed | Reduced feed |
| --- | --- | ---: | ---: |
| Liquid inlet | Liquid mass-flow inlet | 116.9200 kg/s | 29.2300 kg/s |
| Vapour inlet | Vapour mass-flow inlet | 80.6900 kg/s | 20.1725 kg/s |
| Steam outlet | Gauge pressure | 1.120 MPa | Same |
| Vessel and bottom | Stationary, no-slip walls | Selected roughness/film treatment | As defined for startup |

The reduced-feed hold produced a more stable liquid inventory. The estimated inventory fall was only 0.30% between iterations 1080 and 1580, with about 31 kg remaining at the end of the hold. This was approximately 93% below the 454 kg stored in the absorber-free 342k reference, whose inventory was still rising. The two cases differed in mesh and loading, so this contrast reflects the combined changes in removal, feed and mesh (Appendix A.3).

The scaled continuity residual also fell, reaching a minimum of $3.2\times10^{-4}$ (Figure 11), about 650 times lower than the approximately 0.21 at the absorber-free 342k comparison point (Appendix A.3). The lower reported residual and small inventory change together supported gradually returning to full feed. Each loading stage started from the flow field reached in the previous stage. This gradual increase is consistent with Fluent guidance for improving solution stability in swirling flows ([Ansys, Inc., 2025l](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_ug/flu_ug_uns_sec_models_swirl.html)).

![Residuals, bulk-liquid inventory and actual inlet loading during early development](../figures/results-described-early-development.png)

*Figure 11. Residuals, liquid inventory and inlet loading during the reduced-feed hold, ramp and subsequent development.*

Figure 11 shows the continuity residual rising during the ramp, then falling to about $2.8\times10^{-3}$ during full-feed development with Coupled pressure–velocity scheme and Global Time Step pseudo-time. Markers A, B and C identify the ramp start, full feed with Coupled activation, and wall-film activation, respectively; the horizontal axis records solver iterations, not physical time.

Residual oscillations and an unresolved liquid mass balance remained, so the full-feed state was not treated as converged. Nevertheless, the startup showed substantially improved numerical behaviour: the continuity residual decreased markedly, inventory changed little late in the reduced-feed hold, and the calculation reached full feed. These improvements justified saving the smooth-wall, film-disabled state at iteration 5586 as the common baseline for the wall-treatment comparisons.

<!-- Evidence: absorber-free 342k continuity reference, selected case history, Appendix A.1, carrier residuals and liquid histories. Residual ratio: 0.20837 / 0.00032056 = approximately 650. Inventory comparison: (453.612255 - 31.3571) / 453.612255 = approximately 93.1% lower; the hold inventory fell 0.30% over iterations 1080–1580. These are separate run states, not a measured depletion of the absorber-free inventory. This compares an absorber-free endpoint with a reduced-feed hold minimum across different meshes and loading; it is not an isolated absorber-effect measurement or a mass-balance-error ratio. -->

### 4.5. Liquid remaining near the upper wall

The absorber provided a lower liquid-removal route, but substantial liquid still reached the steam outlet at full feed. Figure 12 illustrates the concern in an earlier absorber trial: liquid-rich bands extend up the outer walls to the upper shoulders, with smaller liquid-rich regions near the internal outlet entrance.

![Liquid-volume-fraction contour and velocity vectors from an earlier absorber trial, with liquid-rich bands along the upper outer walls](../../../meetings/2026-09-14/figures/P07A-02-absorber-active1900-XY-VOF-velocity.png)

*Figure 12. Liquid volume fraction and velocity vectors in an earlier absorber trial.*

Providing a sink addressed local removal, but effective collection also required liquid transport towards that region. The upper-wall liquid suggested that gravity and wall friction were not strong enough to redirect it downwards. Although the contours alone did not establish the force balance, they motivated the roughness and wall-film studies in Sections 4.6.1 and 4.6.2, which examined whether changing the wall treatment could help liquid reach the absorber.

<!-- Spatial evidence: original meeting image retained in place; its filename and embedded scene label identify an earlier Phase 7A absorber-active1900 view. It is not the N5586 full-feed parent and is used only as historical qualitative evidence of upper-wall liquid. The exact pair linkage for this older combined contour/vector export has not been independently verified. Related Phase 7A source-state records. The original image has clipped legend text but readable 0–1 ticks; no pixels were altered. -->
<!-- Narrative evidence: 21 September meeting, 00:37–05:05, particularly the observations of liquid above the inlet, upward spiralling and upper-region accumulation. The transcript does not establish that this retained image was the exact contour displayed in that meeting. -->
<!-- Baseline evidence: full-feed control continuation, baseline handoff and full-feed control accounting audit. Figure 12 is inserted without changing existing figure numbers or cross-references. -->

### 4.6. Wall–liquid interaction

Two separate tests from the common baseline examined the wall-liquid problem: one varied roughness to test whether changing wall friction altered the liquid path, while the other introduced EWF to represent liquid as a film with its own storage and transport. To separate these treatments before examining combined cases, the roughness tests kept EWF disabled and the film tests retained smooth walls.

Each test restarted independently from iteration 5586 and ran for 3000 updates. Means were calculated over the final 500 updates, keeping the starting field and comparison interval the same (Section 3.4). Inventory was assessed alongside outlet flow to distinguish changed routing from depletion of stored liquid.

#### 4.6.1. Wall roughness

Wall roughness was included in the wall-friction treatment through the equivalent sand-grain height $k_s$ and roughness constant $C_s$ ([Ansys, Inc., 2025k](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_th/x1-5720008.164.html)). The sensitivity tests examined how these parameters changed liquid flow through the steam outlet, the primary quantity used here to investigate carryover. Appendix A.6 records the wall treatment.

Roughness ranged from 0 to 8 mm, with detailed comparison controls in Appendix A.1.

<!-- Motivation: early outlet-flow record; roughness hypothesis; film hypothesis; 5 October wall-liquid discussion. -->

Changing wall roughness produced large changes in mean bulk-liquid flow through the steam outlet (Figure 13). At $C_s=0.5$, a roughness height of 0.05 mm raised mean outlet flow by about 21% relative to the smooth-wall reference, whereas 8 mm reduced it by about 44%. Increasing $C_s$ lowered the flow at both fixed roughness heights. Dashed lines mark the smooth-wall reference.

![Effect of roughness height and constant on bulk-liquid steam-outlet flow](../figures/results-described-roughness.png)

*Figure 13. Mean outlet liquid flow versus (a) roughness height and (b) roughness constant.*

<!-- Evidence for the material-reference continuation: Commercial-steel results. The 0.045 mm value is a selected reference, not a measured separator finish or a matched roughness-only comparison. -->

<!-- Evidence: roughness-screen results and sample standard deviations and comparison figure and provenance. The source's later statement identifying the lowest outlet conflicts with its table; the table values are used here. -->

The 8 mm case also reduced stored liquid mass substantially, showing that wall friction affected both storage and outlet flow. Because increased roughness could raise or lower outlet flow, its selected value needed a physical basis. A commercial-steel reference, $k_s=0.045$ mm and $C_s=0.5$, was selected to represent the intended wall material, with the bottom kept smooth (Appendix A.1).

#### 4.6.2. Adding wall-film modelling

Changing wall friction did not explicitly represent liquid stored on the wall. The second test therefore returned to the smooth-wall baseline and introduced the Eulerian Wall Film (EWF) model. It solved surface mass and momentum equations, with accretion transferring bulk liquid into the film ([Ansys, Inc., 2025e](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_ug/flu_ug_ewf_sec_options.html)).

With common smooth-wall starting fields and throughput-controlled liquid removal, EWF with accretion reduced mean bulk-liquid outlet flow by about 93%, from 24.4 to 1.74 kg/s over the matched reporting window (Figure 14). Film mass and momentum were solved together at a 10 µs step. The shaded region marks the final 500 iterations used for comparison.

![Bulk-liquid steam-outlet flow with EWF disabled and with EWF and accretion enabled](../figures/results-described-film-outlet.png){width=78.4%}

*Figure 14. Outlet liquid flow with EWF disabled and accretion enabled.*

During the accretion-enabled continuation, bulk liquid mass fell from about 296 to 63 kg, while film mass reached about 3 kg. The marked reduction in steam-outlet liquid flow showed how strongly wall-film transfer affected predicted carryover. With liquid now entering a separate film, longer calculations were needed to establish where it went: spreading along the wall, remaining stored or draining.

<!-- Evidence: film-disabled and accretion-enabled comparison, wall-film-screen results and native sections, paired contour provenance and selected endpoint histories. The film-disabled continuation's mean is from its separate comparison run and is not substituted for the roughness screen's smooth-wall mean. -->

Combining roughness, film transport and the contact-based absorber still left drainage about 10% below accretion over the final window (Appendix A.1). This continued storage motivated longer film studies; first, the lengthy startup was revised to introduce these treatments earlier.

<!-- Evidence: contact-strength screens, complete selected case history and corrected film ledger. The short strength-screen branch is distinct from the original-field continuation identified in Appendix A.1. -->

### 4.7. Shorter startup with wall-film modelling

Before extending film development, the long startup procedure was revised to introduce the combined treatments earlier and reach full feed with smaller loading disturbances. The shortened procedure reused the reduced-feed field without reinitialisation, then activated the contact-based absorber, roughness, the Coupled scheme and an initially dry film before increasing the feed.

The original and shortened startup sequences were compared as complete procedures (Section 3.4 and Appendix A.1).

The shortened startup substantially reduced disturbances during the loading ramp. The continuity normalisation was identical for both startup ramps (Appendix A.3). Within the ramp window, the peak continuity residual fell by 70.15%, peak combined bulk and film inventory by 70.43%, and peak outward liquid flow through the steam outlet by 75.78% relative to the historical ramp (Figure 15).

![Historical and shortened startup at matched inlet-ramp progress](../figures/results-described-startup.png)

*Figure 15. Historical and shortened startup: (a) continuity residual, (b) liquid inventory and (c) outlet liquid flow.*

Switching on the added treatments during the activation hold produced a continuity residual peak of 0.10593, higher than the historical ramp peak. This hold is excluded from Figure 15. The film solution did not meet the thickness and momentum tolerance in 15 of the final 100 hold updates, but met it throughout the following ramp (Appendix A.4). The shortened procedure thus separated the difficult activation step from the feed increase, producing a smoother loading ramp.

The check of the contact-based absorber also confirmed that removal followed the specified law (Appendix A.3). By activating the treatments before increasing feed, the revised procedure produced a smoother transition to full loading, with lower peaks in residual, liquid inventory and carryover during the ramp. This improved startup supplied the full-feed starting field for the longer film studies.

<!-- Evidence: shortened-startup results, audited metrics, native source checks and normalisation and native final histories for Appendix A.3. -->

### 4.8. Film growth and drainage

The initial film produced during startup was advanced to 500 ms to examine whether it would spread and develop sustained drainage. The surrounding bulk flow field was held fixed so that its effect on the film remained unchanged. This bulk field had not converged beforehand. Drainage here means Fluent’s reported liquid outflow across the film-domain edges, excluding the bulk absorber and the direct film drain introduced in Section 4.9 (Appendix A.5).

Drainage rose rapidly during early development and then began to level out (Figure 16), but remained below film input (accretion) as inventory continued to rise through 500 ms. Over the final reporting window, drainage was still approximately 14% below input. The film mass-balance check supported this accumulation: over 490–500 ms, input minus drainage agreed with the measured storage rate to within 0.008% of input (Appendix A.5). The nearly level drainage curve therefore hid continued storage, which the mass balance and inventory history revealed together.

![Film inventory, accretion and drainage against accepted film time through 500 ms](../figures/results-film-development-reference500ms.png)

*Figure 16. Film inventory, input and drainage through 500 ms.*

The contour plots show film development across the vessel wall (Figure 17). Spreading and thickening in the lower and middle wall regions show that film growth involved both increasing surface coverage and increasing local storage.

![Wall-film thickness at three stages of development](../figures/wall-film-described-development.png)

*Figure 17. Wall-film thickness during development with the bulk flow held fixed.*

Small film timesteps made these calculations costly. In a matched 2.5 ms test, 20 µs passed the local checks, while 25 µs exceeded the 0.1% film mass-balance error limit despite similar film fields. The mass-balance check therefore determined which timestep passed the test; longer runs still required checks on stability and mass balance as the film developed (Appendix A.4).

Together, the histories and contours showed how liquid spread, built up and drained along the wall. Tracking film mass alongside outflow revealed continued storage even after drainage began to level out. This linked film development to the balance between supply and removal, directing the next tests towards release and direct drainage.

<!-- The computational-cost and optimisation experience is described from the author's report revision direction; no measured runtime or speed-up is claimed. -->
<!-- Evidence: selected film-development results, spatial metrics and reporting windows, 500 ms campaign results, selected reference-speed CSV and Figure 16 provenance. -->

### 4.9. Film release and lower-wall drainage

Film liquid continued to accumulate, so two ways to reduce it were tested. First, stripping and edge separation allowed liquid to leave the film as droplets ([Ansys, Inc., 2025b](https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/flu_th/flu_th_ewf_sec_film_submodels.html)). Film mass still increased (Appendix A.5). The next test added a drain at the lower wall.

Because the bulk absorber could not remove film liquid, the film domain was extended onto the lower wall and a separate mass and momentum sink was added as a direct film drain. Matched Drain OFF/ON cases used identical starting fields, the same film domain and bulk flow held fixed. Over 15 ms, the drain reduced lower-wall inventory by about 70% (Figure 18). Net extra external removal was 0.1897 kg, closely matching the reduction in total film inventory and confirming the added liquid removal over this interval (Appendix A.5).

![Matched lower-wall film inventories and cumulative external removal with the direct drain off and on](../figures/results-direct-film-drain.png)

*Figure 18. Drain OFF/ON comparison: (a) lower-wall film mass and (b) external liquid removal.*

During longer development, lower-wall film inventory remained low while upper-film inventory continued to grow. The later Courant-limit failure means that the end of the run cannot be treated as a reliable endpoint (Appendix A.5). Upper-wall accumulation was already present before that failure. The inventory trends show that the remaining storage problem was above the drain: removal controlled the lower region while liquid continued to accumulate higher on the wall.

The drain removed liquid that reached the lower wall. The remaining task was to understand how liquid reached it from higher in the vessel. This result separated the two parts of collection—transport to the drain and removal at the drain—and gave the next mesh comparison a clear focus.

<!-- Evidence: release-mechanism continuation, matched direct-drain test and long drain-ON development. -->

### 4.10. Numerical checks and mesh sensitivity

The coarse mesh provided a practical basis for developing film transport and drainage. The next question was whether its predicted film coverage, storage and drainage remained similar on finer meshes. Four meshes (60k, 342k, 680k and 997k) were compared at a common film time of 195 ms. Earlier coarse-mesh drainage had begun to level out around 200 ms (Figure 16), providing a practical observation point for comparing film paths, storage and removal across meshes.

Each film evolved with the bulk flow for its mesh held fixed and the selected steel roughness applied. The prepared bulk flows and starting film states differed between meshes (Appendix A.6), so the films began under different conditions. The comparison examined how each prepared flow supported film spreading, storage and drainage.

Figure 19 unfolds the cylindrical wall, with height vertically and angle around the vessel horizontally. The white opening marks the inlet. All panels use a 0–0.30 mm thickness scale, with higher values clipped; purple indicates low thickness, not necessarily a dry wall. Arrows show direction rather than speed.

![Wall-film thickness at the selected starting states and at 195 ms for four mesh resolutions](../../../experiments/phase-09-mesh-convergence/figures/selected-film-thickness.png)

*Figure 19. Wall-film thickness before development (top) and at 195 ms (bottom).*

At 195 ms, relatively thick film covers much of the displayed wall on the 60k mesh. The finer meshes show more distinct liquid paths and thinner upper-wall regions. The 342k and 680k patterns are similar, while the 997k case has less clearly visible film above the inlet. These paths show where liquid travels along the wall, making their position and development relevant to drainage.

The inventory and drainage results support this spatial contrast (Figure 20). The finer meshes contain less film and have lower drain rates than the 60k case. Although 342k and 680k give similar film inventories and drainage, the 997k case contains about 30% less film and drains about 32% less than 680k. The finest completed mesh breaks the apparent agreement between the intermediate meshes, so mesh independence has not been established. The fall in both film mass and drainage on the finest mesh links the changed removal rate to a different wall-liquid inventory.

![Bulk-liquid outflow, bulk inventory, film inventory and lower-wall drain rate across mesh resolutions](../../../experiments/phase-09-mesh-convergence/figures/selected-mesh-response.png)

*Figure 20. Bulk-liquid quantities, film inventory and lower-wall drain rate across meshes.*

Because the same removal law was used on each mesh, the lower rates could be traced directly to less film in the lower-wall removal region. The useful comparison was therefore how each prepared flow supplied that region. The 2.6M case in Figure 20 provides an initial bulk-flow reference.

Bulk pressure differences varied less across these cases. The calculated area-averaged inlet-to-outlet static pressure difference was 11.0–11.3 kPa, a spread of about 3% of the mean. This falls within Pointon et al.'s roughly 10–40 kPa range of typical predicted losses. Their example design specified 19 kPa at 11.7 bar and 1875 t/h, compared with the present 11.2 bar and about 711 t/h, so it provides context at different operating conditions ([Pointon et al., 2009, pp. 944–945](https://publications.mygeoenergynow.org/grc/1028587.pdf)).

Using the outlet steam-quality definition in Section 2.2, the bulk vapour and liquid mass-flow rates at the comparison points give an outlet steam quality of 99.32–99.42%, compared with Pointon's design outlet steam quality of 99.87%. Appendix A.6 records the calculation. The corresponding liquid fractions, 0.58–0.68% here and 0.13% in that design, show how similar steam-quality percentages can hide differences in liquid carryover.

Rizaldy et al. also found evidence of brine carryover at Wairakei and proposed wall-film entrainment as a contributor, giving the film-transport question practical relevance ([Rizaldy et al., 2016, Sections 3–4](https://www.researchgate.net/publication/310818568_LIQUID_CARRYOVER_IN_GEOTHERMAL_STEAM-WATER_SEPARATORS)).

Similar bulk pressure differences occurred alongside clear changes in film coverage, storage and drainage. Differences in starting fields limit what can be assigned to mesh resolution alone (Appendix A.6). The comparison showed why mesh assessment must also follow the wall-liquid paths: the amount reaching the drain depends on where the film develops and how it moves.

<!-- Evidence: selected-state results and history availability, endpoint CSV, history audit, film-map provenance, and endpoint-figure provenance. Percentages use unrounded endpoint values. The author supplied the observation-time rationale on 17 October 2026. -->

### 4.11. Initial design tests

The fourth research question asks how CFD can inform separator design optimisation. The earlier studies identified a specific design problem: liquid captured at the wall could remain high in the vessel instead of reaching the lower removal region. Since providing removal at the base did not resolve that transport problem, the design focus shifted towards guiding wall liquid after capture, rather than treating capture alone as successful separation.

Two features were proposed to address this transport problem: a vertical blocker to interrupt the recirculation of wall liquid before it meets the incoming steam again, and an angled ramp to guide liquid downwards towards the removal region.

The 154k blocker and 213k ramp cases reached 150 ms of EWF development; Appendix A.8 gives the setup details. Figure 21 presents the associated local mixture-velocity vectors at 50 ms.

The blocker interrupts the local vector pattern, while flow beside the ramp follows its inclined edge. These local flow changes agree with the intended roles of the features: interrupting circulation and guiding liquid downwards.

| (a) Vertical film blocker | (b) Angled film ramp |
| --- | --- |
| ![Vertical blocker with local mixture-velocity vectors](../../../experiments/phase-10-proposed-design/figures/manual-vertical-blocker-basic-50ms.png){height=40mm} | ![Angled ramp with local mixture-velocity vectors](../../../experiments/phase-10-proposed-design/figures/manual-angled-ramp-50ms.png){height=40mm} |

*Figure 21. Preliminary mixture-velocity vectors around (a) the vertical film blocker and (b) the angled film ramp.*

The EWF calculations were too short to show whether these local flow changes increase or reduce separation efficiency. Longer film calculations are needed to assess how each feature changes wall-liquid storage, collection and carryover. These initial tests gave a clear direction for further design work: use a blocker to interrupt circulation or a ramp to guide liquid towards removal.

### 4.12. Workflow and automation

The preceding investigations required repeated setup changes, long calculations and comparisons between saved states. Automation connected these tasks within a reusable workflow (Figure 22), with OpenAI Codex helping to prepare cases, run Fluent and analyse results. Its main benefits were preserving previous work, carrying out repeated tasks and checking results.

The programme included 387 configurations run across both project partners, including failed and partial trials. This programme depended on being able to reuse earlier cases and findings as each investigation developed.

![Experiment workflow linking research questions, previous findings, model setup, Fluent calculations, analysis and subsequent decisions.](../../../../assets/readme/experiment-workflow.png)

*Figure 22. Experiment workflow linking research questions, execution, evidence and subsequent decisions.*

A connected knowledge base and experiment records preserved each test's purpose, assumptions, settings and results. Saved cases and checked procedures gave later tests a starting point, while checkpoints preserved work for recovery after a failure.

Task instructions defined the objectives, allowed changes and stopping conditions. The Model Context Protocol (MCP) connection linked the agent to persistent Fluent sessions through PyFluent, allowing it to inspect settings and issue commands. Scheduled monitoring supported progress checks and recovery during long runs while the host and solver remained available. The workflows and Fluent integration are available in the [project GitHub repository](https://github.com/Shuhei-uni/P4P_knowledgeWiki).

Checks of Fluent settings, solver logs and saved flow fields allowed the model setup and results to be reviewed. For example, the timestep test in Section 4.8 rejected the 25 µs candidate because of its mass-balance error, despite similar film fields. The mass-balance check tied that decision to numerical evidence.

Scientific judgement remained central to defining the research questions and interpreting the results. Experience gained with Fluent and CFD showed that some investigations added little to understanding the liquid path. Selecting useful tests therefore remained a research decision; automation made it practical to carry them out, preserve the evidence and build on the results.

<!-- Diagram reproduced unchanged from the repository README. “Auto Loop” and “Result.md” are older labels for the current phase-loop workflow and results.md records; the implementation evolved during the project. -->

<!-- Scale-count audit, 17 October 2026: all 166 exact setup.md files in the 15 Project/experiments campaign folders were read, together with linked results, historical/deferred setup records and execution evidence. Count distinct executed experimental conditions/protocols across BOTH authors. Multiple cases inside one setup count separately. Deliberately tested numerical-setting changes and standalone DPM comparisons count; failed/partial trials count if solver execution is evidenced. Exclude unchanged continuations, checkpoints, repeated identical conditions, routine implementation/seeded verification probes, pre-solve blocks, prepared-only cases, and scheduled controls never reached. Do not count every ramp step or individual particle track.
Campaign | setup.md files | distinct executed configurations
phase-01-purnanto-baseline-and-inlet-exploration | 7 | 22
phase-02-parity-reset-and-pre-v2-qualification | 5 | 15
phase-03-dpm-carryover-and-coupling | 5 | 28 (includes 12 Andy historical cases)
phase-04-ewf-wall-film-mechanisms | 7 | 7
phase-05-full-geometry-v2 | 8 | 52
phase-06-full-geometry-with-brine-pool | 8 | 8
phase-07a-simplified-purnanto-liquid-removal | 32 | 24
phase-07b-full-geometry-liquid-removal | 12 | 12
phase-07-1a-absorber-convergence | 1 | 9
phase-07-2a-wall-liquid-routing | 41 | 98
phase-08-storyline-reconstruction | 13 | 49
phase-09-mesh-convergence | 9 | 15
phase-09-steady-vof-pool | 8 | 23
phase-10-proposed-design | 9 | 10
phase-10-single-inlet-mesh-convergence | 1 | 15
TOTAL | 166 | 387 = 358 bulk/film/numerical conditions + 29 standalone particle-tracking comparisons.
Cross-phase deduplication: 7.2A R0/E0 counted once under 7.1A; 7.2A inherited 60k N8000 baseline counted under Phase 9 mesh; historical F1 SIMPLE/F0 alias counted once; Phase 6 S1-R/F11, D04/S3-C and S6/S4-C repeats excluded; Phase 6 D01/D02 pressure cases count once despite references in missing Phase 5 Stage 5; current matched 2025 R2 tet benchmark differs from historical 2024 R2 protocol. Same-control restarts and endpoint fractional timesteps are not extra cases.
Evidence limit: this is an exact sum of identified configurations in retained records, not a proven complete all-time total. Missing Phase 5 Stage 5 Realizable/RSM/SST detail, unidentifiable early Student/anthracite tests, a poorly identified failed stripping test and uncertain corrupt G025 execution were excluded. No simultaneous-computer count or measured speed-up is claimed. Detailed read-only subagent ledgers were produced in the operating-system temporary directory, consolidated as cfd-case-audit-consolidated.md; the campaign files above and their linked results own the evidence. -->

<!-- Workflow sources: repository overview; phase-loop procedure; MCP session controls; run-control procedure. The reflection on learning CFD, peripheral work and expert judgement comes from the author's direction on 17 October 2026. No measured reduction in hallucination or task drift is claimed. -->
