# Development of a Multitask Transformer-Based Model and Web System for Joint Sentiment Analysis and AI-Generated Review Provenance Classification: A Controlled Mixed-Domain Study

**Manuscript status:** research protocol and system design draft. No trained model, assembled study corpus, or empirical model results are reported in this draft.

## Abstract

Online reviews communicate evaluative sentiment, while their provenance may be human-authored or generated with language models. These are related but distinct prediction tasks. This manuscript specifies a planned controlled mixed-domain study and a prototype web system for evaluating a shared Transformer encoder with separate sentiment and provenance heads. The planned comparison includes single-task neural baselines and non-neural baselines under in-domain, domain-held-out, and generator-held-out evaluation. To reduce confounding, human and generated reviews will be balanced or stratified by domain, sentiment, and length where feasible, and source-related variants will remain within one split. Evaluation will report class-sensitive discrimination, calibration, subgroup performance, and uncertainty. A nine-specialist orchestration prototype currently implements request validation, preprocessing, language and domain checks, separate heuristic task estimates, evidence checking, reliability gating, and synthesis. It is an architectural demonstration only: its heuristic outputs are not experimental findings. The study is designed to test whether joint training provides useful transfer without concealing negative transfer or out-of-distribution failures. Provenance outputs will be treated as fallible signals, not proof of authorship.

**Keywords:** multitask learning; sentiment analysis; AI-generated text detection; review provenance; domain adaptation; evaluation protocol

## 1. Introduction

Reviews are useful both for their expressed opinions and for studying how their text was produced. Sentiment classification estimates evaluative polarity; provenance classification estimates whether a text belongs to a human-authored or machine-generated class defined by the study. Neither task answers whether a review is truthful, deceptive, or representative. Their labels and error costs differ, so a system should expose the two outputs separately.

Multitask learning can improve a task by sharing representations, but gains are not guaranteed and task interactions can be negative (Caruana, 1997; Liu et al., 2019). Sentiment also varies across domains, motivating explicit domain-aware evaluation (Blitzer et al., 2007). Machine-generated text detection has been studied across generators, languages, and domains; benchmarks make evaluation conditions central to interpreting detector scores and documenting generalization limits (Wang et al., 2024a, 2024b; He et al., 2024). Separately, detector performance may be brittle under text modifications (Mitchell et al., 2023; Sadasivan et al., 2025), and language-related bias has been reported for non-native English writing (Liang et al., 2023).

This study therefore focuses on controlled comparisons, not a claim that a particular architecture is already superior. The planned contribution is a reproducibility-oriented evaluation protocol, to be finalized with concrete data sources, generation settings, annotations, and split IDs, plus a web-system prototype that keeps sentiment and provenance outputs distinct, surfaces uncertainty and abstention, and records experimental-example provenance.

## 2. Research questions

**RQ1.** Under matched training data and evaluation splits, does a shared-encoder multitask model improve sentiment and provenance macro-F1 relative to corresponding single-task models, in-domain and across held-out domains?

**RQ2.** How do provenance and sentiment performance, calibration, and error types vary across review domains and held-out text generators?

**RQ3.** Does joint training create measurable negative transfer for either task or any domain/generator subgroup, compared with single-task training?

These questions are answerable only after a licensed corpus, model runs, and predeclared splits exist. They do not assume positive results.

## 3. Proposed system

The planned predictor uses a pretrained Transformer encoder with two task-specific heads: a sentiment head for the chosen sentiment label set and a binary provenance head for human versus generated origin under the study’s operational definition. The web system will return both predictions, calibrated confidence or an explicit abstention, domain and language metadata, model/version identifiers, and a notice that provenance is not proof of authorship.

The current prototype is a local Python system with a coordinator and nine specialists: request validation, preprocessing, language, domain context, sentiment, provenance cues, evidence checking, reliability gating, and synthesis. It demonstrates message contracts and inter-agent handoffs. It uses a small hand-authored lexicon and heuristic provenance features, not a Transformer. Its output is excluded from all proposed model-performance claims. The implementation and current limitations are documented in the [project report](report.md).

## 4. Proposed methods

### 4.1 Data construction and documentation

The study will combine human-authored review text obtained from sources whose licenses and terms permit the intended research use with generated review text produced under recorded prompts by multiple documented language-model generators. The concrete sources, model names and versions, dates, prompt templates, decoding settings, and licensing status remain to be selected and recorded before collection. No dataset is claimed as already assembled.

For each example, retain a study ID, text, operational sentiment label and annotation provenance, domain, origin class, generator or human-source metadata as permitted, collection date or generation settings, language, length, and source/group ID. Publish a data statement describing collection, exclusions, label definitions, intended use, privacy review, and redistribution restrictions. Human and generated text must not be balanced by changing the text itself. If exact matching is not feasible, report distributions and use stratification or covariate analyses.

### 4.2 Annotation and quality control

Define sentiment labels before annotation, including how neutral, mixed, and ambiguous opinions are handled. Use independent annotators for a documented subset, adjudicate disagreements with a written protocol, and report agreement with a statistic suited to the label design. Provenance labels should come from verified collection/generation metadata, not from a detector’s prediction. Exclude or separately label cases with uncertain provenance. Review annotators should not infer authorship from style.

### 4.3 Leakage control and splits

Deduplicate exact and near-duplicate texts before splitting. Variants derived from one prompt, product/review source, or base text must be grouped by source ID and assigned to a single split. Publish split counts and the overlap audit. Use a fixed training/validation/test split for in-domain evaluation, leave-one-domain-out testing for domain generalization, and a generator-held-out test set for provenance generalization. Select thresholds and calibrators on validation data only. Keep the test set sealed until final evaluation.

### 4.4 Models and comparisons

Compare: (a) shared-encoder multitask Transformer with two heads; (b) two single-task Transformer models using the same backbone and comparable tuning budget; (c) majority or stratified-prior baselines; and (d) a transparent lexical or conventional feature baseline. Use identical split IDs and document pretrained model, tokenizer, hyperparameters, random seeds, class weighting, early stopping, and compute. Ablations may remove one head’s loss during training or remove domain metadata, provided they are declared before test evaluation.

### 4.5 Metrics and statistical analysis

For each task report macro-F1, per-class precision, recall and F1, confusion matrix, and accuracy as a secondary measure. For binary provenance also report PR-AUC, especially if class prevalence is unequal. Report calibration using Brier score and expected calibration error with the binning procedure specified. Provide results by domain, generator, language, and relevant length strata when sample sizes permit. Estimate uncertainty with bootstrap resampling grouped by source ID; use paired comparisons on identical examples and report confidence intervals and effect sizes. Report abstention coverage and selective performance if the application gate can abstain. Do not interpret a single aggregate score as proof of robustness.

### 4.6 Reliability and web evaluation

The web-system evaluation will test schema validation, unsupported-language handling, known/unknown domains, abstention behavior, evidence traceability, response consistency, and logging. A separate usability evaluation would require an approved protocol and participant consent; it is outside the current prototype report. System latency and failure rate should be measured on specified hardware after the model is integrated.

## 5. Planned results and reporting

No empirical model results are available at manuscript-draft time. Results tables should be populated only from reproducible runs after the data and splits are frozen. The final manuscript should include: dataset composition and split audit; model/hyperparameter table; in-domain and held-out metrics with uncertainty; calibration and abstention; error examples with sensitive details removed; and ablations. If multitask learning fails to improve one or both tasks, that outcome remains reportable and directly answers RQ1/RQ3.

## 6. Threats to validity and responsible use

**Construct validity:** “AI-generated” is an operational dataset label tied to recorded sources and generation procedures, not an intrinsic property detectable with certainty. Sentiment labels are subjective and depend on annotation policy.

**Internal validity:** source, prompt, domain, length, and sentiment can become shortcuts for provenance. Grouped splits, metadata audits, matched/stratified distributions, and baselines reduce but cannot eliminate confounding.

**External validity:** findings may not transfer to languages, domains, generators, editing practices, or time periods outside the evaluation. Detector work has documented distribution sensitivity and bias concerns (Sadasivan et al., 2025; Liang et al., 2023).

**Ethical use:** provenance classification can falsely accuse human writers or misclassify edited machine text. Do not use model output as sole evidence for moderation, academic-integrity action, employment, or authorship adjudication. Provide human review, abstention, and a clear limitation notice. Respect dataset licenses, privacy terms, and applicable institutional review requirements.

## 7. Conclusion

This manuscript defines a falsifiable evaluation of joint sentiment and review-provenance classification across controlled domains and generators. A multi-agent prototype provides inspectable orchestration, evidence checks, and reliability gating, but it does not yet implement or validate the proposed Transformer. The next scientific step is to freeze a documented corpus and split protocol, train matched baselines, and report both successful and negative-transfer results with subgroup uncertainty.

## Declarations

- **Data availability:** no study corpus has yet been assembled for this draft. The final statement must identify sources, licenses, access conditions, and any restricted material.
- **Code availability:** prototype source is included with this coursework project; model-training code is not yet implemented.
- **Funding / conflicts of interest:** to be completed by the author for the final submission; no personal declarations are inferred here.
- **Ethics review:** no human-subject experiment is reported in this protocol draft. Review the institution’s requirements before collecting data or involving participants.
- **AI assistance disclosure:** complete this field according to course and institutional policy before submission.

## References

Blitzer, J., Dredze, M., & Pereira, F. (2007). Biographies, Bollywood, boom-boxes and blenders: Domain adaptation for sentiment classification. *Proceedings of ACL 2007*, 440–447. https://aclanthology.org/P07-1056/

Caruana, R. (1997). Multitask learning. *Machine Learning, 28*, 41–75. https://doi.org/10.1023/A:1007379606734

He, X., Shen, X., Chen, Z., Backes, M., & Zhang, Y. (2024). MGTBench: Benchmarking machine-generated text detection. *Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security*, 2251–2265. https://doi.org/10.1145/3658644.3670344

Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779

Liu, X., He, P., Chen, W., & Gao, J. (2019). Multi-task deep neural networks for natural language understanding. *Proceedings of ACL 2019*, 4487–4496. https://doi.org/10.18653/v1/P19-1441

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., & Finn, C. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. *Proceedings of ICML 2023, PMLR 202*, 24950–24962. https://proceedings.mlr.press/v202/mitchell23a.html

Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2025). Can AI-generated text be reliably detected? Stress testing AI text detectors under various attacks. *Transactions on Machine Learning Research*. https://openreview.net/forum?id=00gsAZdF0t

Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Afzal, O. M., Mahmoud, T., Puccetti, G., Arnold, T., Aji, A. F., Habash, N., Gurevych, I., & Nakov, P. (2024a). M4GT-Bench: Evaluation benchmark for black-box machine-generated text detection. *Proceedings of ACL 2024*, 3964–3992. https://doi.org/10.18653/v1/2024.acl-long.218

Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Afzal, O. M., Mahmoud, T., Puccetti, G., & Arnold, T. (2024b). SemEval-2024 Task 8: Multidomain, multimodel and multilingual machine-generated text detection. *Proceedings of SemEval 2024*, 2057–2079. https://doi.org/10.18653/v1/2024.semeval-1.279
