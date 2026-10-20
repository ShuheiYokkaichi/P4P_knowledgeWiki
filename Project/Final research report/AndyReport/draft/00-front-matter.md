# Geothermal steam-water separator design CFD modelling and optimising

## Title page information

| Field | Information |
| --- | --- |
| Author | Andy Tran |
| Co-worker | Shuhei Yokkaichi |
| Supervisors | Sadiq Zarrouk and Maedeh Amirpour |
| Institution | The University of Auckland |
| Report | Part IV Research Project Report |
| UPI | qtra338 |
| Date | 18 October 2026 |

## Abstract

This project developed and tested an inherited computational fluid dynamics model to investigate two-phase inlet conditions in a geothermal steam–water separator. Separate liquid and vapour inlet regions made the prescribed distribution explicit. Numerical collection, staged loading and wall-film modelling extended the model to examine where liquid accumulated and how it could reach removal. These developments addressed continuing inventory and pressure changes identified during baseline mesh assessment.

On the same mesh and at matched 10,000-iteration endpoints, the imposed stratified inlet retained about 37% more liquid than the mixed inlet and produced clearer wall and base enrichment. Both still sent nearly all incoming bulk liquid through the steam outlet, so the result established sensitivity of liquid distribution rather than improved separation. Low-feed preparation, inlet ramping and Coupled pressure–velocity treatment supplied starting fields for wall studies, with continuity residuals of approximately 0.002–0.005 at full feed. The reported full-feed state retained excess liquid removal equivalent to 20.81% of liquid feed.

Wall-film calculations made surface transport, storage and drainage separately observable. Selected windows passed local balance checks with the bulk equations active. A matched direct-drain test reduced the lower-wall store by 70.32%, but total film by only 1.70% relative to the undrained case. Local drainage therefore did not control the whole film inventory. Explicit brine-outlet studies added component and short-duration checks, without establishing sustained operating drainage.

Mesh and particle tests identified which predictions remained sensitive to numerical choices. At 195 ms, the finest of four completed frozen-bulk mesh states had about 30% less film and 32% less instantaneous drainage than the next coarser mesh. Differences in preparation and held bulk fields prevented an isolated mesh-error estimate. Reconstructed efficiency estimates agreed with earlier project estimates within 0.019 percentage points when unfinished tracks were counted as separated, although 16.78–33.29% of injected particle mass had no resolved final destination. A tenfold increase in tracking allowance more than doubled the small escaped-mass estimate.

The contribution is a set of tested modelling capabilities and evidence linking inlet distribution, liquid storage and removal. A complete, stationary, mesh-independent and physically validated separator solution was not established. The findings define the liquid accounting, particle-fate and geometry checks still needed before using the model for performance optimisation.

## Declaration

**Student:** Andy Tran (qtra338)

I hereby declare that:

1.  This report is the result of the final year project work carried out by my project partner (see cover page) and I under the guidance of our supervisor (see cover page) in the 2026 academic year at the Department Engineering Science and Biomedical Engineering, Faculty of Engineering, University of Auckland.

2.  This report is not the outcome of work done previously.

3.  This report is not the outcome of work done in collaboration, except that with a potential project sponsor (if any) as stated in the text.

4.  This report is not the same as any report, thesis, conference article or journal paper, or any other publication or unpublished work in any format.

**Statement of contribution and prior work.** The starting point was the separator CFD model supplied by Hananto Purnanto from the work reported by Purnanto et al. (2013). During the 2026 project, this model was reconstructed and assessed, and extended through split-inlet modelling, numerical liquid collection, staged loading, wall-film transport and drainage treatments, and explicit brine-outlet investigations. Mesh and particle-tracking assessments examined the limits of the resulting predictions. This report presents these developments and findings from the joint project with Shuhei Yokkaichi. Reproduced or adapted figures identify their sources in their captions.

**Use of generative AI.** OpenAI Codex assisted with coding, evidence analysis and report drafting.

**Prior report material.** The literature review reuses material from the author’s first report for this project, with subsequent revisions.

**Word count:** 11,289 words from Introduction through Future Work, including headings, captions and tables.

**Signature:** Andy Tran

**Date:** 18 October 2026

## Table of contents

1. Introduction
2. Literature review
3. Model and methods
4. Verification and validation assessment
5. Results
6. Discussion
7. Conclusions and future work
8. References
9. Appendices

Appendices A–E retain the evidence register, numerical checks, unresolved evidence, model definitions and historical particle inputs. Appendix F gives the explicit brine-outlet investigation; Appendix G gives supporting development and sensitivity results.

The LaTeX edition generates the table of contents and page references automatically.

## Acknowledgements

I would like to thank my supervisors, Sadiq Zarrouk and Maedeh Amirpour, for their guidance, advice and feedback throughout this project.

I also thank my project partner, Shuhei Yokkaichi, for his collaboration, shared work and discussions throughout the year.

I am grateful to Hananto Purnanto for providing the separator CFD model that formed the starting point for this project.

## Glossary of terms and symbols

| **Term** | **Meaning** |
|:---|:---|
| BOC | Bottom-outlet cyclone separator |
| CFD | Computational fluid dynamics |
| DPM | Discrete Phase Model (droplet tracking) |
| EWF | Eulerian Wall Film (surface liquid transport) |
| RANS | Reynolds-averaged Navier–Stokes equations |
| RNG | Renormalisation group (turbulence model) |
| VOF | Volume of Fluid (interface model) |
| Carrier field | Bulk flow used for droplet tracking |
| Active bulk | Bulk flow equations continue to update |
| Frozen bulk | Bulk fields held fixed while other models advance |
| Film accretion | Liquid transferred into the wall-film model |
| Incomplete trajectory | Particle track without a resolved final destination |
| Collector | Numerical region that removes liquid through a source |
| Stationary inventory | Retained liquid mass within stated change limits |
| Numerical acceptance | Meeting the stated checks for an individual test and observation window |
| Liquid inventory | Liquid mass retained within the vessel or wall film |
| Residual | Scaled measure of how well a discretised equation is satisfied |
| Outlet dryness (outlet steam quality) | Vapour mass fraction in flow through the steam outlet |
| Sink | Negative source term used to remove mass numerically |
| Film age | Time accumulated by the film equations; not necessarily physical elapsed time of the whole flow |
| Inner film iterations | Iterations used to solve the film equations within one film timestep |
| RMS | Root-mean-square measure used here for spatial velocity differences |
| Validation | Assessment against physical evidence for an intended use |

### Symbols 

|  |  |
|:---|:---|
| $\alpha_L$ | Liquid volume fraction |
| $\rho_L$ | Liquid density (kg/m$^{3}$) |
| $\dot m$ | Mass flow rate (kg/s) |
| $M_L$ | Retained liquid mass (kg) |
| $M_f$ | Retained wall-film mass (kg) |
| $R_L$ | Signed liquid balance remainder (kg/s) |
| $S_L$ | Liquid mass source per unit volume (kg/(m$^{3}$·s)) |
| $\tau$ | Collector depletion time (s) |
| $K$ | Dimensionless outlet-resistance coefficient |
| $\eta_{\mathrm{assumed}}$ | Efficiency estimate assuming incomplete particles are separated (%) |

