"""
PlantCare AI - Plant Disease Chatbot Assistant

Uses TF-IDF search over a plant disease dataset and Groq API (GPT model)
to answer user questions about plant diseases, symptoms, prevention, and treatment.
"""

import os
from pathlib import Path
from datasets import load_from_disk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from groq import Groq

# =========================================================
# 1. LOAD ENVIRONMENT VARIABLES
# =========================================================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found. Please set it in your .env file."
    )

client = Groq(api_key=api_key)

# =========================================================
# 2. LOAD HUGGING FACE DATASET
# =========================================================
DATASET_PATH = Path(__file__).parent / "hf_dataset"

print("Loading plant disease dataset...")
dataset = load_from_disk(str(DATASET_PATH))

# Get first available split
split_name = list(dataset.keys())[0]
data = dataset[split_name]

print(f"Using split: {split_name}")
print(f"Number of records: {data.num_rows}")

# =========================================================
# 3. GET QUESTIONS FROM DATASET
# =========================================================
questions = []
for question in data["question"]:
    if question is None:
        questions.append("")
    else:
        questions.append(str(question))

# =========================================================
# 4. CREATE TF-IDF SEARCH ENGINE
# =========================================================
print("Building chatbot knowledge search...")

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2)
)

question_vectors = vectorizer.fit_transform(questions)
print("Knowledge search ready!")

# =========================================================
# 5. CONVERSATION CONTEXT
# =========================================================
conversation_context = {
    "crop": None,
    "disease": None
}

# Follow-up question indicators
FOLLOW_UP_WORDS = [
    "it", "its", "this", "that", "these", "those",
    "the disease", "the plant", "the crop"
]

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
    
    # Get current memory
    previous_disease = conversation_context.get("disease")
    previous_crop = conversation_context.get("crop")
    
    # Build search question with context
    search_question = user_question
    if previous_disease:
        search_question += " " + str(previous_disease)
    if previous_crop:
        search_question += " " + str(previous_crop)
    
    # TF-IDF search
    user_vector = vectorizer.transform([search_question])
    similarities = cosine_similarity(user_vector, question_vectors)[0]
    
    # Boost results matching current disease
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

# =========================================================
# 8. GENERATE ANSWER USING GROQ
# =========================================================
def generate_answer(user_question, retrieved_results):
    """Generate answer using Groq API."""
    
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
    # Update conversation context from diagnosis if provided
    if context:
        if context.get("disease") and not conversation_context["disease"]:
            conversation_context["disease"] = context["disease"]
        if context.get("crop") and not conversation_context["crop"]:
            conversation_context["crop"] = context["crop"]
    
    # Search dataset
    results = search_dataset(message, top_k=3)
    
    # Update conversation context from search results
    if results:
        best_result = results[0]
        disease = best_result.get("disease")
        crop = best_result.get("crop")
        
        if disease and not conversation_context["disease"]:
            conversation_context["disease"] = str(disease)
        if crop and not conversation_context["crop"]:
            conversation_context["crop"] = str(crop)
    
    # Generate answer
    answer = generate_answer(message, results)
    
    return answer

def reset_context():
    """Reset conversation context."""
    conversation_context["crop"] = None
    conversation_context["disease"] = None
