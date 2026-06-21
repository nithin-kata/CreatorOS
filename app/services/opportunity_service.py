import random

NICHE_DATA = {
    "ai": {
        "today": {
            "topic": "AI Agents for Automating Repetitive Student/Office Work",
            "reason": "Recruiters and tech founders are actively sharing agentic workflows. Presenting practical use-cases makes you look highly future-proof.",
            "strength": 92
        },
        "alerts": [
            {"topic": "MCP (Model Context Protocol) Servers rising", "reason": "Developers are shifting to standard contexts for LLM tool usage.", "strength": 88},
            {"topic": "Local LLMs running on consumer laptops", "reason": "Privacy concerns are driving high engagement for local execution guides.", "strength": 84},
            {"topic": "AI Career Roadmaps performing well", "reason": "Career advice tailored to the AI era is gaining massive traction among students.", "strength": 91}
        ]
    },
    "startups": {
        "today": {
            "topic": "Bootstrapping vs Venture Capital in 2026",
            "reason": "Economic shifts are favoring lean, self-funded startups. Sharing capital-efficient strategies builds immediate trust.",
            "strength": 95
        },
        "alerts": [
            {"topic": "Building in Public (Transparency) driving growth", "reason": "Audiences engage 3x more with authentic metrics and build updates.", "strength": 93},
            {"topic": "Product-Led Growth (PLG) tactics for micro-SaaS", "reason": "Founders are seeking low-friction acquisition strategies.", "strength": 89},
            {"topic": "Solopreneurship and the 1-person company model", "reason": "Tools like AI are enabling high-leverage solopreneurs.", "strength": 91}
        ]
    },
    "programming": {
        "today": {
            "topic": "Why Full-stack Engineers must become System Architects",
            "reason": "With AI generating boilerplate code, the real value of engineers is shifting toward high-level system design.",
            "strength": 91
        },
        "alerts": [
            {"topic": "Rust language popularity in system tools", "reason": "High-performance rewrites are trending in software tools discussions.", "strength": 87},
            {"topic": "TypeScript v5+ features and performance tips", "reason": "Actionable code snippets are outperforming general theory.", "strength": 83},
            {"topic": "Serverless edge runtimes vs traditional VMs", "reason": "Deployment speed and cost-saving articles are getting pinned.", "strength": 89}
        ]
    },
    "productivity": {
        "today": {
            "topic": "Digital Minimalism and Deep Work Blocks",
            "reason": "In the age of infinite feeds, ability to focus is a superpower. Sharing your focus setup gets high saves.",
            "strength": 89
        },
        "alerts": [
            {"topic": "The 'Second Brain' setup for creative professionals", "reason": "Note-taking systems (Obsidian/Notion) have a highly active sub-community.", "strength": 88},
            {"topic": "Time Blocking vs To-Do lists", "reason": "Debates on workspace time management drive high comments and interactions.", "strength": 85},
            {"topic": "AI as an administrative personal assistant", "reason": "Ways to automate email/calendar invite heavy engagement.", "strength": 90}
        ]
    },
    "default": {
        "today": {
            "topic": "Sharing lessons from failure in your industry",
            "reason": "Authenticity and vulnerability out-perform polished victory posts. Share what you learned from a recent mistake.",
            "strength": 90
        },
        "alerts": [
            {"topic": "Niche-specific tools saving you 10 hours a week", "reason": "Actionable tool recommendations drive immediate bookmark saves.", "strength": 86},
            {"topic": "A 5-year trend prediction in your area", "reason": "Futuristic projections demonstrate leadership and clear foresight.", "strength": 88},
            {"topic": "A breakdown of a major leader in your space", "reason": "Deconstructing someone else's success invites collaborative discussion.", "strength": 85}
        ]
    }
}

def clean_niche_input(niche_str):
    """
    Splits the niche string and looks for matches in our pre-defined database.
    """
    if not niche_str:
        return ["default"]
    
    niches = [n.strip().lower() for n in niche_str.split(",")]
    matched = []
    for niche in niches:
        for key in NICHE_DATA.keys():
            if key in niche or niche in key:
                matched.append(key)
    
    return matched if matched else ["default"]

def get_todays_opportunity(goal, niche_str):
    """
    Generates a personalized daily opportunity based on goal and niche.
    """
    matched_niches = clean_niche_input(niche_str)
    primary_niche = matched_niches[0]
    
    data = NICHE_DATA.get(primary_niche, NICHE_DATA["default"])
    today_template = data["today"]
    
    # Customize based on user goal to make it highly authentic
    goal_customization = ""
    if "Job" in goal:
        goal_customization = " Shows recruiters you understand industry dynamics and can apply knowledge."
    elif "Brand" in goal:
        goal_customization = " Establishes you as a forward-thinking voice and industry authority."
    elif "Followers" in goal:
        goal_customization = " Promotes viral sharing since it addresses a highly active general discussion."
    elif "Startup" in goal:
        goal_customization = " Displays founder-level technical and operational awareness to prospective users."

    return {
        "topic": today_template["topic"],
        "reason": today_template["reason"] + goal_customization,
        "strength": today_template["strength"]
    }

def get_opportunity_alerts(goal, niche_str):
    """
    Generates a list of 3 trending opportunity alerts.
    """
    matched_niches = clean_niche_input(niche_str)
    
    alerts = []
    # Collect alerts from user's niches or defaults
    for niche in matched_niches:
        alerts.extend(NICHE_DATA.get(niche, NICHE_DATA["default"])["alerts"])
        
    # De-duplicate alerts
    unique_alerts = []
    seen = set()
    for alert in alerts:
        if alert["topic"] not in seen:
            seen.add(alert["topic"])
            unique_alerts.append(alert)
            
    # Always return exactly 3 alerts
    if len(unique_alerts) < 3:
        unique_alerts.extend(NICHE_DATA["default"]["alerts"])
        
    # Shuffle or slice to get 3
    random.seed(len(niche_str))  # Make it stable per user niche
    sampled = random.sample(unique_alerts, min(len(unique_alerts), 5))
    return sampled[:3]

def refresh_niche_opportunities(goal, niche_str, creator_type=None, target_audience=None):
    """
    Generates 3 fresh trending opportunities for the user's niche using Groq API.
    Falls back to a randomized local selection if API key is missing or fails.
    """
    from app.services.groq_service import get_groq_client_headers, DEFAULT_MODEL
    import requests
    import json
    
    headers = get_groq_client_headers()
    
    if headers:
        system_prompt = (
            "You are an expert trend forecaster and content strategist analyzing real-time digital signals.\n"
            "Generate exactly 3 fresh, highly specific, and currently trending content opportunities over the internet "
            "that would appeal to the user's specific target audience.\n\n"
            "Generate a JSON array matching this structure EXACTLY (do not wrap inside an outer object, return a list at top level):\n"
            "[\n"
            "  {\n"
            '    "topic": "Vibrant scroll-stopping trending topic name",\n'
            '    "reason": "1-2 sentences explaining why this topic is hot right now and how it appeals to the target audience"\n'
            "  },\n"
            "  ...\n"
            "]\n\n"
            "Do not include any markdown framing outside the JSON, markdown code block backticks (like ```json), or explanatory text. Return raw JSON."
        )
        
        user_prompt = (
            f"User Goal: {goal}\n"
            f"User Profile: {creator_type or 'Professional'}\n"
            f"Niches: {niche_str}\n"
            f"Target Audience: {target_audience or 'general network'}\n"
        )
        
        try:
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.85
            }
            
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                result_json = response.json()
                content_text = result_json["choices"][0]["message"]["content"]
                parsed = json.loads(content_text)
                
                # Check for standard list structure
                if isinstance(parsed, list):
                    return parsed[:3]
                elif isinstance(parsed, dict):
                    # In case the model wrapped it in an object like {"opportunities": [...]}
                    for val in parsed.values():
                        if isinstance(val, list):
                            return val[:3]
                    # Or convert dict to list
                    return [{"topic": k, "reason": str(v)} for k, v in parsed.items()][:3]
        except Exception as e:
            print(f"Fallback triggered during opportunities refresh: {e}")
            
    # Fallback to local database with randomization to ensure fresh content
    matched_niches = clean_niche_input(niche_str)
    pool = []
    for n in matched_niches:
        pool.extend(NICHE_DATA.get(n, NICHE_DATA["default"])["alerts"])
    # If not enough, extend with default alerts
    if len(pool) < 3:
        pool.extend(NICHE_DATA["default"]["alerts"])
        
    # De-duplicate pool
    seen = set()
    unique_pool = []
    for item in pool:
        if item["topic"] not in seen:
            seen.add(item["topic"])
            unique_pool.append(item)
            
    # Shuffle list randomly to return fresh alerts
    random.shuffle(unique_pool)
    return unique_pool[:3]
