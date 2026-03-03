1. What was the paper about?
This paper introduces ContextualJudgeBench, a pairwise judge evaluation benchmark covering contextual generation settings (RAG-QA and summarisation), consisting of 2,000 preference pairs across eight splits organised around four evaluation criteria: refusal validity, faithfulness, completeness, and conciseness. The benchmark is the first dedicated to assessing LLM-based judge models in settings where evaluated responses are generated from externally provided context rather than solely from parametric knowledge. A comprehensive study evaluates 11 fine-tuned judge models (ranging from 3.8B to 70B parameters) and 9 general-purpose prompted models against this benchmark.

2. What problem did they solve?
Judge models have been touted as general-purpose evaluators but are evaluated almost exclusively on non-contextual scenarios such as instruction following, leaving their performance in contextual settings entirely unmeasured. No benchmarks existed to measure the quality of contextual evaluators, despite the increasing prevalence of RAG and summarisation use cases in which responses must be faithful to an externally provided context and evaluated accordingly. Existing pointwise evaluation approaches assign criteria scores (faithfulness, relevance) independently per response, which produces ambiguous pairwise orderings when responses differ across multiple criteria simultaneously (e.g., one response is more relevant but less faithful than another).

3. How did they solve it?
The authors introduce a conditional evaluation hierarchy that resolves criterion ambiguity by imposing a fixed "order of operations": first, refusal validity (is the response correctly refusing, or correctly substantive, given context answerability?); second, faithfulness (is the substantive response grounded in the context?); third, completeness (which faithful response covers more essential information?); fourth, conciseness (which equally complete response avoids extraneous content?). This hierarchy operates as the evaluation protocol applied to each pairwise sample and is reflected directly in the eight benchmark splits. Preference pairs are constructed via three approaches: (H) pairing existing human-annotated responses by criterion scores or errors; (M1) prompting a frontier LLM to generate a new response of a specific type (e.g., a context-based refusal, a hallucinated response) to serve as the negative or positive pair member; and (M2) prompting a frontier LLM to modify an existing response in a targeted manner (e.g., inserting direct context quotations to increase verbosity without altering substance, or removing citation-linked lines to reduce completeness). To control for positional bias, each test sample is evaluated twice with the order of responses swapped (Run 1 and Run 2); the primary metric is consistent accuracy (correct in both runs), with a random selection baseline of 25%.

4. Models and data
Models

No fine-tuning was conducted by the authors in this study; all models are used at inference time only.

Fine-tuned judge models (11 total, 3.8B to 70B): GLIDER (Deshpande et al., 2024), Prometheus-2 (Kim et al., 2024), OffsetBias (Park et al., 2024), Atla-Selene (Alexandru et al., 2025), Skywork-Critic (Shiwen et al., 2024), SFRJudge (Wang et al., 2024b), Self-taught-evaluator (Wang et al., 2024c) -- judge evaluator role -- inference only -- pre-existing fine-tuned judges
General-purpose prompted models (9 total): Llama-3.1-8B, Llama-3.1-70B, Llama-3.3-70B (Dubey et al., 2024); GPT-4o, GPT-4o-mini (Hurst et al., 2024); GPT-o1, o3-mini (Jaech et al., 2024); DeepSeek-R1 (685B) and DeepSeek-R1-distill (70B) (Guo et al., 2025) -- prompted judge role -- inference only
Reference evaluators (pointwise baselines): RAGAS (Es et al., 2023) -- applied to refusal, faithfulness, and completeness splits; MiniCheck (Tang et al., 2024) -- applied to refusal and faithfulness splits
Frontier LLM used for benchmark construction (approaches M1 and M2) -- perturbation generator -- not specified in paper
Datasets

All datasets are used for evaluation (benchmark construction); none are used for training in this study.

LFRQA (Han et al., 2024) -- evaluation -- splits 1, 3, 5, 7 (refusal answerable; faithfulness QA; completeness QA; conciseness QA)
FaithEval (Ming et al., 2024) -- evaluation -- split 2 (refusal unanswerable)
QA-Feedback (Wu et al., 2023), RAGTruth (Niu et al., 2024), LFQA (Xu et al., 2023), MRQA (Fisch et al., 2019) -- evaluation -- splits 3, 5, 7 (faithfulness QA; completeness QA; conciseness QA)
Summarisation annotation corpora: Wan et al. (2024), Lee et al. (2024), Liu et al. (2024b) -- evaluation -- splits 4, 6, 8 (faithfulness, completeness, and conciseness summarisation)
5. Experimental results
On ContextualJudgeBench, the best-performing models are o1 (55.3), o3-mini (52.6), and DeepSeek-R1 (51.9) in consistent accuracy, all large reasoning models, while the best-performing fine-tuned judge model is SFRJudge-70B (51.4), which nearly matches DeepSeek-R1. Fine-tuned judge models outperform general-purpose prompted models at comparable scale: SFRJudge-8B achieves 39.3 versus GPT-4o-mini at 38.8. Reasoning-specific training yields measurable improvement: DeepSeek-R1-Llama-70B improves upon its base model Llama-3.3-70B-Instruct by 4.4 points. The annotated text records highlighted values of 78.8 and 83.2 within a partial capture of Table 3 (page 7, consistent accuracy table), but the row and column attribution cannot be determined from the partial annotations alone. A further finding, stated in the annotated text, is that inference-time scaling for judges may actually lead to performance degradations, contrary to the trend observed in generation tasks.

6. What did they conclude?
The paper concludes that contextual evaluation is significantly more challenging than non-contextual evaluation, even for state-of-the-art models: o1, the best-performing model, barely reaches 55% consistent accuracy compared to a random baseline of 25%. The strong performance of reasoning models and the gains from reasoning-specific training (DeepSeek-R1-Llama-70B over Llama-3.3-70B-Instruct by 4.4 points) indicate that contextual evaluation is a reasoning-intensive task. Contrary to expectations from generation tasks, inference-time scaling for judges may actually lead to performance degradations in this setting. The authors conclude that ContextualJudgeBench complements existing contextual generation benchmarks by providing a systematic means of assessing contextual evaluators rather than the generators they evaluate.

7. Limitations
The frontier LLM used for benchmark construction (approaches M1 and M2) is not specified in paper. The researcher noted: "They use an LLM to generate the opposites. Which LLM?" This omission directly affects reproducibility; different construction LLMs will produce different negative examples with different detectability characteristics.

Contamination risk from LLM-generated negatives: "Problem is that everything wrong is LLM generated. Everything correct is the old perhaps already learned data." If evaluated models have been pre-trained on the original positive responses, the benchmark may not accurately reflect real-world judge performance.

The specific perturbation types used in approach M1 beyond context-based refusals and hallucinated responses are not enumerated in the annotated text. The researcher queried: "Perturbation is done by models. Which peturbations?"

The selection criteria for which responses from human-annotated datasets are retained for pairing are underspecified in the annotated text. The researcher asked: "How do they select these?"

Benchmark coverage is restricted to RAG-QA and summarisation; other contextual generation tasks (e.g., dialogue with retrieved context, code with documentation) are not included.

The mechanism by which inference-time scaling leads to performance degradations is not explained in the annotated text (later sections were truncated in the annotations reviewed).

8. My take
The conditional evaluation hierarchy is the paper's genuinely useful structural contribution: "Refusal is the most imporant. It means go retrieve again. Next is faithful. Is this grounded in your output." This ordering is operationally well-motivated for RAG systems, where failing to refuse on an unanswerable question is a harder failure to recover from than producing a slightly incomplete faithful answer. I am concerned about the long-term validity of the benchmark because "Problem is that everything wrong is LLM generated. Everything correct is the old perhaps already learned data", meaning that negative examples are synthetic and may be systematically distinguishable by models trained on the same underlying data. The unanswered question of which frontier LLM was used for construction ("They use an LLM to generate the opposites. Which LLM?") is a real reproducibility gap that undermines the claim of a reliable, fixed evaluation standard. The finding that inference-time scaling may degrade judge performance is counterintuitive and worth replicating carefully before drawing conclusions about the cost-effectiveness of reasoning-model judges.

9. Summary
ContextualJudgeBench is a pairwise judge evaluation benchmark for contextual generation settings (RAG-QA and summarisation), consisting of 2,000 preference pairs across eight splits organised around a conditional evaluation hierarchy (refusal validity, faithfulness, completeness, conciseness). Prior judge benchmarks evaluated only non-contextual scenarios such as instruction following, leaving judge performance in contextual settings where responses are generated from externally provided context entirely unmeasured, and providing no principled mechanism for resolving ambiguous pairwise comparisons across multiple criteria simultaneously. The authors construct preference pairs using three approaches (human annotations, frontier LLM generation of typed responses, frontier LLM modification of existing responses) and evaluate under a consistency setup that swaps response order across two runs, with consistent accuracy as the primary metric and a 25% random baseline. Eleven fine-tuned judge models (including GLIDER, SFRJudge, Prometheus-2, and Atla-Selene, ranging from 3.8B to 70B parameters) and nine general-purpose models (including o1, DeepSeek-R1, and GPT-4o) were evaluated at inference time on source datasets including LFRQA, FaithEval, QA-Feedback, and RAGTruth, with the best-performing model o1 achieving 55.3 consistent accuracy versus a 25% random baseline. The data construction methodology raises a fundamental concern: "Problem is that everything wrong is LLM generated. Everything correct is the old perhaps already learned data", meaning that benchmark negatives are synthetic and potentially systematically detectable by models trained on the same data distributions, calling into question the validity of this evaluation approach as evaluated models continue to be trained.

10. BibTeX

@inproceedings{xu-etal-2025-context,
    title = "Does Context Matter? {C}ontextual{J}udge{B}ench for Evaluating {LLM}-based Judges in Contextual Settings",
    author = "Xu, Austin  and
      Bansal, Srijan  and
      Ming, Yifei  and
      Yavuz, Semih  and
      Joty, Shafiq",
    editor = "Che, Wanxiang  and
      Nabende, Joyce  and
      Shutova, Ekaterina  and
      Pilehvar, Mohammad Taher",
    booktitle = "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
    month = jul,
    year = "2025",
    address = "Vienna, Austria",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.acl-long.470/",
    doi = "10.18653/v1/2025.acl-long.470",
    pages = "9541--9564",
    ISBN = "979-8-89176-251-0"
}
Sanity check log:

Section 8 contains verbatim NOTEs: "Refusal is the most imporant. It means go retrieve again. Next is faithful. Is this grounded in your output." and "Problem is that everything wrong is LLM generated. Everything correct is the old perhaps already learned data" and "They use an LLM to generate the opposites. Which LLM?" (checkmark)
Section 9, sentence 5 contains verbatim NOTE: "Problem is that everything wrong is LLM generated. Everything correct is the old perhaps already learned data" (checkmark)
All numeric results (55.3, 52.6, 51.9, 51.4, 39.3, 38.8, 4.4, 25%, 2,000) traced to annotated text (checkmark); 78.8 and 83.2 noted as partially unattributable from partial table capture
Method names exact: ContextualJudgeBench, M1, M2, H (checkmark)
Models and datasets explicitly listed or marked not specified in paper (checkmark)
No abstract-only summary (checkmark)
No speculation (checkmark)
No em dashes (checkmark)
Summary is exactly five sentences (checkmark)