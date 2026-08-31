"""
PlantCare AI - Plant Disease Chatbot Assistant

Uses TF-IDF search over a plant disease dataset and Groq API (GPT model)
to answer user questions about plant diseases, symptoms, prevention, and treatment.
"""

import os
from pathlib import Path
from chatbot.disease_knowledge import (
    get_disease_info, get_treatment_info, get_crop_diseases,
    CROP_SEASONAL_GUIDE, HOMEMADE_REMEDIES, FERTILIZER_GUIDE, PESTICIDE_GUIDE
)

# =========================================================
# LAZY INITIALIZATION
# =========================================================
_initialized = False
client = None
data = None
questions = None
question_vectors = None
vectorizer = None

conversation_context = {
    "crop": None,
    "disease": None,
    "severity": None,
}

FOLLOW_UP_WORDS = [
    "it", "its", "this", "that", "these", "those",
    "the disease", "the plant", "the crop"
]

URDU_RANGE = "؀-ۿ"

def _is_urdu(text: str) -> bool:
    """Return True if the text contains Urdu/Arabic script characters."""
    import re
    return bool(re.search(f"[{URDU_RANGE}]", text))


def _get_api_key():
    """Get GROQ_API_KEY from env or Streamlit secrets."""
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return None


def _initialize():
    """Load dataset, build vectorizer, create Groq client. Called lazily on first ask()."""
    global _initialized, client, data, questions, question_vectors, vectorizer

    if _initialized:
        return

    from datasets import load_from_disk
    from sklearn.feature_extraction.text import TfidfVectorizer as _TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_sim
    from groq import Groq

    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Set it in Streamlit Cloud secrets or .env file."
        )
    client = Groq(api_key=api_key)

    DATASET_PATH = Path(__file__).parent / "hf_dataset"
    print("Loading plant disease dataset...")
    dataset = load_from_disk(str(DATASET_PATH))
    split_name = list(dataset.keys())[0]
    data = dataset[split_name]
    print(f"Using split: {split_name}, records: {data.num_rows}")

    questions = []
    for q in data["question"]:
        questions.append("" if q is None else str(q))

    print("Building chatbot knowledge search...")
    vectorizer = _TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))
    question_vectors = vectorizer.fit_transform(questions)
    print("Knowledge search ready!")

    _initialized = True

# =========================================================
# SYSTEM INSTRUCTIONS
# =========================================================
system_message = """You are Kisan Dost, a practical plant health assistant for Pakistani farmers.

LANGUAGE RULE (CRITICAL):
- You MUST respond in the SAME LANGUAGE the farmer uses.
- If the farmer writes in Urdu, you MUST respond entirely in Urdu script. Do not mix English words.
- If the farmer writes in English, respond in English.
- Urdu responses must use proper Urdu script (not Roman Urdu). Use everyday Urdu that a farmer would understand.
- Disease names and product names can stay in their original form if there is no common Urdu equivalent, but all explanations must be in Urdu.

Core behavior:
- Give SPECIFIC advice about the exact disease the farmer is asking about. Never give generic filler.
- Use simple, everyday language. Avoid jargon unless you explain it.
- Be direct: lead with the most actionable information first.
- When the knowledge base provides treatment dosages or product names, ALWAYS include them. Farmers need specifics.
- When SEASONAL GUIDE is provided, mention the relevant season, weather concerns, and prevention tips.
- When HOMEMADE REMEDIES are provided, share the recipe and application method — farmers appreciate low-cost solutions.
- When RECOMMENDED PRODUCTS are listed, mention the brand name, dose, and pre-harvest interval (PHI).
- Use short bullet points for readability.
- Keep answers concise but complete: 40-80 words for simple questions, up to 120 words for treatment or prevention questions.

Answer structure:
- Start with a one-line direct answer to the question.
- Then add 2-4 bullet points with specifics (dosages, timing, products).
- Include a homemade remedy if relevant.
- End with one practical tip if relevant.
- Use **bold** for headings. Leave blank lines between sections.

What to avoid:
- Do not repeat the same generic advice for different diseases. Each disease has unique treatments, causes, and symptoms. Use them.
- Do not say "consult an expert" as the only advice. Give actionable guidance first, then mention consulting if needed.
- Do not invent disease names or treatments not in the provided knowledge.
- Do not answer non-agriculture questions. Politely redirect in the farmer's language.

Conversation memory:
- Remember the disease being discussed. If the user says "it", "this disease", or "its treatment", refer to the current disease.
- If the user names a different disease, switch to that topic.
"""

# =========================================================
# SEARCH DATASET
# =========================================================
def search_dataset(user_question, top_k=3):
    """Search the dataset for relevant Q&A pairs."""
    from sklearn.metrics.pairwise import cosine_similarity

    _initialize()

    previous_disease = conversation_context.get("disease")
    previous_crop = conversation_context.get("crop")

    search_question = user_question
    if previous_disease:
        search_question += " " + str(previous_disease)
    if previous_crop:
        search_question += " " + str(previous_crop)

    user_vector = vectorizer.transform([search_question])
    similarities = cosine_similarity(user_vector, question_vectors)[0]

    if previous_disease:
        for i in range(len(similarities)):
            disease_name = str(data["disease"][i]).lower()
            if previous_disease.lower() in disease_name:
                similarities[i] += 0.20

    top_indexes = similarities.argsort()[-top_k:][::-1]

    results = []
    for index in top_indexes:
        score = similarities[index]
        record = {
            "score": float(score),
            "question": data["question"][index],
            "answer": data["answer"][index],
            "crop": data["crop"][index],
            "disease": data["disease"][index],
            "severity": data["severity"][index],
            "category": data["category"][index],
            "question_category": data["question_category"][index]
        }
        results.append(record)

    return results


def _build_knowledge_context(disease_info, user_question):
    """Build comprehensive context from disease knowledge base.

    Always includes the full disease profile so the LLM can give
    specific, varied answers instead of generic ones.
    """
    parts = []
    crop_id = disease_info.get("crop", "")
    parts.append(f"\n=== DISEASE KNOWLEDGE FOR: {disease_info['disease'].upper()} ===")
    parts.append(f"Pathogen: {disease_info['pathogen']}")

    parts.append(f"\nSymptoms:")
    for s in disease_info['symptoms']:
        parts.append(f"- {s}")

    parts.append(f"\nCauses and spread:")
    for c in disease_info['causes']:
        parts.append(f"- {c}")

    parts.append(f"\nOrganic / Biological treatments:")
    for t in disease_info['treatment_organic']:
        parts.append(f"- {t}")

    parts.append(f"\nChemical treatments:")
    for t in disease_info['treatment_chemical']:
        parts.append(f"- {t}")

    parts.append(f"\nPrevention methods:")
    for p in disease_info['prevention']:
        parts.append(f"- {p}")

    if 'severity_indicators' in disease_info:
        parts.append(f"\nSeverity levels:")
        for level, desc in disease_info['severity_indicators'].items():
            parts.append(f"- {level.capitalize()}: {desc}")

    # Add seasonal guidance for the crop
    if crop_id in CROP_SEASONAL_GUIDE:
        guide = CROP_SEASONAL_GUIDE[crop_id]
        parts.append(f"\n=== SEASONAL GUIDE FOR {crop_id.upper()} ===")
        parts.append(f"Fertilizer schedule: {guide.get('fertilizer_schedule', 'N/A')}")
        parts.append(f"Common mistakes: {guide.get('common_mistakes', 'N/A')}")
        for season, info in guide.get("seasons", {}).items():
            parts.append(f"\n{season.capitalize()} season:")
            parts.append(f"  Planting: {info.get('planting', 'N/A')}")
            parts.append(f"  Disease risks: {', '.join(info.get('disease_risks', []))}")
            parts.append(f"  Weather concerns: {info.get('weather_concerns', 'N/A')}")
            parts.append(f"  Prevention: {info.get('prevention_tips', 'N/A')}")

    # Add relevant homemade remedies
    parts.append(f"\n=== HOMEMADE REMEDIES ===")
    for remedy_name, remedy in HOMEMADE_REMEDIES.items():
        if crop_id in remedy.get("crops", []) or "all vegetables" in remedy.get("crops", []):
            parts.append(f"\n{remedy_name.replace('_', ' ').title()}:")
            parts.append(f"  Recipe: {remedy['recipe']}")
            parts.append(f"  Uses: {', '.join(remedy['uses'])}")
            parts.append(f"  Application: {remedy['application']}")

    # Add relevant pesticide/insecticide recommendations
    parts.append(f"\n=== RECOMMENDED PRODUCTS ===")
    disease_lower = disease_info['disease'].lower()
    for category, products in PESTICIDE_GUIDE.get("fungicides", {}).items():
        for product in products:
            targets = [t.lower() for t in product.get("target", [])]
            if any(disease_lower in t or t in disease_lower for t in targets) or "all fungal" in " ".join(targets):
                parts.append(f"- {product['name']} ({product['brand']}): {product['dose']}, PHI: {product['phi']}")

    parts.append(f"=== END KNOWLEDGE ===\n")
    return "\n".join(parts)


def _format_knowledge_base_answer(disease_info, user_question):
    """Format a direct, comprehensive answer from the knowledge base."""
    question_lower = user_question.lower()

    lines = []
    lines.append(f"**{disease_info['disease']}**")
    lines.append(f"*Caused by: {disease_info['pathogen']}*\n")

    is_treatment_q = any(w in question_lower for w in ['treat', 'control', 'manage', 'cure', 'spray', 'what should i do', 'help', 'remove', 'kill'])
    is_prevention_q = any(w in question_lower for w in ['prevent', 'avoid', 'protect', 'stop spread', 'stop it'])
    is_symptom_q = any(w in question_lower for w in ['symptom', 'sign', 'look', 'appear', 'identify', 'spot'])
    is_cause_q = any(w in question_lower for w in ['cause', 'why', 'how', 'reason', 'spread', 'come from'])

    answered_section = False

    if is_symptom_q:
        lines.append("**Symptoms to look for:**")
        for s in disease_info['symptoms']:
            lines.append(f"- {s}")
        answered_section = True

    if is_cause_q:
        if answered_section:
            lines.append("")
        lines.append("**What causes it:**")
        for c in disease_info['causes']:
            lines.append(f"- {c}")
        answered_section = True

    if is_treatment_q:
        if answered_section:
            lines.append("")
        lines.append("**Organic treatments:**")
        for t in disease_info['treatment_organic']:
            lines.append(f"- {t}")
        lines.append("")
        lines.append("**Chemical treatments:**")
        for t in disease_info['treatment_chemical']:
            lines.append(f"- {t}")
        answered_section = True

    if is_prevention_q:
        if answered_section:
            lines.append("")
        lines.append("**How to prevent it:**")
        for p in disease_info['prevention']:
            lines.append(f"- {p}")
        answered_section = True

    if not answered_section:
        lines.append("**Key symptoms:**")
        for s in disease_info['symptoms'][:3]:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("**First steps:**")
        lines.append(f"- {disease_info['treatment_organic'][0]}")
        lines.append(f"- {disease_info['treatment_organic'][1]}")
        lines.append("")
        lines.append("**Prevention:**")
        lines.append(f"- {disease_info['prevention'][0]}")

    lines.append("\n*Confirm product choice and dosage with your local agricultural extension officer.*")
    return "\n".join(lines)


# =========================================================
# GENERATE ANSWER USING GROQ
# =========================================================
def generate_answer(user_question, retrieved_results):
    """Generate answer using Groq API with knowledge base."""

    urdu_mode = _is_urdu(user_question)

    resolved_question = user_question

    if conversation_context["disease"]:
        question_lower = user_question.lower()
        if any(word in question_lower for word in FOLLOW_UP_WORDS):
            resolved_question = (
                f"{user_question}\n"
                f"[The user is referring to {conversation_context['disease']} "
                f"on {conversation_context['crop']}]"
            )

    # Always try to load disease knowledge base
    knowledge_context = ""
    disease_info = None
    if conversation_context["crop"] and conversation_context["disease"]:
        disease_info = get_disease_info(
            conversation_context["crop"],
            conversation_context["disease"]
        )
        if disease_info:
            knowledge_context = _build_knowledge_context(disease_info, user_question)

    # Low-confidence dataset retrieval — fall back to knowledge base directly
    if not retrieved_results or retrieved_results[0]["score"] < 0.2:
        if disease_info:
            if urdu_mode:
                kb_answer = _format_knowledge_base_answer(disease_info, user_question)
                return _translate_to_urdu(kb_answer)
            return _format_knowledge_base_answer(disease_info, user_question)
        if urdu_mode:
            return _translate_to_urdu(
                "I don't have enough information to answer this accurately. "
                "Try asking about symptoms, treatments, or prevention for your crop's disease."
            )
        return (
            "I don't have enough information to answer this accurately. "
            "Try asking about symptoms, treatments, or prevention for your crop's disease."
        )

    # Build context from retrieved dataset results
    context_parts = []
    for i, result in enumerate(retrieved_results):
        context_parts.append(
            f"SOURCE {i+1} (relevance: {result['score']:.2f})\n"
            f"Q: {result['question']}\n"
            f"A: {result['answer']}\n"
            f"Crop: {result['crop']}, Disease: {result['disease']}\n"
        )
    context = "\n---\n".join(context_parts)

    severity_note = ""
    if conversation_context.get("severity"):
        severity_note = (
            f"\nThe farmer's diagnosis shows severity: {conversation_context['severity']}. "
            f"Tailor your advice to this severity level."
        )

    lang_instruction = ""
    if urdu_mode:
        lang_instruction = (
            "\nIMPORTANT: The farmer is speaking Urdu. "
            "You MUST write your entire response in Urdu script. "
            "Do not use English. Do not mix languages.\n"
        )

    user_prompt = f"""Farmer's question: {resolved_question}
{severity_note}

Retrieved from plant disease dataset:
{context}
{knowledge_context}

Answer the farmer's question using the information above.
Prioritize the DISEASE KNOWLEDGE section for specific treatments, dosages, and prevention steps.
Be specific — include product names, dosages, and timing when available.
{lang_instruction}"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


def _translate_to_urdu(english_text: str) -> str:
    """Use Groq to translate an English answer into Urdu."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": (
                "You are a translator. Convert the following English text into "
                "natural Urdu that a Pakistani farmer would understand. "
                "Use Urdu script. Keep disease names and product names as-is "
                "if there is no common Urdu equivalent. "
                "Do not add explanations — just return the Urdu translation."
            )},
            {"role": "user", "content": english_text}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


def _translate_to_english(urdu_text: str) -> str:
    """Use Groq to translate an Urdu query into English for dataset search."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": (
                "You are a translator. Convert the following Urdu text from a "
                "Pakistani farmer into clear, simple English. Focus on the "
                "agricultural meaning — what crop, disease, symptom, or treatment "
                "they are asking about. Return ONLY the English translation, "
                "nothing else."
            )},
            {"role": "user", "content": urdu_text}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# =========================================================
# MAIN CHAT FUNCTION FOR STREAMLIT
# =========================================================
def ask(message: str, context: dict = None, history: list = None) -> str:
    """Main function for Streamlit integration."""
    _initialize()

    if context:
        if context.get("disease"):
            conversation_context["disease"] = context["disease"]
        if context.get("crop"):
            conversation_context["crop"] = context["crop"]
        if context.get("severity"):
            conversation_context["severity"] = context["severity"]

    # If the farmer speaks Urdu, translate to English for dataset search
    # so the TF-IDF matching works (dataset is in English).
    search_message = message
    if _is_urdu(message):
        try:
            search_message = _translate_to_english(message)
        except Exception:
            search_message = message

    results = search_dataset(search_message, top_k=3)

    if results:
        best = results[0]
        if best.get("disease") and not conversation_context["disease"]:
            conversation_context["disease"] = str(best["disease"])
        if best.get("crop") and not conversation_context["crop"]:
            conversation_context["crop"] = str(best["crop"])

    return generate_answer(message, results)

def reset_context():
    """Reset conversation context."""
    conversation_context["crop"] = None
    conversation_context["disease"] = None
    conversation_context["severity"] = None
