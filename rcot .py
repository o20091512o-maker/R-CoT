# -- coding: utf-8 --
# Prototype Notice:
# This code is a prototype to demonstrate the idea of task selection and automatic prompt setup.
# It currently covers only a subset of common tasks and is intended for demonstration purposes.
# TODO: Add more tasks and patterns in future versions.
# Smart R-CoT Prompt Builder
# - Keeps your fixed R-CoT template exactly as provided
# - Infers the best sub-template/specs based on task type + topic
# - Handles ambiguity (e.g., "writing") with guided choices
# - Prints settings in BLUE and final prompt in GREEN (ANSI colors)
# - v2: Added type hints, docstrings, sys.exit(), KeyboardInterrupt handling,
#         task-name constants, needs_topic() helper, task-aware length hints,
#         and BOLD headers.

import difflib
import sys

# ============= ANSI Colors (Console) =============
RESET  = "\033[0m"
BOLD   = "\033[1m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
RED    = "\033[91m"

# ============= Task Name Constants =============
# Centralised strings — edit here once instead of hunting magic strings.
T_ACADEMIC_WRITING        = "academic writing"
T_REWRITING_SCIENTIFIC    = "rewriting scientific text"
T_REWRITING_ACADEMIC      = "rewriting academic text"
T_CODING_EXPLANATION      = "coding explanation"
T_PROGRAMMING_BASICS      = "programming basics"
T_ANALYTICAL_WRITEUPS     = "analytical write-ups"
T_UX_CRITIQUE             = "ux critique"
T_TECHNICAL_CRITIQUE      = "technical critique"
T_SUMMARIZATION           = "summarization"
T_BRAINSTORMING           = "brainstorming"
T_PERSUASION              = "persuasion"
T_EXPLANATION             = "explanation"
T_CREATIVE_IDEATION       = "creative ideation"
T_INSTRUCTION_SIMPLIFY    = "instruction simplification"
T_INFO_STRUCTURING        = "info structuring"
T_DEEP_REFLECTION         = "deep reflection"
T_PROMPT_ENGINEERING      = "prompt engineering"
T_PEDAGOGICAL_REASONING   = "pedagogical reasoning"
T_RATIONAL_THINKING       = "rational thinking"
T_CREATIVE_WRITING        = "creative writing"
T_STORY_WRITING           = "story writing"
T_EMAIL_WRITING           = "email writing"
T_COPYWRITING             = "copywriting"
T_MARKETING_CONTENT       = "marketing content writing"
T_SOCIAL_MEDIA_POST       = "social media post writing"
T_SCRIPT_WRITING          = "script writing"
T_BLOG_WRITING            = "blog writing"
T_CREATIVE_EMAIL_CAMPAIGN = "creative email campaign"

# ============= Task Groups & Settings (E / C) =============
task_groups = {
    "E": {
        "tasks": [
            T_ACADEMIC_WRITING, T_REWRITING_SCIENTIFIC,
            T_REWRITING_ACADEMIC, T_CODING_EXPLANATION,
            T_PROGRAMMING_BASICS, T_ANALYTICAL_WRITEUPS,
            T_UX_CRITIQUE, T_TECHNICAL_CRITIQUE
        ],
        "needs_topic": True,
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
            T_SUMMARIZATION, T_BRAINSTORMING, T_PERSUASION, T_EXPLANATION,
            T_CREATIVE_IDEATION, T_INSTRUCTION_SIMPLIFY,
            T_INFO_STRUCTURING, T_DEEP_REFLECTION, T_PROMPT_ENGINEERING,
            T_PEDAGOGICAL_REASONING, T_RATIONAL_THINKING, T_CREATIVE_WRITING,
            T_STORY_WRITING, T_EMAIL_WRITING, T_COPYWRITING,
            T_MARKETING_CONTENT, T_SOCIAL_MEDIA_POST,
            T_SCRIPT_WRITING, T_BLOG_WRITING, T_CREATIVE_EMAIL_CAMPAIGN
        ],
        "needs_topic": True,
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
    "write":        "writing",
    "writing":      "writing",
    "compose":      "writing",
    "create":       "writing",
    "draft":        "writing",
    "produce":      "writing",
    "generate":     "writing",
    "craft":        "writing",
    "make content": "writing",
    "content":      "writing",

    # E group
    "academic":         T_ACADEMIC_WRITING,
    "essay":            T_ACADEMIC_WRITING,
    "rewrite":          T_REWRITING_SCIENTIFIC,
    "rephrase":         T_REWRITING_SCIENTIFIC,
    "code explanation": T_CODING_EXPLANATION,
    "explain code":     T_CODING_EXPLANATION,
    "programming":      T_PROGRAMMING_BASICS,
    "ux":               T_UX_CRITIQUE,

    # C group
    "summarize":     T_SUMMARIZATION,
    "summary":       T_SUMMARIZATION,
    "abstract":      T_SUMMARIZATION,
    "brainstorm":    T_BRAINSTORMING,
    "persuade":      T_PERSUASION,
    "explain":       T_EXPLANATION,
    "ideas":         T_CREATIVE_IDEATION,
    "innovate":      T_CREATIVE_IDEATION,
    "simplify":      T_INSTRUCTION_SIMPLIFY,
    "organize info": T_INFO_STRUCTURING,
    "reflect":       T_DEEP_REFLECTION,
    "prompt":        T_PROMPT_ENGINEERING,
    "pedagogy":      T_PEDAGOGICAL_REASONING,
    "logic":         T_RATIONAL_THINKING,
    "creative":      T_CREATIVE_WRITING,
    "story":         T_STORY_WRITING,
    "novel":         T_STORY_WRITING,
    "narrative":     T_STORY_WRITING,
    "email":         T_EMAIL_WRITING,
    "mail":          T_EMAIL_WRITING,
    "ad":            T_COPYWRITING,
    "advertise":     T_COPYWRITING,
    "ad copy":       T_COPYWRITING,
    "marketing":     T_MARKETING_CONTENT,
    "campaign":      T_CREATIVE_EMAIL_CAMPAIGN,
    "social":        T_SOCIAL_MEDIA_POST,
    "facebook post": T_SOCIAL_MEDIA_POST,
    "twitter":       T_SOCIAL_MEDIA_POST,
    "x":             T_SOCIAL_MEDIA_POST,
    "linkedin":      T_SOCIAL_MEDIA_POST,
    "instagram":     T_SOCIAL_MEDIA_POST,
    "tiktok":        T_SOCIAL_MEDIA_POST,
    "script":        T_SCRIPT_WRITING,
    "screenplay":    T_SCRIPT_WRITING,
    "blog":          T_BLOG_WRITING
}

ambiguous_tasks = {
    "writing": [
        T_ACADEMIC_WRITING, T_REWRITING_SCIENTIFIC,
        T_REWRITING_ACADEMIC, T_CREATIVE_WRITING, T_STORY_WRITING,
        T_EMAIL_WRITING, T_COPYWRITING, T_MARKETING_CONTENT,
        T_SOCIAL_MEDIA_POST, T_SCRIPT_WRITING, T_BLOG_WRITING,
        T_CREATIVE_EMAIL_CAMPAIGN
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
def list_all_tasks() -> None:
    """Print all supported tasks grouped by their category."""
    print(f"\n{BOLD}Supported Tasks:{RESET}")
    for group, details in task_groups.items():
        print(f"\n{YELLOW}{BOLD}Group {group}:{RESET}")
        for t in details["tasks"]:
            print(f"  - {t}")


def normalize(task_input: str) -> str:
    """Normalize a raw user input to a canonical task name via synonyms."""
    return task_synonyms.get(task_input.strip().lower(),
                             task_input.strip().lower())


def get_task_settings(task_or_synonym: str):
    """
    Resolve a task name (or synonym) to its canonical name, group, and settings.
    Returns (task_name, group_key, settings_dict) or (None, None, None) if not found.
    """
    task_name = normalize(task_or_synonym)
    for group, details in task_groups.items():
        if task_name in details["tasks"]:
            return task_name, group, details["settings"]
    return None, None, None


def needs_topic(task_name: str) -> bool:
    """
    Return True if the given task benefits from a user-supplied topic.
    Reads the 'needs_topic' flag from task_groups instead of a hardcoded list.
    """
    for details in task_groups.values():
        if task_name in details["tasks"]:
            return details.get("needs_topic", False)
    return False


def suggest(task_input: str) -> list:
    """Return a list of close task/synonym matches for an unrecognised input."""
    all_terms = list(task_synonyms.keys()) + [
        t for g in task_groups.values() for t in g["tasks"]
    ]
    return difflib.get_close_matches(task_input.lower(),
                                     all_terms,
                                     n=5,
                                     cutoff=0.5)


# ============= Smart Heuristics for Task Spec =============
def contains_any(text: str, keywords: list) -> bool:
    """Return True if any keyword appears in text (case-insensitive)."""
    t = text.lower()
    return any(k in t for k in keywords)


def detect_length_hint(topic: str, task_name: str = "") -> str:
    """
    Infer an appropriate output-length directive from the topic text
    and optionally from the task type.

    Topic-level cues take priority; task-based defaults apply as fallback.
    """
    # Explicit length cues in the topic always take priority
    if contains_any(topic, ["one paragraph", "paragraph", "short", "brief", "150 words"]):
        return "Length: one concise paragraph (~120–180 words)."
    if contains_any(topic, ["abstract", "executive summary"]):
        return "Length: abstract (150–250 words)."
    if contains_any(topic, ["report", "comprehensive", "long", "in-depth", "extensive"]):
        return "Length: in-depth (600–900 words)."

    # Task-based fallback when no explicit cue is present in topic
    if task_name in [T_UX_CRITIQUE, T_TECHNICAL_CRITIQUE]:
        return "Length: structured critique (400–600 words)."
    if task_name == T_SUMMARIZATION:
        return "Length: concise summary (150–300 words)."
    if task_name in [T_BRAINSTORMING, T_CREATIVE_IDEATION]:
        return "Length: 12 ideas with one-line rationale each."
    if task_name in [T_EMAIL_WRITING, T_SOCIAL_MEDIA_POST]:
        return "Length: short and focused (50–150 words)."
    if task_name in [T_BLOG_WRITING, T_SCRIPT_WRITING]:
        return "Length: medium-form (400–700 words)."
    if task_name in [T_ACADEMIC_WRITING, T_ANALYTICAL_WRITEUPS,
                     T_REWRITING_SCIENTIFIC, T_REWRITING_ACADEMIC]:
        return "Length: academic standard (400–800 words)."

    return "Length: appropriate and concise."


def pick_framework(task_name: str, topic: str) -> str:
    """
    Select the most suitable writing or logical framework for the given
    task and topic combination.
    """
    if task_name in [T_COPYWRITING, T_MARKETING_CONTENT]:
        if contains_any(topic, ["problem", "pain", "struggle", "issue", "friction"]):
            return "Framework: PAS (Problem–Agitate–Solution)."
        if contains_any(topic, ["launch", "new", "introduc", "campaign", "offer", "sale"]):
            return "Framework: AIDA (Attention–Interest–Desire–Action)."
        return "Framework: AIDA (Attention–Interest–Desire–Action)."

    if task_name == T_SOCIAL_MEDIA_POST:
        if contains_any(topic, ["linkedin"]):
            return "Platform: LinkedIn. Style: professional, insight-driven, value first."
        if contains_any(topic, ["twitter", "x"]):
            return "Platform: Twitter/X. Style: crisp hook + thread (3–5 tweets)."
        if contains_any(topic, ["instagram"]):
            return "Platform: Instagram. Style: caption + 5–7 hashtags."
        if contains_any(topic, ["tiktok"]):
            return "Platform: TikTok. Style: hook in first 2 seconds + CTA."
        return "Platform: platform-agnostic. Style: clear hook + value + CTA."

    if task_name == T_EMAIL_WRITING:
        if contains_any(topic, ["complaint", "issue", "refund"]):
            return "Email Type: Complaint/Resolution. Tone: firm yet polite. CTA: resolution timeline."
        if contains_any(topic, ["application", "job", "cv", "resume"]):
            return "Email Type: Job Application. Tone: professional. Structure: intro–fit–evidence–CTA."
        if contains_any(topic, ["follow up", "follow-up", "reminder"]):
            return "Email Type: Follow-up. Tone: polite. Structure: context–value–clear ask."
        if contains_any(topic, ["intro", "introduction", "outreach", "partnership"]):
            return "Email Type: Outreach/Introduction. Tone: warm, concise. CTA: short call."
        return "Email Type: Professional. Tone: concise and courteous. Clear subject + CTA."

    if task_name == T_BLOG_WRITING:
        if contains_any(topic, ["how to", "how-to", "guide", "tutorial"]):
            return "Blog Format: How-to Guide with steps, tips, and examples."
        if contains_any(topic, ["top ", "best", "list", "roundup"]):
            return "Blog Format: Listicle with ranked items and brief justifications."
        if contains_any(topic, ["vs", "versus", "compare", "comparison"]):
            return "Blog Format: Comparative analysis with criteria table."
        return "Blog Format: Standard article with intro–body–conclusion."

    if task_name == T_SCRIPT_WRITING:
        if contains_any(topic, ["ad", "advertisement", "promo", "commercial"]):
            return "Script Type: 30–60s ad. Structure: hook–problem–benefit–CTA."
        if contains_any(topic, ["youtube", "explainer", "video", "shorts"]):
            return "Script Type: YouTube explainer. Structure: hook (0–10s)–sections–recap–CTA."
        return "Script Type: Narrative script with scenes, dialogue, and pacing."

    if task_name in [T_CREATIVE_WRITING, T_STORY_WRITING]:
        if contains_any(topic, ["sci-fi", "science fiction", "cyberpunk", "space"]):
            return "Genre: Sci-Fi. Focus: world-building, plausible tech, character motivation."
        if contains_any(topic, ["mystery", "thriller", "detective"]):
            return "Genre: Mystery/Thriller. Focus: clues, red herrings, rising tension."
        if contains_any(topic, ["fantasy", "myth", "magic"]):
            return "Genre: Fantasy. Focus: lore, stakes, character arcs."
        return "Genre: Literary. Focus: imagery, voice, and character interiority."

    if task_name == T_SUMMARIZATION:
        if contains_any(topic, ["paper", "study", "research", "journal", "systematic review"]):
            return "Summary Type: Structured (Objective–Methods–Findings–Limitations–Implications)."
        return "Summary Type: Bullet-point key takeaways (5–7 bullets)."

    if task_name in [T_EXPLANATION, T_CODING_EXPLANATION, T_PROGRAMMING_BASICS]:
        if contains_any(topic, ["algorithm", "complexity", "big-o", "time", "space"]):
            return "Explainer Mode: Step-by-step with annotated pseudocode + Big-O analysis."
        if contains_any(topic, ["bug", "error", "debug"]):
            return "Explainer Mode: Debugging guide with hypothesis–tests–fix–verification."
        return "Explainer Mode: Concept breakdown with analogy + minimal runnable example."

    if task_name in [T_ACADEMIC_WRITING, T_REWRITING_SCIENTIFIC,
                     T_REWRITING_ACADEMIC, T_ANALYTICAL_WRITEUPS]:
        if contains_any(topic, ["literature review", "survey", "systematic", "meta-analysis"]):
            return "Structure: Formal academic style with literature synthesis and proper citations (APA 7th)."
        if contains_any(topic, ["proposal", "methodology", "methods"]):
            return "Structure: Aim–Background–Methods–Expected Results–Limitations."
        if contains_any(topic, ["paragraph", "short", "brief"]):
            return "Structure: One paragraph with thesis + evidence + micro-conclusion."
        return "Structure: Introduction–Argumentation–Conclusion with cautious, hedged claims."

    if task_name in [T_UX_CRITIQUE, T_TECHNICAL_CRITIQUE]:
        return "Critique Mode: Heuristics (Nielsen) + severity ratings + prioritized recommendations."

    if task_name in [T_BRAINSTORMING, T_CREATIVE_IDEATION]:
        return "Ideation Mode: 12 ideas grouped in 3 themes; each idea with one-line rationale."

    if task_name in [T_INFO_STRUCTURING, T_INSTRUCTION_SIMPLIFY,
                     T_PEDAGOGICAL_REASONING, T_RATIONAL_THINKING,
                     T_DEEP_REFLECTION, T_PERSUASION, T_PROMPT_ENGINEERING]:
        return "Mode: Clear headings, numbered steps, and evidence-backed rationale."

    return "Mode: Best-practice structure for the task."


def academic_style_prefs(task_name: str) -> str:
    """Return a style directive string appropriate for the given task."""
    if task_name in [T_ACADEMIC_WRITING, T_REWRITING_SCIENTIFIC,
                     T_REWRITING_ACADEMIC, T_ANALYTICAL_WRITEUPS]:
        return "Style: academic English, objective tone, precise terminology, avoid first-person; cite if sources are referenced."
    if task_name in [T_CODING_EXPLANATION, T_PROGRAMMING_BASICS, T_EXPLANATION]:
        return "Style: clear technical English, minimal jargon, examples first, definitions precise."
    if task_name == T_SUMMARIZATION:
        return "Style: neutral, concise, faithful to source; no new claims."
    if task_name in [T_COPYWRITING, T_MARKETING_CONTENT,
                     T_SOCIAL_MEDIA_POST, T_CREATIVE_EMAIL_CAMPAIGN]:
        return "Style: persuasive, audience-aware, crisp CTAs, avoid fluff."
    if task_name == T_EMAIL_WRITING:
        return "Style: professional, courteous, direct subject lines."
    if task_name == T_BLOG_WRITING:
        return "Style: informative, scannable subheadings, short paragraphs."
    if task_name in [T_SCRIPT_WRITING, T_STORY_WRITING, T_CREATIVE_WRITING]:
        return "Style: vivid, voice-driven, show-don't-tell."
    return "Style: clear and coherent."


def build_task_spec(task_name: str, topic: str) -> str:
    """
    Compose a single rich Task line for the R-CoT template by combining
    the task name, topic, framework, length hint, and style preference.
    """
    length_hint = detect_length_hint(topic, task_name)
    framework   = pick_framework(task_name, topic)
    style       = academic_style_prefs(task_name)

    parts = [task_name.title(), f"Topic: {topic}", framework, length_hint, style]
    return " — ".join(parts)


# ============= Main Interactive Flow =============
def main() -> None:
    """Entry point: interactive R-CoT prompt builder."""
    print(f"\n{BOLD}{YELLOW}=== Reflective Chain-of-Thought (R-CoT) Selector ==={RESET}")
    print("Type 'list' to see all supported tasks.\n")

    try:
        user_input = input("Enter the task name: ").strip()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Exiting.{RESET}")
        sys.exit(0)

    if user_input.lower() == "list":
        list_all_tasks()
        sys.exit(0)

    # ---- Resolve or clarify task ----
    task_name, group, settings = get_task_settings(user_input)

    if not group:
        norm = normalize(user_input)

        if norm in ambiguous_tasks:
            print(f"\n{YELLOW}Your input is too general. Possible options:{RESET}")
            for i, opt in enumerate(ambiguous_tasks[norm], 1):
                print(f"  {i}. {opt}")
            try:
                choice = input("\nEnter the number of the correct task: ").strip()
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Exiting.{RESET}")
                sys.exit(0)

            if choice.isdigit() and 1 <= int(choice) <= len(ambiguous_tasks[norm]):
                chosen = ambiguous_tasks[norm][int(choice) - 1]
                task_name, group, settings = get_task_settings(chosen)
            else:
                print(f"{RED}No valid selection. Exiting.{RESET}")
                sys.exit(1)

        else:
            suggestions = suggest(user_input)
            if suggestions:
                print(f"{YELLOW}Did you mean:{RESET}")
                for i, s in enumerate(suggestions, 1):
                    print(f"  {i}. {s}")
                try:
                    choice = input(
                        "\nEnter the number of the correct task (or press Enter to cancel): "
                    ).strip()
                except KeyboardInterrupt:
                    print(f"\n{YELLOW}Exiting.{RESET}")
                    sys.exit(0)

                if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                    selected = suggestions[int(choice) - 1]
                    task_name, group, settings = get_task_settings(selected)
                else:
                    print(f"{RED}No task selected. Exiting.{RESET}")
                    sys.exit(1)
            else:
                print(
                    f"{RED}No similar tasks found. Type 'list' to view supported tasks.{RESET}"
                )
                sys.exit(1)

    # ---- Ask for topic when relevant ----
    topic = ""
    if task_name and needs_topic(task_name):
        try:
            topic = input("\nWhat topic do you want to write about? ").strip()
            while not topic:
                topic = input("Please enter a valid topic: ").strip()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Exiting.{RESET}")
            sys.exit(0)

    # ---- Display settings ----
    print(f"\n{BOLD}{YELLOW}Task Selected:{RESET} {task_name}")
    print(f"{BOLD}{YELLOW}Group:{RESET}         {group}")
    print(f"\n{BOLD}{BLUE}Optimal Settings:{RESET}")
    for k, v in settings.items():
        print(f"{BLUE}  - {k}: {v}{RESET}")

    # ---- Build smart task spec and final prompt ----
    task_spec    = build_task_spec(task_name, topic if topic else "(no explicit topic)")
    final_prompt = RCOT_TEMPLATE.format(task_spec=task_spec)

    print(f"\n{BOLD}{GREEN}Generated R-CoT Prompt:{RESET}")
    print(f"{GREEN}{final_prompt}{RESET}")


if __name__ == "__main__":
    main()
