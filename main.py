import pickle
from search import search_assessments

# Load metadata (needed for filtering by test_type)
with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)


def is_greeting(message):
    greetings = [
        "hello",
        "hi",
        "hey",
        "greetings",
        "good morning",
        "good afternoon",
        "hola",
        "yo",
    ]
    return (
        message.lower().strip() in greetings
        or message.lower().strip().rstrip("!.,") in greetings
    )


def build_acronym_map(metadata):
    acronym_map = {}
    import re

    for item in metadata:
        # From name
        match = re.search(r"\(([A-Z]+)\)", item["name"])
        if match:
            acronym_map[match.group(1).lower()] = item["name"]
        # From description
        if item.get("description"):
            matches = re.findall(r"\(([A-Z]+)\)", item["description"])
            for acr in matches:
                acronym_map[acr.lower()] = item["name"]
    return acronym_map


ACRONYM_MAP = build_acronym_map(metadata)


# ------------------------------------------------------------------
# Helper: search by test_type (since your search_assessments doesn't filter)
# ------------------------------------------------------------------
def search_by_test_type(test_type_code, top_k=5):
    """Filter metadata by test_type field."""
    results = []
    for item in metadata:
        if item.get("test_type") == test_type_code:
            results.append(item)
    # Sort by name for consistency
    results = sorted(results, key=lambda x: x.get("name", ""))[:top_k]
    return results


# ------------------------------------------------------------------
# Vague query detection
# ------------------------------------------------------------------
def is_vague_first_query(message):
    msg = message.lower()
    vague_phrases = [
        "help me hire",
        "need an assessment",
        "recommend assessment",
        "hiring someone",
        "need hiring test",
    ]
    specific_keywords = [
        "java",
        "python",
        "sales",
        "healthcare",
        "excel",
        "word",
        "backend",
        "frontend",
        "aws",
        "docker",
        "sql",
        "graduate",
        "operator",
        "safety",
        "admin",
        "engineer",
        "developer",
        "nurse",
    ]
    if any(keyword in msg for keyword in specific_keywords):
        return False
    if any(phrase in msg for phrase in vague_phrases):
        return True
    if len(msg.split()) <= 4:
        return True
    return False


# ------------------------------------------------------------------
# Refinement detection
# ------------------------------------------------------------------
def is_refinement_request(message):
    msg = message.lower()
    add_phrases = ["add", "also", "actually", "in addition", "plus"]
    test_type_keywords = ["personality", "verbal", "numerical", "cognitive", "ability"]
    return any(p in msg for p in add_phrases) and any(
        t in msg for t in test_type_keywords
    )


# ------------------------------------------------------------------
# Intent detection
# ------------------------------------------------------------------
def detect_intent(messages):
    latest_content = messages[-1]["content"]

    if isinstance(latest_content, dict):
        latest = str(latest_content).lower()
    else:
        latest = latest_content.lower()

    user_turns = len([m for m in messages if m["role"] == "user"])

    # compare FIRST
    if "compare" in latest or "difference between" in latest:
        return "compare"

    # confirmation SECOND
    confirmation_phrases = [
        "looks good",
        "lock it in",
        "locked in",
        "confirm",
        "confirmed",
        "that works",
        "sounds good",
        "finalize",
        "keep this",
    ]

    if any(p in latest for p in confirmation_phrases):
        return "confirmation"

    # refusal
    off_topic_keywords = [
        "fire employee",
        "terminate employee",
        "salary dispute",
        "lawsuit",
    ]

    if any(k in latest for k in off_topic_keywords):
        return "refuse"

    # ONLY vague turn 1 after special intents checked
    if user_turns == 1:
        return "clarify"

    return "recommend"


# ------------------------------------------------------------------
# Response generators
# ------------------------------------------------------------------
def generate_clarification():
    return {
        "reply": "Could you share the role, seniority level, must-have skills, and any constraints like language requirements, assessment length, or simulation vs knowledge preferences?",
        "recommendations": [],
        "end_of_conversation": False,
    }


def generate_refusal():
    return {
        "reply": "I can help with SHL assessment recommendations, but I can't provide legal or HR policy advice.",
        "recommendations": [],
        "end_of_conversation": False,
    }


def generate_compare(messages):
    latest = messages[-1]["content"]

    # Extract assessment names: look for pattern "between X and Y"
    import re

    match = re.search(r"between (.+?) and (.+?)(?:\?|\.|$)", latest, re.IGNORECASE)
    if not match:
        return {
            "reply": "Please specify two assessments to compare, e.g., 'What is the difference between OPQ and GSA?'",
            "recommendations": [],
            "end_of_conversation": False,
        }

    name1 = match.group(1).strip()
    name2 = match.group(2).strip()

    # Search for each assessment by exact name match (fallback to partial)
    def find_assessment(name):
        name_lower = name.lower().strip()

        # 1. Exact match (case-insensitive)
        for item in metadata:
            if item["name"].lower() == name_lower:
                return item

        # 2. Partial match (name contains query or query contains name)
        for item in metadata:
            item_name_lower = item["name"].lower()
            if name_lower in item_name_lower or item_name_lower in name_lower:
                return item

        # 3. Acronym in parentheses: e.g., "GSA" appears in description as "(GSA)" or name has "(GSA)"
        # Build a map of acronym -> full name from metadata
        acronym_map = {}
        for item in metadata:
            # Check name for acronym pattern "Full Name (ACR)"
            import re

            match = re.search(r"\(([A-Z]+)\)", item["name"])
            if match:
                acronym_map[match.group(1).lower()] = item["name"]
            # Check description for "(ACR)"
            if item.get("description"):
                matches = re.findall(r"\(([A-Z]+)\)", item["description"])
                for acr in matches:
                    acronym_map[acr.lower()] = item["name"]

        if name_lower in acronym_map:
            full_name = acronym_map[name_lower]
            # Now find the item with that full name
            for item in metadata:
                if item["name"].lower() == full_name.lower():
                    return item

        # 4. Word match: treat the query as a word in name/description
        for item in metadata:
            if name_lower in item["name"].lower().split() or (
                item.get("description")
                and name_lower in item["description"].lower().split()
            ):
                return item

        return None

    a = find_assessment(name1)
    b = find_assessment(name2)

    if not a or not b:
        missing = []
        if not a:
            missing.append(name1)
        if not b:
            missing.append(name2)
        return {
            "reply": f"Could not find '{', '.join(missing)}' in the SHL catalog. Please check the names.",
            "recommendations": [],
            "end_of_conversation": False,
        }

    reply = f"""Comparison between {a['name']} and {b['name']}:

{a['name']}
- Description: {a.get('description', 'N/A')}
- Test Type: {a.get('test_type', 'N/A')}
- URL: {a['url']}

{b['name']}
- Description: {b.get('description', 'N/A')}
- Test Type: {b.get('test_type', 'N/A')}
- URL: {b['url']}
"""
    return {"reply": reply.strip(), "recommendations": [], "end_of_conversation": False}


def generate_recommendations(messages):
    # Combine all user messages for context
    user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
    results = search_assessments(user_text, top_k=10)

    # If the latest user message asks to add personality, do it here too
    latest = messages[-1]["content"].lower()
    if "personality" in latest:
        personality_tests = search_by_test_type("P", top_k=5)
        existing_names = {r["name"] for r in results}
        for p in personality_tests:
            if p["name"] not in existing_names:
                results.append(p)

    results = results[:10]
    recommendations = [
        {"name": r["name"], "url": r["url"], "test_type": r.get("test_type", "")}
        for r in results
    ]
    return {
        "reply": f"Here are {len(recommendations)} assessments that may fit your hiring needs.",
        "recommendations": recommendations,
        "end_of_conversation": False,
    }


def handle_refinement(messages):
    # Find the last assistant recommendations in history
    previous_recs = []
    for msg in reversed(messages):
        if msg["role"] == "assistant" and msg.get("recommendations"):
            previous_recs = msg["recommendations"]
            break

    if not previous_recs:
        return generate_recommendations(messages)

    last_user = messages[-1]["content"].lower()
    new_results = []

    if "personality" in last_user:
        new_results = search_by_test_type("P", top_k=5)

    # Merge, avoid duplicates by name
    existing_names = {r["name"] for r in previous_recs}
    for r in new_results:
        rec = {"name": r["name"], "url": r["url"], "test_type": r.get("test_type", "")}
        if rec["name"] not in existing_names:
            previous_recs.append(rec)

    final_recs = previous_recs[:10]
    return {
        "reply": f"Updated shortlist: added personality tests. Here are {len(final_recs)} assessments.",
        "recommendations": final_recs,
        "end_of_conversation": False,
    }


def get_last_recommendations(messages):
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            content = msg.get("content")

            if isinstance(content, dict):
                recs = content.get("recommendations", [])
                if recs:
                    return recs

    return []


# ------------------------------------------------------------------
# Main handler
# ------------------------------------------------------------------
def handle_chat(messages):
    intent = detect_intent(messages)

    if intent == "confirmation":
        recs = get_last_recommendations(messages)

        if recs:
            return {
                "reply": "Confirmed. Final shortlist locked.",
                "recommendations": recs,
                "end_of_conversation": True,
            }

        return {
            "reply": "I couldn't find a previous shortlist to confirm.",
            "recommendations": [],
            "end_of_conversation": False,
        }

    if intent == "greeting":
        return {
            "reply": "Hello! I can help you find SHL assessments. Tell me about the role, skills, or seniority level you're hiring for.",
            "recommendations": [],
            "end_of_conversation": False,
        }

    if intent == "clarify":
        return generate_clarification()
    if intent == "refinement":
        return handle_refinement(messages)
    if intent == "compare":
        return generate_compare(messages)

    if intent == "refuse":
        return generate_refusal()
    # default
    return generate_recommendations(messages)


# For local testing
if __name__ == "__main__":
    test_msgs = [
        {
            "role": "user",
            "content": "I need assessments for a data analyst role, focus on numerical reasoning.",
        },
        {
            "role": "assistant",
            "content": "Here are some...",
            "recommendations": [
                {"name": "Verify Numerical", "url": "...", "test_type": "A"}
            ],
        },
        {"role": "user", "content": "Actually, add personality tests too."},
    ]
    print(handle_chat(test_msgs))
