"""Seed manifest.db with demo artifacts, chunks, and embeddings."""

import sqlite3
import struct
import sys
from pathlib import Path

import os

DB_DIR = Path(os.environ.get("EVO_STORE", str(Path(__file__).resolve().parent.parent / "data")))
DB_PATH = DB_DIR / "manifest.db"

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '',
    topics TEXT NOT NULL DEFAULT '',
    html_path TEXT,
    md_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    title, summary, tags, topics,
    content='artifacts', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    char_start INTEGER NOT NULL DEFAULT 0,
    char_end INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='chunks', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
"""

# NOTE: embeddings table created separately after sqlite-vec is loaded

ARTIFACTS = [
    {
        "slug": "transformer-attention-mechanism",
        "title": "The Transformer Attention Mechanism",
        "summary": "The transformer architecture, introduced in 'Attention Is All You Need' (Vaswani et al., 2017), replaced recurrence with self-attention — allowing every token in a sequence to attend to every other token in parallel. Scaled dot-product attention computes Q, K, V matrices from input embeddings, then calculates attention weights as softmax(QK^T / sqrt(d_k)). Multi-head attention runs this operation h times with different learned projections, then concatenates the results. This parallelism is what makes transformers trainable on massive datasets — unlike RNNs, there's no sequential bottleneck. The quadratic memory cost of self-attention (O(n^2) in sequence length) drove later innovations like Flash Attention, which fuses the attention computation to avoid materializing the full attention matrix in HBM, reducing memory from O(n^2) to O(n) while maintaining exact computation. Modern LLMs from GPT-4 to Claude to Gemini are all transformer variants. The architecture's dominance comes not from any single innovation but from how well attention scales with compute and data.",
        "tags": "transformers,attention,deep-learning,architecture",
        "topics": "self-attention,multi-head-attention,flash-attention,scaling-laws",
        "created_at": "2026-03-15 10:00:00",
    },
    {
        "slug": "nvidia-blackwell-architecture",
        "title": "NVIDIA Blackwell GPU Architecture and AI Infrastructure",
        "summary": "NVIDIA's Blackwell architecture (B200/GB200) represents a generational leap in AI compute density. Each B200 GPU contains 208 billion transistors on a two-die design connected by a 10 TB/s chip-to-chip interconnect — the first GPU to use TSMC's 4NP process at this scale. Key architectural innovations: a second-generation Transformer Engine that supports FP4 precision (doubling inference throughput per watt versus Hopper's FP8), a fifth-generation NVLink delivering 1.8 TB/s bidirectional bandwidth between GPUs (up from 900 GB/s on H100), and a dedicated decompression engine that enables database-query-scale joins directly in GPU memory. The GB200 NVL72 rack-scale system packages 36 Grace CPUs and 72 Blackwell GPUs into a single liquid-cooled rack delivering 720 PFLOPS of FP4 inference. For training, Blackwell enables trillion-parameter models that previously required multiple racks to fit in a single NVL72 system. The DGX B200 targets AI factories — purpose-built datacenters where the GPU is the unit of compute, not the server. Jensen Huang's thesis: the more you buy, the more you save, because larger models running on denser hardware produce better tokens-per-dollar economics.",
        "tags": "nvidia,hardware,gpu,infrastructure,blackwell",
        "topics": "blackwell,b200,nvlink,ai-infrastructure,fp4",
        "created_at": "2026-03-22 14:30:00",
    },
    {
        "slug": "rapamycin-longevity-research",
        "title": "Rapamycin and the mTOR Pathway in Longevity Research",
        "summary": "Rapamycin, originally discovered as an antifungal compound from soil bacteria on Easter Island (Rapa Nui), is the most replicated pharmacological intervention for lifespan extension in laboratory animals. It works by inhibiting mTOR (mechanistic target of rapamycin), a kinase that acts as a central integrator of nutrient sensing, growth signals, and cellular metabolism. When nutrients are abundant, mTOR promotes cell growth and protein synthesis; when inhibited by rapamycin, cells shift toward autophagy — the recycling of damaged proteins and organelles. In mice, rapamycin extended median lifespan by 9-14% even when started late in life (equivalent to age 60 in humans), an effect observed across multiple independent labs in the NIA Interventions Testing Program. The mechanism is not simply caloric restriction mimicry — rapamycin also reduces senescent cell burden, improves immune function in elderly subjects (shown in a 2014 Novartis trial where low-dose rapamycin analogs improved vaccine responses in people over 65 by 20%), and suppresses the senescence-associated secretory phenotype (SASP). Current human trials are exploring intermittent dosing protocols to capture longevity benefits while minimizing immunosuppressive side effects. The key open question: does mTOR inhibition extend human healthspan, or only compress morbidity?",
        "tags": "longevity,biology,rapamycin,aging,mtor",
        "topics": "mtor-pathway,autophagy,lifespan-extension,senescence",
        "created_at": "2026-04-05 09:15:00",
    },
    {
        "slug": "metabolic-health-insulin-resistance",
        "title": "Insulin Resistance: The Metabolic Root of Chronic Disease",
        "summary": "Insulin resistance — the diminished ability of cells to respond to insulin signaling — underlies a cluster of conditions including type 2 diabetes, cardiovascular disease, non-alcoholic fatty liver disease, and possibly Alzheimer's (increasingly called 'type 3 diabetes'). The mechanism: when cells are chronically exposed to high insulin levels (driven by frequent carbohydrate-dense meals), they downregulate insulin receptors as a protective response, similar to how chronic noise exposure reduces hearing sensitivity. The liver becomes the first casualty — hepatic insulin resistance leads to uncontrolled gluconeogenesis (glucose production even when blood sugar is already high) and de novo lipogenesis (converting excess carbohydrates to fat, manifesting as visceral and liver fat). Peter Attia's framework distinguishes metabolic health from body composition: a person with normal BMI can be metabolically unhealthy (TOFI — thin outside, fat inside), while an overweight person with good insulin sensitivity may have lower cardiovascular risk. Key biomarkers: fasting insulin (more sensitive than fasting glucose, which rises only after significant beta-cell damage), HOMA-IR, triglyceride-to-HDL ratio (a proxy for LDL particle size), and oral glucose tolerance test with insulin measurements. Interventions that restore insulin sensitivity: time-restricted eating (extending the overnight fast to 16+ hours), resistance training (muscle is the largest glucose sink), sleep optimization (one night of sleep deprivation can induce transient insulin resistance), and zone 2 cardio (improves mitochondrial density and fat oxidation capacity).",
        "tags": "health,metabolism,insulin,chronic-disease",
        "topics": "insulin-resistance,metabolic-syndrome,type-2-diabetes,cardiovascular",
        "created_at": "2026-04-12 11:00:00",
    },
    {
        "slug": "context-window-engineering",
        "title": "Context Window Engineering: From 4K to 1M+ Tokens",
        "summary": "The context window — how many tokens an LLM can process in a single forward pass — has expanded from GPT-3's 2,048 tokens to Gemini 1.5's 1 million+ tokens in under three years. This expansion required solving several interconnected problems. The fundamental challenge is the quadratic cost of self-attention: doubling the context length quadruples the compute and memory. Solutions fall into three categories. First, architectural modifications: sparse attention patterns (Longformer, BigBird) that attend to local windows plus selected global tokens, reducing complexity to O(n·sqrt(n)); ring attention that distributes sequence chunks across devices so each GPU only computes attention for its local segment. Second, position encoding innovations: RoPE (Rotary Position Embedding) enables length generalization by encoding position as rotations in the embedding space, allowing models trained on short sequences to extrapolate to longer ones via NTK-aware scaling or YaRN. Third, inference-time techniques: KV-cache compression (storing only key-value pairs for a sliding window plus landmark tokens), and retrieval-augmented approaches that offload long-context to an external index. The practical impact: long context enables in-context learning with entire codebases, document-level reasoning without chunking artifacts, and 'many-shot' prompting where hundreds of examples replace fine-tuning. But longer context doesn't mean better retrieval — the 'lost in the middle' phenomenon shows models attend more to the beginning and end of their context, with degraded recall for information in the middle.",
        "tags": "llm,context-window,architecture,scaling",
        "topics": "context-length,rope,sparse-attention,kv-cache,lost-in-the-middle",
        "created_at": "2026-04-20 16:00:00",
    },
    {
        "slug": "sleep-architecture-cognitive-performance",
        "title": "Sleep Architecture and Its Impact on Cognitive Performance",
        "summary": "Sleep is not a monolithic state but a precisely orchestrated cycle of distinct stages, each serving different biological functions. A typical 8-hour night contains 4-6 cycles, each lasting approximately 90 minutes. Stage N3 (slow-wave sleep, or deep sleep) dominates the first half of the night and is critical for memory consolidation — the hippocampus replays the day's experiences and transfers selected memories to neocortical long-term storage through sharp-wave ripples. REM sleep, which increases in duration toward morning, is where emotional memory processing and creative problem-solving occur — the brain makes novel associations between seemingly unrelated concepts (which is why solutions often arrive 'overnight'). Matthew Walker's research at UC Berkeley demonstrates the cognitive costs of sleep deprivation with precision: after 24 hours without sleep, cognitive performance drops to the equivalent of a 0.1% blood alcohol level. Even modest chronic restriction (6 hours/night for two weeks) produces impairments equivalent to two full nights of total deprivation, but — critically — subjects lose the ability to perceive their own impairment, creating a dangerous illusion of competence. For engineers and researchers, the most actionable findings: sleep spindles (12-16 Hz oscillations in stage N2) correlate with motor skill consolidation and fluid intelligence; morning REM deprivation (from alarm clocks cutting the night short) disproportionately impacts creative and divergent thinking; caffeine has a half-life of 5-6 hours, meaning a 2 PM coffee still has 25% of its stimulant effect at midnight; and alcohol, despite sedating you faster, fragments sleep architecture and suppresses REM by 20-50%.",
        "tags": "health,sleep,neuroscience,cognition,performance",
        "topics": "sleep-stages,memory-consolidation,rem-sleep,slow-wave-sleep",
        "created_at": "2026-05-01 08:30:00",
    },
    {
        "slug": "apple-silicon-unified-memory",
        "title": "Apple Silicon: Unified Memory Architecture and ML Implications",
        "summary": "Apple's M-series chips (M1 through M4 Ultra) introduced unified memory architecture (UMA) to consumer hardware — a design where the CPU, GPU, and Neural Engine share a single pool of high-bandwidth memory, eliminating the copy overhead that plagues discrete GPU systems. On a traditional x86 + NVIDIA setup, moving a tensor from CPU to GPU requires traversing PCIe (64 GB/s for PCIe 5.0 x16) — a bottleneck that dominates inference time for memory-bound workloads. Apple's UMA eliminates this entirely: the GPU reads the same physical memory the CPU wrote to, with no copy. The M4 Ultra offers 192GB of unified memory with 819 GB/s bandwidth — enough to run a 70B parameter model (quantized to 4-bit) entirely in memory with responsive token generation. This makes Apple Silicon uniquely positioned for local LLM inference: while an NVIDIA H100 has more raw FLOPS, getting a 70B model onto a consumer NVIDIA GPU requires either extreme quantization or multi-GPU setups with $10K+ hardware. A Mac Studio with M4 Ultra runs the same model from a single wall outlet. The Neural Engine (16-core on M4) adds dedicated matrix multiply hardware for on-device ML tasks. The practical impact for AI engineers: local model development, fine-tuning experimentation, and RAG pipeline testing can happen on a laptop without cloud GPU costs. The limitation remains training — UMA bandwidth, while excellent for inference, cannot match the 3.35 TB/s of HBM3e on an H100 for gradient-heavy training workloads.",
        "tags": "hardware,apple,silicon,ml-inference,architecture",
        "topics": "unified-memory,apple-silicon,local-inference,m4-ultra",
        "created_at": "2026-05-10 13:45:00",
    },
    {
        "slug": "zone-2-training-mitochondrial-health",
        "title": "Zone 2 Training: Mitochondrial Density and Metabolic Flexibility",
        "summary": "Zone 2 cardiovascular training — sustained exercise at an intensity where you can maintain a conversation but with slight effort (roughly 60-70% of max heart rate, or a blood lactate level of 1.7-2.0 mmol/L) — is the single most efficient exercise modality for improving metabolic health at the cellular level. The mechanism operates through mitochondrial biogenesis: sustained, moderate-intensity aerobic exercise activates PGC-1α, the master regulator of mitochondrial production, increasing both the number and efficiency of mitochondria in type I muscle fibers. More mitochondria means greater capacity to oxidize fatty acids for fuel (fat oxidation peaks at zone 2 intensity), reducing reliance on glucose and improving metabolic flexibility — the ability to switch between fuel sources based on availability. Iñigo San-Millán, the exercise physiologist who trains Tadej Pogačar and advises Peter Attia, has published data showing that zone 2 training is the only intensity that specifically improves mitochondrial function without producing excessive lactate that shifts energy production toward glycolysis. The minimum effective dose appears to be 3-4 sessions per week of 45-60 minutes each. Higher-intensity training (HIIT, zone 5) improves VO2max and cardiac output but does not equivalently stimulate mitochondrial biogenesis — it primarily improves the heart's pump capacity and glycolytic pathway efficiency. For knowledge workers concerned about cognitive longevity, the connection is direct: the brain consumes 20% of the body's oxygen despite being 2% of body mass. Improved mitochondrial density means better cerebral oxygen delivery and ATP production, which correlates with sustained attention, working memory, and resistance to cognitive decline with age.",
        "tags": "health,exercise,mitochondria,metabolism,longevity",
        "topics": "zone-2,mitochondrial-biogenesis,metabolic-flexibility,fat-oxidation",
        "created_at": "2026-05-18 07:00:00",
    },
    {
        "slug": "structured-output-json-mode",
        "title": "Structured Output: Getting Reliable JSON from LLMs",
        "summary": "Getting an LLM to return valid, schema-conformant JSON is harder than it sounds and essential for building reliable applications. Three approaches have emerged, each with different tradeoff profiles. First, prompt-based: instruct the model to return JSON and hope — unreliable at 85-95% compliance even with detailed schema descriptions; fails on nested objects, enums, and optional fields. Second, constrained decoding: modify the token sampling process to only allow tokens that produce valid JSON at each step. This is what OpenAI's 'json_mode' and Anthropic's tool use implement — the model physically cannot produce invalid output because the decoder masks out syntactically illegal tokens. Outlines and guidance are open-source libraries that implement constrained decoding for local models. Third, schema-validated generation with retry: generate freely, validate against a Zod/Pydantic schema, and retry on failure. This preserves the model's full generative capability but adds latency for retries. The practical architecture: use constrained decoding (function calling / tool use) for production pipelines where reliability is non-negotiable, and schema-validated generation for exploratory tasks where the model needs more freedom. For RAG applications specifically, structured output enables typed citation objects (source slug, excerpt, confidence score) rather than hoping the model formats citations consistently in prose.",
        "tags": "llm,json,structured-output,engineering,reliability",
        "topics": "constrained-decoding,json-mode,function-calling,schema-validation",
        "created_at": "2026-05-25 15:30:00",
    },
    {
        "slug": "creatine-cognitive-neuroprotection",
        "title": "Creatine Beyond Muscle: Cognitive Benefits and Neuroprotection",
        "summary": "Creatine monohydrate, the most studied sports supplement in history with over 500 peer-reviewed papers, has cognitive benefits that are only now receiving serious attention. The mechanism is straightforward: creatine donates a phosphate group to regenerate ATP from ADP, and the brain — despite being 2% of body mass — consumes 20% of the body's ATP. Creatine supplementation increases brain phosphocreatine reserves by 5-15%, providing a larger buffer for ATP regeneration during cognitively demanding tasks. A 2018 meta-analysis in Experimental Gerontology found that creatine supplementation improved short-term memory and reasoning in healthy adults, with stronger effects under conditions of stress, sleep deprivation, or aging — precisely the conditions where ATP demand exceeds supply. The effect size is modest but consistent: 5-10% improvement in working memory tasks under cognitive load. For vegetarians and vegans, the effects are larger (10-15%) because they have lower baseline brain creatine from lack of dietary intake (creatine is found primarily in meat and fish). The neuroprotective angle is more speculative but compelling: traumatic brain injury depletes brain creatine reserves, and animal studies show pre-injury creatine loading reduces cortical damage by up to 36%. Human trials are underway for creatine's role in concussion recovery. Standard dosing: 3-5g daily of creatine monohydrate, no loading phase needed, taken consistently. It's one of the few supplements where the evidence base is robust enough to recommend broadly — safe, cheap ($0.03/day), and effective across multiple outcome measures.",
        "tags": "health,supplements,cognition,creatine,neuroprotection",
        "topics": "creatine-monohydrate,atp-regeneration,cognitive-enhancement,brain-health",
        "created_at": "2026-06-02 10:15:00",
    },
    {
        "slug": "ai-inference-economics",
        "title": "The Economics of AI Inference: Cost Curves and Scaling Dynamics",
        "summary": "The cost of AI inference is falling faster than Moore's Law ever delivered for general compute, but the dynamics are more complex than a single curve suggests. Three forces are driving costs down simultaneously. First, hardware efficiency: each GPU generation (H100 → B200 → next) delivers roughly 2-3x inference throughput per watt, compounded by architectural innovations like FP4 precision and speculative decoding. Second, model distillation: smaller models trained to mimic larger ones (GPT-4o mini, Claude Haiku, Gemma) deliver 80-90% of frontier model quality at 10-50x lower cost. Third, software optimization: vLLM's PagedAttention, continuous batching, and KV-cache sharing reduce serving costs by 2-5x compared to naive implementations, independent of hardware. The result: GPT-3.5 level quality that cost $60 per million tokens in 2022 now costs under $0.10. But demand is elastic — as inference gets cheaper, applications that were economically impossible become viable (real-time RAG on every search query, AI-generated UI for every user session, continuous code review), so total spend increases even as unit costs fall. This is Jevons' paradox applied to compute. For application builders, the strategic implication is clear: optimize for quality and latency first, cost second, because the cost floor is dropping out from under you. The architecture decisions that matter are not 'how to make this cheaper today' but 'how to make this better when inference is 10x cheaper next year.'",
        "tags": "ai,economics,inference,scaling,infrastructure",
        "topics": "inference-cost,distillation,vllm,jevons-paradox,optimization",
        "created_at": "2026-06-10 12:00:00",
    },
    {
        "slug": "vo2max-all-cause-mortality",
        "title": "VO2max: The Single Strongest Predictor of All-Cause Mortality",
        "summary": "Cardiorespiratory fitness, measured as VO2max (maximum oxygen uptake during exercise), is the single strongest predictor of all-cause mortality — stronger than smoking, hypertension, or diabetes as independent risk factors. A 2018 study in JAMA Network Open following 122,007 patients over 23 years found that moving from the bottom 25th percentile to above the 95th percentile of fitness was associated with a 5x reduction in mortality risk. Crucially, there was no upper plateau — being in the 'elite' fitness category (top 2.3%) continued to reduce risk versus merely 'above average.' The mechanism is multi-system: high VO2max reflects efficient oxygen delivery (cardiac output × arteriovenous O2 difference), which requires a strong heart, compliant vasculature, high hemoglobin mass, dense capillary networks in muscle, and high mitochondrial density. Each of these adaptations independently reduces disease risk. Peter Attia frames the practical implication using what he calls the 'Centenarian Decathlon' — a list of 18 physical tasks you want to be able to perform at age 100 (carry groceries, climb stairs, get up from the floor, etc.). Since VO2max declines approximately 10% per decade after age 30, you need to build a large enough reserve in your 30s-50s that the inevitable decline still leaves you above the functional threshold at 80-100. A 50-year-old man with a VO2max of 50 ml/kg/min (97th percentile) who declines to 30 ml/kg/min at age 80 is still functionally independent; one who starts at 35 (50th percentile) and declines to 21 is below the threshold for independent living. The prescription: 3-4 sessions of zone 2 per week (builds the aerobic base) plus 1-2 sessions of high-intensity intervals (pushes the VO2max ceiling). This combination is more effective than either modality alone.",
        "tags": "health,fitness,longevity,cardio,vo2max",
        "topics": "vo2max,all-cause-mortality,cardiorespiratory-fitness,centenarian-decathlon",
        "created_at": "2026-06-15 08:00:00",
    },
]


def seed():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        print(f"DB exists at {DB_PATH} — removing for fresh seed.")
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    # Load sqlite-vec for embeddings table
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception as exc:
        print(f"WARNING: sqlite-vec not available ({exc}). Skipping embeddings.")
        _seed_artifacts_and_chunks(conn, embed=False)
        conn.close()
        return

    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(chunk_id INTEGER PRIMARY KEY, embedding float[{EMBEDDING_DIM}])"
    )

    _seed_artifacts_and_chunks(conn, embed=True)
    conn.close()


def _seed_artifacts_and_chunks(conn: sqlite3.Connection, embed: bool) -> None:
    # Insert artifacts
    for art in ARTIFACTS:
        conn.execute(
            "INSERT INTO artifacts (slug, title, summary, tags, topics, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                art["slug"],
                art["title"],
                art["summary"],
                art["tags"],
                art["topics"],
                art["created_at"],
                art["created_at"],
            ),
        )

    conn.commit()

    # Create chunks from summaries
    artifacts = conn.execute("SELECT id, summary FROM artifacts").fetchall()
    chunk_ids_texts: list[tuple[int, str]] = []

    for art_id, summary in artifacts:
        if not summary:
            continue
        cursor = conn.execute(
            "INSERT INTO chunks (artifact_id, text, char_start, char_end) VALUES (?, ?, 0, ?)",
            (art_id, summary, len(summary)),
        )
        chunk_ids_texts.append((cursor.lastrowid, summary))

    conn.commit()
    print(f"Seeded {len(ARTIFACTS)} artifacts and {len(chunk_ids_texts)} chunks.")

    if not embed or not chunk_ids_texts:
        return

    # Embed chunks
    print("Computing embeddings with fastembed...")
    try:
        from fastembed import TextEmbedding

        embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    except ImportError:
        print("WARNING: fastembed not installed. Skipping embeddings.")
        return

    texts = [text for _, text in chunk_ids_texts]
    embeddings = list(embedder.embed(texts))

    for (chunk_id, _), embedding in zip(chunk_ids_texts, embeddings):
        blob = struct.pack(f"{len(embedding)}f", *embedding.tolist())
        conn.execute(
            "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, blob),
        )

    conn.commit()
    print(f"Embedded {len(embeddings)} chunks ({EMBEDDING_DIM} dims).")


if __name__ == "__main__":
    seed()
