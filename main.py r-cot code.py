# -*- coding: utf-8 -*-
# Smart R-CoT Prompt Builder for Replit
# - Keeps your fixed R-CoT template exactly as provided
# - Infers the best sub-template/specs based on task type + topic
# - Handles ambiguity (e.g., "writing") with guided choices
# - Prints settings in BLUE and final prompt in GREEN (ANSI colors)

import difflib
import re

# ============= ANSI Colors (Replit Console) =============
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"

# ============= Task Groups & Settings (E / C) =============
task_groups = {
    "E": {
        "tasks": [
            "academic writing", "rewriting scientific text", "rewriting academic text",
            "coding explanation", "programming basics", "analytical write-ups",
            "ux critique", "technical critique"
        ],
        "settings": {
            "Temperature": 0.5,
            "Top P": 0.7,
            "Output Length (tokens)": 65536,
            "Thinking Budget": "Low = 10000",
            "Media Resolution": "Default",
            "Stop Sequences": ["END"],
            "Expected Effect": "Very accurate text, semi-formal style"
        }
    },
    "C": {
        "tasks": [
            "summarization", "brainstorming", "persuasion", "explanation",
            "creative ideation", "instruction simplification", "info structuring",
            "deep reflection", "prompt engineering", "pedagogical reasoning",
            "rational thinking", "creative writing", "story writing", "email writing",
            "copywriting", "marketing content writing", "social media post writing",
            "script writing", "blog writing", "creative email campaign"
        ],
        "settings": {
            "Temperature": 1.2,
            "Top P": 0.9,
            "Output Length (tokens)": 65536,
            "Thinking Budget": "Medium = 19149",
            "Media Resolution": "Default",
            "Stop Sequences": None,
            "Expected Effect": "Balanced between creativity and accuracy"
        }
    }
}

# ============= Synonyms & Ambiguity Handling =============
task_synonyms = {
    # Generic / ambiguous
    "write": "writing", "writing": "writing", "compose": "writing", "create": "writing",
    "draft": "writing", "produce": "writing", "generate": "writing", "craft": "writing",
    "make content": "writing", "content": "writing",

    # E
    "academic": "academic writing", "essay": "academic writing",
    "rewrite": "rewriting scientific text", "rephrase": "rewriting scientific text",
    "code explanation": "coding explanation", "explain code": "coding explanation",
    "programming": "programming basics", "ux": "ux critique",

    # C
    "summarize": "summarization", "summary": "summarization", "abstract": "summarization",
    "brainstorm": "brainstorming",
    "persuade": "persuasion",
    "explain": "explanation",
    "ideas": "creative ideation", "innovate": "creative ideation",
    "simplify": "instruction simplification",
    "organize info": "info structuring",
    "reflect": "deep reflection",
    "prompt": "prompt engineering",
    "pedagogy": "pedagogical reasoning",
    "logic": "rational thinking",
    "creative": "creative writing",
    "story": "story writing", "novel": "story writing", "narrative": "story writing",
    "email": "email writing", "mail": "email writing",
    "ad": "copywriting", "advertise": "copywriting", "ad copy": "copywriting",
    "marketing": "marketing content writing",
    "campaign": "creative email campaign",
    "social": "social media post writing", "facebook post": "social media post writing",
    "twitter": "social media post writing", "x": "social media post writing",
    "linkedin": "social media post writing", "instagram": "social media post writing",
    "tiktok": "social media post writing",
    "script": "script writing", "screenplay": "script writing",
    "blog": "blog writing"
}

ambiguous_tasks = {
    "writing": [
        "academic writing", "rewriting scientific text", "rewriting academic text",
        "creative writing", "story writing", "email writing", "copywriting",
        "marketing content writing", "social media post writing",
        "script writing", "blog writing", "creative email campaign"
    ]
}

# ============= Fixed R-CoT Template (exactly as provided) =============
RCOT_TEMPLATE = """You must follow the "Reflective Chain of Thought" (R-CoT).
Do not skip or merge steps. Stop after each step.

Task: [ {task_spec} ]

1. Understand – Restate the task in your own words, identify requirements, and clarify constraints. Stop after finishing this step.


2. Reason – Think through the solution logically and reflectively, explore multiple angles, and consider potential challenges. Stop after finishing this step.


3. Act – Provide the final output as required by the task, based only on the previous reasoning.



Strict Rule: At each step, write only the content of that step and then stop. Do not continue to the next step until explicitly asked.
"""

# ============= Utilities =============
def list_all_tasks():
    print("\nSupported Tasks:")
    for group, details in task_groups.items():
        print(f"\n{YELLOW}Group {group}:{RESET}")
        for t in details["tasks"]:
            print(f" - {t}")

def normalize(task_input: str) -> str:
    return task_synonyms.get(task_input.strip().lower(), task_input.strip().lower())

def get_task_settings(task_or_synonym):
    task_name = normalize(task_or_synonym)
    for group, details in task_groups.items():
        if task_name in details["tasks"]:
            return task_name, group, details["settings"]
    return None, None, None

def suggest(task_input):
    all_terms = list(task_synonyms.keys()) + [t for g in task_groups.values() for t in g["tasks"]]
    return difflib.get_close_matches(task_input.lower(), all_terms, n=5, cutoff=0.5)

# ============= Smart Heuristics for Task Spec =============
def contains_any(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

def detect_length_hint(topic):
    if contains_any(topic, ["one paragraph", "paragraph", "short", "brief", "150 words"]):
        return "Length: one concise paragraph (~120–180 words)."
    if contains_any(topic, ["abstract", "executive summary"]):
        return "Length: abstract (150–250 words)."
    if contains_any(topic, ["report", "comprehensive", "long", "in-depth", "extensive"]):
        return "Length: in-depth (600–900 words)."
    return "Length: appropriate and concise."

def pick_framework(task_name, topic):
    # Choose the best-known writing/logical framework for the task+topic
    if task_name == "copywriting" or task_name == "marketing content writing":
        if contains_any(topic, ["problem", "pain", "struggle", "issue", "friction"]):
            return "Framework: PAS (Problem–Agitate–Solution)."
        if contains_any(topic, ["launch", "new", "introduc", "campaign", "offer", "sale"]):
            return "Framework: AIDA (Attention–Interest–Desire–Action)."
        return "Framework: AIDA (Attention–Interest–Desire–Action)."

    if task_name in ["social media post writing"]:
        if contains_any(topic, ["linkedin"]):
            return "Platform: LinkedIn. Style: professional, insight-driven, value first."
        if contains_any(topic, ["twitter", "x"]):
            return "Platform: Twitter/X. Style: crisp hook + thread (3–5 tweets)."
        if contains_any(topic, ["instagram"]):
            return "Platform: Instagram. Style: caption + 5–7 hashtags."
        if contains_any(topic, ["tiktok"]):
            return "Platform: TikTok. Style: hook in first 2 seconds + CTA."
        return "Platform: platform-agnostic. Style: clear hook + value + CTA."

    if task_name == "email writing":
        if contains_any(topic, ["complaint", "issue", "refund"]):
            return "Email Type: Complaint/Resolution. Tone: firm yet polite. CTA: resolution timeline."
        if contains_any(topic, ["application", "job", "cv", "resume"]):
            return "Email Type: Job Application. Tone: professional. Structure: intro–fit–evidence–CTA."
        if contains_any(topic, ["follow up", "follow-up", "reminder"]):
            return "Email Type: Follow-up. Tone: polite. Structure: context–value–clear ask."
        if contains_any(topic, ["intro", "introduction", "outreach", "partnership"]):
            return "Email Type: Outreach/Introduction. Tone: warm, concise. CTA: short call."
        return "Email Type: Professional. Tone: concise and courteous. Clear subject + CTA."

    if task_name == "blog writing":
        if contains_any(topic, ["how to", "how-to", "guide", "tutorial"]):
            return "Blog Format: How-to Guide with steps, tips, and examples."
        if contains_any(topic, ["top ", "best", "list", "roundup"]):
            return "Blog Format: Listicle with ranked items and brief justifications."
        if contains_any(topic, ["vs", "versus", "compare", "comparison"]):
            return "Blog Format: Comparative analysis with criteria table."
        return "Blog Format: Standard article with intro–body–conclusion."

    if task_name in ["script writing"]:
        if contains_any(topic, ["ad", "advertisement", "promo", "commercial"]):
            return "Script Type: 30–60s ad. Structure: hook–problem–benefit–CTA."
        if contains_any(topic, ["youtube", "explainer", "video", "shorts"]):
            return "Script Type: YouTube explainer. Structure: hook (0–10s)–sections–recap–CTA."
        return "Script Type: Narrative script with scenes, dialogue, and pacing."

    if task_name in ["creative writing", "story writing"]:
        if contains_any(topic, ["sci-fi", "science fiction", "cyberpunk", "space"]):
            return "Genre: Sci-Fi. Focus: world-building, plausible tech, character motivation."
        if contains_any(topic, ["mystery", "thriller", "detective"]):
            return "Genre: Mystery/Thriller. Focus: clues, red herrings, rising tension."
        if contains_any(topic, ["fantasy", "myth", "magic"]):
            return "Genre: Fantasy. Focus: lore, stakes, character arcs."
        return "Genre: Literary. Focus: imagery, voice, and character interiority."

    if task_name == "summarization":
        if contains_any(topic, ["paper", "study", "research", "journal", "systematic review"]):
            return "Summary Type: Structured (Objective–Methods–Findings–Limitations–Implications)."
        return "Summary Type: Bullet-point key takeaways (5–7 bullets)."

    if task_name in ["explanation", "coding explanation", "programming basics"]:
        if contains_any(topic, ["algorithm", "complexity", "big-o", "time", "space"]):
            return "Explainer Mode: Step-by-step with annotated pseudocode + Big-O analysis."
        if contains_any(topic, ["bug", "error", "debug"]):
            return "Explainer Mode: Debugging guide with hypothesis–tests–fix–verification."
        return "Explainer Mode: Concept breakdown with analogy + minimal runnable example."

    if task_name in ["academic writing", "rewriting scientific text", "rewriting academic text", "analytical write-ups"]:
        if contains_any(topic, ["literature review", "survey", "systematic", "meta-analysis"]):
            return "Structure: Formal academic style with literature synthesis and proper citations (APA 7th)."
        if contains_any(topic, ["proposal", "methodology", "methods"]):
            return "Structure: Aim–Background–Methods–Expected Results–Limitations."
        if contains_any(topic, ["paragraph", "short", "brief"]):
            return "Structure: One paragraph with thesis + evidence + micro-conclusion."
        return "Structure: Introduction–Argumentation–Conclusion with cautious, hedged claims."

    if task_name in ["ux critique", "technical critique"]:
        return "Critique Mode: Heuristics (Nielsen) + severity ratings + prioritized recommendations."

    if task_name in ["brainstorming", "creative ideation"]:
        return "Ideation Mode: 12 ideas grouped in 3 themes; each idea with one-line rationale."

    if task_name in ["info structuring", "instruction simplification", "pedagogical reasoning", "rational thinking", "deep reflection", "persuasion", "prompt engineering"]:
        return "Mode: Clear headings, numbered steps, and evidence-backed rationale."

    return "Mode: Best-practice structure for the task."

def academic_style_prefs(task_name):
    # Additional style directives (folded into the Task line)
    if task_name in ["academic writing", "rewriting scientific text", "rewriting academic text", "analytical write-ups"]:
        return "Style: academic English, objective tone, precise terminology, avoid first-person; cite if sources are referenced."
    if task_name in ["coding explanation", "programming basics", "explanation"]:
        return "Style: clear technical English, minimal jargon, examples first, definitions precise."
    if task_name in ["summarization"]:
        return "Style: neutral, concise, faithful to source; no new claims."
    if task_name in ["copywriting", "marketing content writing", "social media post writing", "creative email campaign"]:
        return "Style: persuasive, audience-aware, crisp CTAs, avoid fluff."
    if task_name in ["email writing"]:
        return "Style: professional, courteous, direct subject lines."
    if task_name in ["blog writing"]:
        return "Style: informative, scannable subheadings, short paragraphs."
    if task_name in ["script writing", "story writing", "creative writing"]:
        return "Style: vivid, voice-driven, show-don’t-tell."
    return "Style: clear and coherent."

def build_task_spec(task_name, topic):
    """Compose a single, rich Task line for your fixed R-CoT template."""
    length_hint = detect_length_hint(topic)
    framework = pick_framework(task_name, topic)
    style = academic_style_prefs(task_name)

    # Tighten language for the Task bracket; keep everything in one line.
    # Example: Task: [ Academic Writing — Topic: AI in healthcare — Structure: ... — Length: ... — Style: ... ]
    parts = [
        task_name.title(),
        f"Topic: {topic}",
        framework,
        length_hint,
        style
    ]
    return " — ".join(parts)

# ============= Main Interactive Flow =============
print(f"{YELLOW}=== Reflective Chain-of-Thought (R-CoT) Selector ==={RESET}")
print("Type 'list' to see all supported tasks.\n")

user_input = input("Enter the task name: ").strip()
if user_input.lower() == "list":
    list_all_tasks()
    exit()

# Resolve or clarify task
task_name, group, settings = get_task_settings(user_input)
if not group:
    norm = normalize(user_input)
    if norm in ambiguous_tasks:
        print(f"\n{YELLOW}Your input is too general. Possible options:{RESET}")
        for i, opt in enumerate(ambiguous_tasks[norm], 1):
            print(f"{i}. {opt}")
        choice = input("\nEnter the number of the correct task: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ambiguous_tasks[norm]):
            chosen = ambiguous_tasks[norm][int(choice) - 1]
            task_name, group, settings = get_task_settings(chosen)
        else:
            print(f"{RED}No valid selection. Exiting.{RESET}")
            exit()
    else:
        suggestions = suggest(user_input)
        if suggestions:
            print(f"{YELLOW}Did you mean:{RESET}")
            for i, s in enumerate(suggestions, 1):
                print(f"{i}. {s}")
            choice = input("\nEnter the number of the correct task (or press Enter to cancel): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                selected = suggestions[int(choice) - 1]
                task_name, group, settings = get_task_settings(selected)
            else:
                print(f"{RED}No task selected. Exiting.{RESET}")
                exit()
        else:
            print(f"{RED}No similar tasks found. Type 'list' to view supported tasks.{RESET}")
            exit()

# Ask for topic when relevant
topic = ""
if task_name and ("writing" in task_name or task_name in [
    "summarization", "explanation", "brainstorming", "persuasion",
    "creative ideation", "instruction simplification", "info structuring",
    "deep reflection", "prompt engineering", "pedagogical reasoning",
    "rational thinking", "coding explanation", "programming basics",
    "analytical write-ups", "ux critique", "technical critique"
]):
    topic = input("\nWhat topic do you want to write about? ").strip()
    while not topic:
        topic = input("Please enter a valid topic: ").strip()

# Display settings
print(f"\n{YELLOW}Task Selected:{RESET} {task_name}")
print(f"{YELLOW}Group:{RESET} {group}")
print(f"\n{BLUE}Optimal Settings:{RESET}")
for k, v in settings.items():
    print(f"{BLUE}- {k}: {v}{RESET}")

# Build smart task spec and final prompt
task_spec = build_task_spec(task_name, topic if topic else "(no explicit topic)")
final_prompt = RCOT_TEMPLATE.format(task_spec=task_spec)

print(f"\n{GREEN}Generated R-CoT Prompt:{RESET}")
print(f"{GREEN}{final_prompt}{RESET}")
    if task_name in ["script writing"]:
        if contains_any(topic, ["ad", "advertisement", "promo", "commercial"]):
            return "Script Type: 30–60s ad. Structure: hook–problem–benefit–CTA."
        if contains_any(topic, ["youtube", "explainer", "video", "shorts"]):
            return "Script Type: YouTube explainer. Structure: hook (0–10s)–sections–recap–CTA."
        return "Script Type: Narrative script with scenes, dialogue, and pacing."

    if task_name in ["creative writing", "story writing"]:
        if contains_any(topic, ["sci-fi", "science fiction", "cyberpunk", "space"]):
            return "Genre: Sci-Fi. Focus: world-building, plausible tech, character motivation."
        if contains_any(topic, ["mystery", "thriller", "detective"]):
            return "Genre: Mystery/Thriller. Focus: clues, red herrings, rising tension."
        if contains_any(topic, ["fantasy", "myth", "magic"]):
            return "Genre: Fantasy. Focus: lore, stakes, character arcs."
        return "Genre: Literary. Focus: imagery, voice, and character interiority."

    if task_name == "summarization":
        if contains_any(topic, ["paper", "study", "research", "journal", "systematic review"]):
            return "Summary Type: Structured (Objective–Methods–Findings–Limitations–Implications)."
        return "Summary Type: Bullet-point key takeaways (5–7 bullets)."

    if task_name in ["explanation", "coding explanation", "programming basics"]:
        if contains_any(topic, ["algorithm", "complexity", "big-o", "time", "space"]):
            return "Explainer Mode: Step-by-step with annotated pseudocode + Big-O analysis."
        if contains_any(topic, ["bug", "error", "debug"]):
            return "Explainer Mode: Debugging guide with hypothesis–tests–fix–verification."
        return "Explainer Mode: Concept breakdown with analogy + minimal runnable example."

    if task_name in ["academic writing", "rewriting scientific text", "rewriting academic text", "analytical write-ups"]:
        if contains_any(topic, ["literature review", "survey", "systematic", "meta-analysis"]):
            return "Structure: Formal academic style with literature synthesis and proper citations (APA 7th)."
        if contains_any(topic, ["proposal", "methodology", "methods"]):
            return "Structure: Aim–Background–Methods–Expected Results–Limitations."
        if contains_any(topic, ["paragraph", "short", "brief"]):
            return "Structure: One paragraph with thesis + evidence + micro-conclusion."
        return "Structure: Introduction–Argumentation–Conclusion with cautious, hedged claims."

    if task_name in ["ux critique", "technical critique"]:
        return "Critique Mode: Heuristics (Nielsen) + severity ratings + prioritized recommendations."

    if task_name in ["brainstorming", "creative ideation"]:
        return "Ideation Mode: 12 ideas grouped in 3 themes; each idea with one-line rationale."

    if task_name in ["info structuring", "instruction simplification", "pedagogical reasoning", "rational thinking", "deep reflection", "persuasion", "prompt engineering"]:
        return "Mode: Clear headings, numbered steps, and evidence-backed rationale."

    return "Mode: Best-practice structure for the task."

def academic_style_prefs(task_name):
    # Additional style directives (folded into the Task line)
    if task_name in ["academic writing", "rewriting scientific text", "rewriting academic text", "analytical write-ups"]:
        return "Style: academic English, objective tone, precise terminology, avoid first-person; cite if sources are referenced."
    if task_name in ["coding explanation", "programming basics", "explanation"]:
        return "Style: clear technical English, minimal jargon, examples first, definitions precise."
    if task_name in ["summarization"]:
        return "Style: neutral, concise, faithful to source; no new claims."
    if task_name in ["copywriting", "marketing content writing", "social media post writing", "creative email campaign"]:
        return "Style: persuasive, audience-aware, crisp CTAs, avoid fluff."
    if task_name in ["email writing"]:
        return "Style: professional, courteous, direct subject lines."
    if task_name in ["blog writing"]:
        return "Style: informative, scannable subheadings, short paragraphs."
    if task_name in ["script writing", "story writing", "creative writing"]:
        return "Style: vivid, voice-driven, show-don’t-tell."
    return "Style: clear and coherent."

def build_task_spec(task_name, topic):
    """Compose a single, rich Task line for your fixed R-CoT template."""
    length_hint = detect_length_hint(topic)
    framework = pick_framework(task_name, topic)
    style = academic_style_prefs(task_name)

    # Tighten language for the Task bracket; keep everything in one line.
    # Example: Task: [ Academic Writing — Topic: AI in healthcare — Structure: ... — Length: ... — Style: ... ]
    parts = [
        task_name.title(),
        f"Topic: {topic}",
        framework,
        length_hint,
        style
    ]
    return " — ".join(parts)

# ============= Main Interactive Flow =============
print(f"{YELLOW}=== Reflective Chain-of-Thought (R-CoT) Selector ==={RESET}")
print("Type 'list' to see all supported tasks.\n")

user_input = input("Enter the task name: ").strip()
if user_input.lower() == "list":
    list_all_tasks()
    exit()

# Resolve or clarify task
task_name, group, settings = get_task_settings(user_input)
if not group:
    norm = normalize(user_input)
    if norm in ambiguous_tasks:
        print(f"\n{YELLOW}Your input is too general. Possible options:{RESET}")
        for i, opt in enumerate(ambiguous_tasks[norm], 1):
            print(f"{i}. {opt}")
        choice = input("\nEnter the number of the correct task: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ambiguous_tasks[norm]):
            chosen = ambiguous_tasks[norm][int(choice) - 1]
            task_name, group, settings = get_task_settings(chosen)
        else:
            print(f"{RED}No valid selection. Exiting.{RESET}")
            exit()
    else:
        suggestions = suggest(user_input)
        if suggestions:
            print(f"{YELLOW}Did you mean:{RESET}")
            for i, s in enumerate(suggestions, 1):
                print(f"{i}. {s}")
            choice = input("\nEnter the number of the correct task (or press Enter to cancel): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                selected = suggestions[int(choice) - 1]
                task_name, group, settings = get_task_settings(selected)
            else:
                print(f"{RED}No task selected. Exiting.{RESET}")
                exit()
        else:
            print(f"{RED}No similar tasks found. Type 'list' to view supported tasks.{RESET}")
            exit()

# Ask for topic when relevant
topic = ""
if task_name and ("writing" in task_name or task_name in [
    "summarization", "explanation", "brainstorming", "persuasion",
    "creative ideation", "instruction simplification", "info structuring",
    "deep reflection", "prompt engineering", "pedagogical reasoning",
    "rational thinking", "coding explanation", "programming basics",
    "analytical write-ups", "ux critique", "technical critique"
]):
    topic = input("\nWhat topic do you want to write about? ").strip()
    while not topic:
        topic = input("Please enter a valid topic: ").strip()

# Display settings
print(f"\n{YELLOW}Task Selected:{RESET} {task_name}")
print(f"{YELLOW}Group:{RESET} {group}")
print(f"\n{BLUE}Optimal Settings:{RESET}")
for k, v in settings.items():
    print(f"{BLUE}- {k}: {v}{RESET}")

# Build smart task spec and final prompt
task_spec = build_task_spec(task_name, topic if topic else "(no explicit topic)")
final_prompt = RCOT_TEMPLATE.format(task_spec=task_spec)

print(f"\n{GREEN}Generated R-CoT Prompt:{RESET}")
print(f"{GREEN}{final_prompt}{RESET}")