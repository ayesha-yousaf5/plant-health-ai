"""
PlantCare AI - Plant Disease Chatbot Assistant

Uses TF-IDF search over a plant disease dataset and Groq API (GPT model)
to answer user questions about plant diseases, symptoms, prevention, and treatment.
"""

import os
from pathlib import Path
from chatbot.disease_knowledge import get_disease_info, get_treatment_info, get_crop_diseases

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
    "disease": None
}

FOLLOW_UP_WORDS = [
    "it", "its", "this", "that", "these", "those",
    "the disease", "the plant", "the crop"
]


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
# 6. SYSTEM INSTRUCTIONS
# =========================================================
system_message = """
You are PlantCare AI, a friendly and practical plant health assistant
designed especially for farmers.

Your job is to help users with:
- Plant diseases
- Plant symptoms
- Disease causes
- Disease severity
- Disease prevention
- Disease management
- Crop health
- Basic plant care

IMPORTANT RULES:

1. Use the retrieved dataset information as your main source.
2. Do not invent disease names, symptoms, severity levels, treatments,
   or other agricultural information.
3. If the retrieved information is not sufficient, clearly say:
   "The available dataset does not contain enough information to answer
   this question accurately."
4. Keep answers SHORT and useful.
5. Normally answer in about 20–50 words.
6. Use simple language that a farmer can easily understand.
7. Avoid unnecessary technical terms.
8. Do not give long explanations unless the user asks for more detail.
9. Give the most important information first.
10. Use short bullet points when they make the answer easier to understand.
11. Be friendly, clear, and practical.
12. Format answers clearly using Markdown.
13. Put every heading on its own line and make headings bold.
14. Use bullet points for lists.
15. Leave a blank line between different sections.
16. Keep answers short and easy to read.
17. Do not write the entire answer as one large paragraph.

IMPORTANT ANSWER FORMAT:

Always organize your answer into clearly separated sections.

For every heading:
- Put the heading on its own line.
- Make the heading bold using Markdown.
- Leave a blank line before and after the heading.
- Do not put the heading and its explanation on the same line.

For lists:
- Put EVERY item on a separate line.
- Use "- " before every item.
- Never put multiple bullet points on one line.

When answering multiple parts of a question, create a separate
heading for each part.

Example:

**Apple Scab**

Apple scab is a fungal disease that affects apple trees.

**Symptoms**

- Olive-green spots appear on leaves.
- Dark scabs may appear on fruit.
- Leaves may fall early.

**Causes**

Apple scab is caused by a fungus that spreads in wet conditions.

**Prevention**

- Remove infected leaves.
- Keep good airflow around the tree.

Keep answers short, normally 20–50 words.
Use simple language suitable for farmers.

If the user asks questions unrelated to agriculture or plant health, say:

"I'm PlantCare AI, a plant health assistant. I can only help with
plant diseases, symptoms, prevention, severity, and plant care."

CONVERSATION MEMORY:

Remember the main plant disease being discussed.

If the user uses words such as:
"it", "this disease", "this plant", "its symptoms", "its causes",
"its prevention", "its treatment"

understand that they are referring to the disease currently
being discussed in the conversation.

For example:

User: What is Apple Scab?
Assistant: [answer]

User: What are its causes?
Assistant: Answer about Apple Scab.

If the user clearly names a different disease, switch the
conversation topic to that disease.

Do not answer unrelated questions.
"""

# =========================================================
# 7. SEARCH DATASET
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
    """Build context string from disease knowledge base based on question."""
    question_lower = user_question.lower()
    
    context_parts = []
    context_parts.append(f"\n=== DETAILED DISEASE KNOWLEDGE BASE ===")
    context_parts.append(f"Disease: {disease_info['disease']}")
    context_parts.append(f"Pathogen: {disease_info['pathogen']}")
    
    # Always include symptoms
    context_parts.append(f"\nSymptoms:")
    for symptom in disease_info['symptoms']:
        context_parts.append(f"- {symptom}")
    
    # Include causes
    context_parts.append(f"\nCauses:")
    for cause in disease_info['causes']:
        context_parts.append(f"- {cause}")
    
    # Include treatments based on question
    if any(word in question_lower for word in ['treat', 'control', 'manage', 'cure', 'spray', 'chemical', 'organic', 'pesticide', 'fungicide']):
        context_parts.append(f"\nOrganic/Biological Treatments:")
        for treatment in disease_info['treatment_organic']:
            context_parts.append(f"- {treatment}")
        
        context_parts.append(f"\nChemical Treatments:")
        for treatment in disease_info['treatment_chemical']:
            context_parts.append(f"- {treatment}")
    
    # Include prevention
    if any(word in question_lower for word in ['prevent', 'avoid', 'protect', 'stop', 'reduce risk']):
        context_parts.append(f"\nPrevention Methods:")
        for prevention in disease_info['prevention']:
            context_parts.append(f"- {prevention}")
    
    # Include severity indicators if severity is mentioned
    if any(word in question_lower for word in ['severe', 'mild', 'moderate', 'stage', 'level']):
        if 'severity_indicators' in disease_info:
            context_parts.append(f"\nSeverity Indicators:")
            for level, description in disease_info['severity_indicators'].items():
                context_parts.append(f"- {level.capitalize()}: {description}")
    
    context_parts.append(f"\n=== END KNOWLEDGE BASE ===\n")
    
    return "\n".join(context_parts)


def _format_knowledge_base_answer(disease_info, user_question):
    """Format a direct answer from knowledge base when dataset retrieval fails."""
    question_lower = user_question.lower()
    
    answer_parts = []
    answer_parts.append(f"**{disease_info['disease']}**")
    answer_parts.append(f"*Pathogen: {disease_info['pathogen']}*\n")
    
    # Provide relevant information based on question
    if any(word in question_lower for word in ['symptom', 'sign', 'look', 'appear', 'identify']):
        answer_parts.append("**Symptoms:**")
        for symptom in disease_info['symptoms']:
            answer_parts.append(f"- {symptom}")
    
    if any(word in question_lower for word in ['cause', 'why', 'how', 'reason', 'spread']):
        answer_parts.append("\n**Causes:**")
        for cause in disease_info['causes']:
            answer_parts.append(f"- {cause}")
    
    if any(word in question_lower for word in ['treat', 'control', 'manage', 'cure', 'spray', 'what should i do', 'help']):
        answer_parts.append("\n**Organic Treatments:**")
        for treatment in disease_info['treatment_organic']:
            answer_parts.append(f"- {treatment}")
        
        answer_parts.append("\n**Chemical Treatments:**")
        for treatment in disease_info['treatment_chemical']:
            answer_parts.append(f"- {treatment}")
    
    if any(word in question_lower for word in ['prevent', 'avoid', 'protect', 'stop spread']):
        answer_parts.append("\n**Prevention:**")
        for prevention in disease_info['prevention']:
            answer_parts.append(f"- {prevention}")
    
    # If no specific keywords, provide a general overview
    if not any(word in question_lower for word in ['symptom', 'cause', 'treat', 'prevent', 'control', 'manage']):
        answer_parts.append("\n**Key Information:**")
        answer_parts.append(f"\n*Symptoms:* {', '.join(disease_info['symptoms'][:2])}")
        answer_parts.append(f"\n*Main Treatment:* {disease_info['treatment_organic'][0]}")
        answer_parts.append(f"\n*Prevention:* {disease_info['prevention'][0]}")
    
    answer_parts.append("\n\n*This is general management guidance. Confirm product choice and dosage with a local agricultural extension officer before applying anything.*")
    
    return "\n".join(answer_parts)


# =========================================================
# 8. GENERATE ANSWER USING GROQ
# =========================================================
def generate_answer(user_question, retrieved_results):
    """Generate answer using Groq API with enhanced knowledge base."""
    
    # Resolve follow-up questions
    resolved_question = user_question
    question_lower = user_question.lower()
    
    if conversation_context["disease"]:
        # Check if user is referring to current disease
        if any(word in f" {question_lower} " for word in [" it ", " its "]):
            resolved_question = (
                f"{user_question}\n\n"
                f"IMPORTANT CONTEXT: The user is referring to the plant disease "
                f"'{conversation_context['disease']}'."
            )
        
        if any(word in question_lower for word in FOLLOW_UP_WORDS):
            resolved_question = (
                f"{user_question} "
                f"The user is referring to {conversation_context['disease']}."
            )
    
    # Check if we have sufficient information
    if retrieved_results and retrieved_results[0]["score"] < 0.2:
        # Try to use knowledge base even if dataset retrieval failed
        if conversation_context["crop"] and conversation_context["disease"]:
            disease_info = get_disease_info(
                conversation_context["crop"],
                conversation_context["disease"]
            )
            if disease_info:
                return _format_knowledge_base_answer(disease_info, user_question)
        
        return (
            "I don't have enough information in my plant disease "
            "dataset to answer this question accurately."
        )
    
    # Build context from retrieved results
    context = ""
    for i, result in enumerate(retrieved_results):
        context += f"""
SOURCE {i + 1}

Question:
{result["question"]}

Answer:
{result["answer"]}

Crop:
{result["crop"]}

Disease:
{result["disease"]}

Severity:
{result["severity"]}

Category:
{result["category"]}

Question Category:
{result["question_category"]}

Similarity:
{result["score"]}

--------------------------------
"""
    
    # Add disease knowledge base information if available
    knowledge_context = ""
    if conversation_context["crop"] and conversation_context["disease"]:
        disease_info = get_disease_info(
            conversation_context["crop"],
            conversation_context["disease"]
        )
        if disease_info:
            knowledge_context = _build_knowledge_context(disease_info, user_question)
    
    # Add topic information if we have a current topic
    current_topic = conversation_context["disease"]
    if current_topic:
        topic_information = f"""
The current conversation is about:
{current_topic}

If the user uses words such as "it", "this disease",
"this plant", "its symptoms", or "its treatment",
understand that they are referring to the current topic.
"""
    else:
        topic_information = ""
    
    # Build user prompt
    user_prompt = f"""
User question:

{resolved_question}

{topic_information}

Relevant information retrieved from the
plant disease dataset:

{context}

{knowledge_context}

Using the retrieved information, answer
the user's question clearly and accurately.

If the user is asking a follow-up question,
use the current conversation topic to understand
what they are referring to.

Keep the answer short, simple, and suitable
for farmers.
"""
    
    # Groq API call
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2
    )
    
    return response.choices[0].message.content

# =========================================================
# 9. MAIN CHAT FUNCTION FOR STREAMLIT
# =========================================================
def ask(message: str, context: dict = None, history: list = None) -> str:
    """
    Main function for Streamlit integration.

    Args:
        message: User's question
        context: Diagnosis context (crop, disease, severity, etc.)
        history: Conversation history (not used currently)

    Returns:
        AI response string
    """
    _initialize()

    if context:
        if context.get("disease") and not conversation_context["disease"]:
            conversation_context["disease"] = context["disease"]
        if context.get("crop") and not conversation_context["crop"]:
            conversation_context["crop"] = context["crop"]

    results = search_dataset(message, top_k=3)

    if results:
        best_result = results[0]
        disease = best_result.get("disease")
        crop = best_result.get("crop")

        if disease and not conversation_context["disease"]:
            conversation_context["disease"] = str(disease)
        if crop and not conversation_context["crop"]:
            conversation_context["crop"] = str(crop)

    answer = generate_answer(message, results)

    return answer

def reset_context():
    """Reset conversation context."""
    conversation_context["crop"] = None
    conversation_context["disease"] = None
