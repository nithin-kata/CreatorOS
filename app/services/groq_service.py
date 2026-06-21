import os
import json
import requests
import random
from flask import current_app

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"

def get_groq_client_headers():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def generate_post(goal, niche, platform, tone, prompt, memory_context=None, creator_type=None, target_audience=None, niche_details=None, document_context=None):
    """
    Generates structured content using Groq API, with a premium copywriting focus.
    If the API key is not configured or fails, it defaults to a high-quality fallback generator.
    """
    headers = get_groq_client_headers()
    
    # Constructing a comprehensive ghostwriter system prompt
    system_prompt = (
        "You are an elite ghostwriter, copywriting strategist, and personal brand architect for top-tier creators.\n"
        "Your goal is to write high-converting, premium-quality content that goes viral and gets massive impressions.\n\n"
        "CRITICAL WRITING GUIDELINES:\n"
        "1. Write like a human practitioner. Avoid corporate fluff, generic definitions, or introductory filler (e.g. 'In today's fast-paced world', 'As a...').\n"
        "2. Use copywriting frameworks like Hook-Insight-Action or Problem-Agitate-Solve.\n"
        "3. Keep lines short. Use vertical whitespace. One idea per paragraph.\n"
        "4. Include concrete metrics, numbers, or specific scenarios (e.g., 'saved 14 hours', 'boosted CTR by 27%') to build immediate trust.\n"
        "5. TONE RULES: Make sure the tone matches the requested style:\n"
        "   - Professional: Decisive, data-driven, authoritative, highly competent.\n"
        "   - Storytelling: Vulnerable, personal, starts in the middle of the action, shares lessons from mistakes.\n"
        "   - Educational: Actionable listicles, step-by-step blueprints, checklists, immediate value.\n"
        "   - Casual: Relatable, friendly, punchy, conversational, no buzzwords.\n"
        "6. Never use AI clichés like 'delve', 'testament', 'revolutionize', 'tapestry', 'delve deep'.\n"
        "7. Strictly avoid using any emojis in the content to maintain maximum professionalism.\n\n"
        "If the target network is 'Blog', generate a JSON object matching this structure EXACTLY:\n"
        "{\n"
        '  "blog_title": "An SEO-optimized, highly click-worthy blog title targeting the audience",\n'
        '  "blog_introduction": "An engaging, problem-focused opening outline that hooks the reader instantly",\n'
        '  "blog_sections": [\n'
        '    {"heading": "1. [Key conceptual section heading]", "outline": "3-4 highly detailed outline points detailing actionable insights, data points, or step-by-step blueprints."},\n'
        '    {"heading": "2. [Key actionable section heading]", "outline": "3-4 highly detailed outline points detailing actionable insights, data points, or step-by-step blueprints."},\n'
        '    {"heading": "3. [Key tactical section heading]", "outline": "3-4 highly detailed outline points detailing actionable insights, data points, or step-by-step blueprints."}\n'
        '  ],\n'
        '  "blog_conclusion": "A strong summary of the article and a low-friction call-to-action.",\n'
        '  "blog_keywords": "3-5 comma-separated SEO keywords"\n'
        "}\n\n"
        "For all other networks (LinkedIn, X, Instagram), generate a JSON object matching this structure EXACTLY:\n"
        "{\n"
        '  "hook": "A scroll-stopping opening hook (under 3 punchy lines) designed to maximize click-through rate",\n'
        '  "body": "The core educational value or story, formatted with short lines, bullet points, and vertical whitespace",\n'
        '  "cta": "An engaging, low-friction call-to-action to maximize comments/shares",\n'
        '  "hashtags": "3-5 relevant, high-impact hashtags",\n'
        '  "caption": "Short visual-focused caption for Instagram only",\n'
        '  "thread": ["1/ [First tweet - Hook & outline of the thread] [No Emoji]", "2/ [Second tweet - Main value point 1]", "3/ [Third tweet - Value point 2]", "4/ [Fourth tweet - CTA and wrap-up]"]\n'
        "}\n\n"
        "Do not include any markdown framing outside the JSON, markdown code block backticks (like ```json), or explanatory text. Return raw JSON."
    )
    
    user_prompt = (
        f"Goal: {goal}\n"
        f"Niche/Topics: {niche}\n"
        f"Platform: {platform}\n"
        f"Tone: {tone}\n"
        f"Topic to write about: {prompt}\n"
    )
    
    if creator_type:
        user_prompt += f"Creator Profile: {creator_type}\n"
    if target_audience:
        user_prompt += f"Target Audience: {target_audience}\n"
    if niche_details:
        user_prompt += f"Specific Expertise context: {niche_details}\n"
    if memory_context:
        user_prompt += f"\nCreator Memory Context (Avoid these exact angles or hooks to keep content fresh):\n{memory_context}\n"
    if document_context:
        user_prompt += f"\nReference Context / Source Material (Analyse and incorporate details from this content):\n{document_context}\n"
        
    if headers:
        try:
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.75
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                result_json = response.json()
                content_text = result_json["choices"][0]["message"]["content"]
                parsed_data = json.loads(content_text)
                parsed_data["_source"] = "api"
                return parsed_data
            else:
                print(f"\n[GROQ API EXPLICIT ERROR] Status: {response.status_code} | Body: {response.text}\n")
                if current_app:
                    current_app.logger.warning(f"Groq API Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"\n[GROQ EXCEPTION IN CALL] Error: {e}\n")
            if current_app:
                current_app.logger.warning(f"Groq API call failed: {e}. Falling back to generator simulator.")
            
    # Fallback high-quality simulation
    fallback_data = get_fallback_generation(goal, niche, platform, tone, prompt, creator_type, target_audience, document_context)
    fallback_data["_source"] = "fallback"
    return fallback_data

def get_fallback_generation(goal, niche, platform, tone, prompt, creator_type=None, target_audience=None, document_context=None):
    """
    Generates premium-level realistic creator content templates dynamically when Groq is unavailable.
    It builds high-impression copy using real copywriting formulas (PAS, Hook-Insight, Contrarian).
    """
    clean_prompt = prompt.replace("🔥", "").replace("🚀", "").replace("📈", "").strip()
    primary_niche = niche.split(",")[0].strip() if niche else "personal branding"
    audience = target_audience or "recruitment scouts"
    creator = creator_type or "professional"
    
    # 1. Platform is Blog Outline
    if platform.lower() == 'blog':
        title_templates = [
            f"The Compounding Playbook: Master {clean_prompt} as a {creator}",
            f"Why 90% of Creators Fail at {clean_prompt} (And the 3-Step System to Fix It)",
            f"The Practitioner's Guide to {clean_prompt}: From Rookie to Authority"
        ]
        title = random.choice(title_templates)
        
        intro = (
            f"Most guides on {clean_prompt} focus on general theories. In this breakdown, we skip the fluff. "
            f"As a {creator} targeting {audience}, building consistency in {primary_niche} is the highest leverage move you can make. "
            f"Here is the exact step-by-step framework to transition from chasing impressions to building authentic authority."
        )
        if document_context:
            intro += "\n\nNote: Content outline aligned using reference documents."
            
        sections = [
            {
                "heading": f"1. The Core Paradigm Shift in {primary_niche}",
                "outline": f"• Stop broadcasting general advice; focus on sharing practitioner-level proof.\n• Why targeting {audience} requires showing your actual code, designs, or business metrics.\n• The difference between vanity metrics and high-impression value delivery."
            },
            {
                "heading": f"2. The 3-Step Execution Framework for {clean_prompt}",
                "outline": f"• Step 1: Audit your current setup and identify friction points.\n• Step 2: Build a weekly distribution channel to document your learnings in public.\n• Step 3: Iterate based on qualitative comments rather than raw volume."
            },
            {
                "heading": "3. Designing the Feedback Loop",
                "outline": f"• How to leverage CreatorOS consistency metrics to maintain compounding streak results.\n• Repurposing core insights from this framework into punchy X threads and LinkedIn posts.\n• Encouraging low-friction interaction to grow your professional network."
            }
        ]
        conclusion = f"The creator economy rewards practitioners who act, not spectators who comment. Pick one system from this guide and build it today."
        keywords = f"{clean_prompt.replace(' ', '')}, {primary_niche.replace(' ', '')}, {creator.replace(' ', '')}Growth"
        
        return {
            "blog_title": title,
            "blog_introduction": intro,
            "blog_sections": sections,
            "blog_conclusion": conclusion,
            "blog_keywords": keywords
        }
        
    # 2. Platform is Social Media (LinkedIn, X, Instagram)
    # Generate high-impression hooks based on Tone
    hooks = {
        "Professional": [
            f"The best candidates don't have the best resumes. They have the best proof of work.\n\nHere is how I'm master-planning {clean_prompt} to stand out to {audience}:",
            f"99% of conversations about {clean_prompt} are theoretical.\n\nLet's talk about the raw data, metrics, and actionable systems that actually drive {goal.lower()}:",
            f"If your goal is to {goal.lower()}, stop chasing vanity metrics.\n\nInstead, build systems around {primary_niche}. Here is the exact blueprint I use:"
        ],
        "Storytelling": [
            f"6 months ago, I was completely stuck trying to {goal.lower()}.\n\nI was posting daily about {primary_niche}, but got 0 impressions. Then I changed one thing:",
            f"I made a major mistake when building systems for {clean_prompt}.\n\nIt cost me weeks of wasted effort. But the lesson learned was worth it. Here is the raw story:",
            f"Recruiters didn't care about my certificates.\n\nThey cared about my building blocks. Here's how sharing my journey in {primary_niche} opened doors:"
        ],
        "Educational": [
            f"Most professionals spend 10+ hours a week overthinking {clean_prompt}.\n\nHere is a 3-step framework to streamline {primary_niche} and build consistency in 15 minutes a day:",
            f"Want to capture the attention of {audience}?\n\nHere are 3 actionable design frameworks for {clean_prompt} you can copy-paste today:",
            f"I built a blueprint to optimize {clean_prompt} for {goal.lower()}.\n\nNo general theories. Just 3 concrete steps to execute:"
        ],
        "Casual": [
            f"Let's be real about {clean_prompt} for a second.\n\nMost advice you see on your feed is corporate jargon. Here is how it actually works:",
            f"An honest confession: building consistency in {primary_niche} is hard.\n\nBut chasing {goal.lower()} without a plan is harder. Here is my simple system to stay sane:",
            f"Quick question for the feed: are you building in public, or just talking in public?\n\nHere's the difference when documenting {clean_prompt}:"
        ]
    }
    
    # Select hook randomly from tone list
    selected_hook = random.choice(hooks.get(tone, hooks["Professional"]))
    
    # Body structures based on tone
    bodies = {
        "Professional": (
            f"To capture the attention of {audience}, your content must show practitioner-level competence.\n\n"
            f"Here are 3 key execution pillars to apply to {clean_prompt}:\n"
            f"1. Document the actual process, not just the finished project.\n"
            f"2. Use specific metrics (e.g. time saved, cost reduced) to demonstrate value.\n"
            f"3. Align every insight with your target niche of {primary_niche}.\n\n"
            f"Consistency is not about writing more; it's about being more specific."
        ),
        "Storytelling": (
            f"I used to believe that success in {clean_prompt} was about luck.\n\n"
            f"I was copying templates and writing generic tips. It felt hollow, and the results showed it.\n\n"
            f"Everything changed when I shared my actual failures—like how I mismanaged my first {primary_niche} project.\n\n"
            f"Authenticity beats polished slides. If you want to connect with {audience}, share the process behind your growth."
        ),
        "Educational": (
            f"Here is the step-by-step checklist to optimize {clean_prompt} starting today:\n\n"
            f"• Step 1: Audit your core themes. Pick 2 topics under {primary_niche}.\n"
            f"• Step 2: Establish a weekly commitment (use tools like CreatorOS to track streaks).\n"
            f"• Step 3: Focus on depth. Write for a single reader: {audience}.\n\n"
            f"Save this checklist if you are actively working on {goal.lower()}."
        ),
        "Casual": (
            f"You don't need a 5-step masterclass to get started with {clean_prompt}.\n\n"
            f"You just need to share what you learned today. \n\n"
            f"If you're a {creator} writing about {primary_niche}, stop writing like a textbook. Write like you're explaining it to a friend over coffee.\n\n"
            f"It's less pressure, and honestly, people actually read it."
        )
    }
    
    selected_body = bodies.get(tone, bodies["Professional"])
    if document_context:
        selected_body += "\n\nNote: Copy aligned with uploaded document insights."
        
    # Call-to-actions based on goal
    ctas = {
        "Get a Job": f"Recruiters: what is the first thing you look for on a candidate's profile? Let me know below.",
        "Build Personal Brand": f"What is your biggest roadblock when it comes to {clean_prompt}? Let's discuss in the comments.",
        "Grow Followers": f"If this resonated, follow for more breakdowns on {primary_niche}. Share this post with a friend!",
        "Promote Startup": f"If you want to automate this process, try out CreatorOS. Link is in my bio."
    }
    
    selected_cta = ctas.get(goal, "What are your thoughts on this? Drop a reply below.")
    
    # Hash tags
    hash_list = [f"#{t.strip().replace(' ', '')}" for t in niche.split(",")[:3]] if niche else ["#CreatorEconomy", "#PersonalBrand"]
    if "#" not in hash_list[0]:
        hash_list = [f"#{h}" for h in hash_list]
    hashtags = " ".join(hash_list) + " #CreatorOS"
    
    # Thread formatting for X
    thread = [
        f"[Thread] {selected_hook.splitlines()[0]}",
        f"1/ Most advice about {clean_prompt} is generic.\n\nIf you want to reach {audience}, stop copying trends. Share actual blueprints, projects, or mistakes from {primary_niche}.",
        f"2/ Keep it structured.\n\nUse bullet points, focus on high-impact insights, and write simple lines. People read on their phones—whitespace matters.",
        f"3/ Stay consistent.\n\nIf you want to {goal.lower()}, you need to compound your efforts. Pick a weekly target and stick to it.",
        f"4/ That's a wrap! If you found this thread useful:\n\n- Repost the first tweet\n- Follow me for more insights on {primary_niche}"
    ]
    
    # Instagram Caption
    caption = (
        f"Topic Breakdown: {clean_prompt}.\n\n"
        f"If you are aiming to {goal.lower()} as a {creator}, bookmark this post right now.\n\n"
        f"Double tap if this resonates!"
    )
    
    return {
        "hook": selected_hook,
        "body": selected_body,
        "cta": selected_cta,
        "hashtags": hashtags,
        "caption": caption,
        "thread": thread
    }
