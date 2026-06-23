import re

CLICHES = ["delve", "testament", "revolutionize", "tapestry", "digital landscape", "more than ever", "fast-paced world"]

def analyze_post_content(platform, content_dict):
    """
    Evaluates a generated post and returns a score from 0-100,
    a readability rating, and actionable feedback items.
    """
    score = 100
    feedback = []
    readability = "Easy to read"
    
    # Extract text content depending on platform
    plat_lower = platform.lower()
    text_corpus = ""
    
    if plat_lower == 'linkedin':
        hook = content_dict.get('hook', '')
        body = content_dict.get('body', '')
        cta = content_dict.get('cta', '')
        text_corpus = f"{hook} {body} {cta}"
        
        # 1. Hook check (LinkedIn specific)
        if hook:
            hook_lines = [l for l in hook.split('\n') if l.strip()]
            if len(hook_lines) > 3:
                score -= 15
                feedback.append("⚠️ Hook is too long: Keep under 3 lines to avoid early truncation on the feed.")
            else:
                feedback.append("✅ Strong start: Hook is punchy and concise.")
                
        # 2. Spacing check
        if body:
            paragraphs = [p for p in body.split('\n\n') if p.strip()]
            oversized = [p for p in paragraphs if len(p.split()) > 40]
            if oversized:
                score -= 15
                feedback.append("⚠️ Formatting: Some paragraphs are too dense. Split into shorter, 1-2 sentence lines.")
            else:
                feedback.append("✅ Scanable layout: Good use of vertical spacing.")
                
    elif plat_lower == 'x':
        tweets = content_dict.get('thread', [])
        text_corpus = " ".join(tweets)
        
        # 1. Thread length check
        if len(tweets) > 1:
            feedback.append(f"✅ Conversational thread: {len(tweets)} tweets mapped to feed flow.")
            
            # Check character counts
            oversized_tweets = [idx for idx, t in enumerate(tweets, 1) if len(t) > 280]
            if oversized_tweets:
                score -= 20
                feedback.append(f"⚠️ Tweet limits: Tweets #{', '.join(map(str, oversized_tweets))} exceed 280 character limit.")
        else:
            score -= 10
            feedback.append("⚠️ Thread scale: Consider splitting single-tweets into 3+ tweets for higher thread engagement.")
            
    elif plat_lower == 'instagram':
        caption = content_dict.get('caption', '')
        text_corpus = caption
        
        # 1. Instagram opening hook
        if caption:
            caption_lines = [l for l in caption.split('\n') if l.strip()]
            if len(caption_lines) > 0 and len(caption_lines[0].split()) > 10:
                score -= 10
                feedback.append("⚠️ Opening Line: Make your Instagram first line punchier to capture swipe attention.")
            else:
                feedback.append("✅ Hook visual: Strong first-line icon placement.")
                
    elif plat_lower == 'blog':
        title = content_dict.get('blog_title', '')
        intro = content_dict.get('blog_introduction', '')
        sections = content_dict.get('blog_sections', [])
        text_corpus = f"{title} {intro} " + " ".join([s.get('heading', '') + " " + s.get('outline', '') for s in sections])
        
        # 1. Outline structure depth
        if len(sections) < 3:
            score -= 15
            feedback.append("⚠️ Content depth: Use at least 3 body outline headings to provide real SEO structure.")
        else:
            feedback.append("✅ Document depth: Excellent outline section breakdown.")
            
    # --- Universal Copywriting Heuristics ---
    
    # 1. Check for value-formatting lists (bullets, numbers)
    has_list = bool(re.search(r'(?:^\s*[-*•]|\b\d+[./\)])', text_corpus, re.MULTILINE))
    if has_list:
        score += 5  # Bonus
        feedback.append("✅ Value delivery: Great use of lists/bullets to break down concepts.")
    else:
        score -= 10
        feedback.append("⚠️ Scanability: Consider adding a bulleted list to improve reading speed.")
        
    # 2. Check for Low-Friction Call-To-Action (CTA) question mark
    has_cta_question = "?" in content_dict.get('cta', '') or "?" in text_corpus[-150:]
    if has_cta_question:
        score += 5  # Bonus
        feedback.append("✅ Engagement hook: End contains a question to invite comments/replies.")
    else:
        score -= 10
        feedback.append("⚠️ Call-To-Action: Add a clear question at the end to drive community discussions.")
        
    # 3. AI Buzzword clichés penalty
    found_cliches = [c for c in CLICHES if c in text_corpus.lower()]
    if found_cliches:
        score -= len(found_cliches) * 8
        feedback.append(f"⚠️ Cliché Alert: Remove generic phrasing/AI filler keywords: {', '.join(found_cliches)}")
        
    # Clamp score between 20 and 100
    score = max(20, min(100, score))
    
    # Compute Readability
    word_count = len(text_corpus.split())
    if word_count > 150:
        readability = "Easy, comprehensive reading"
    elif word_count > 60:
        readability = "Quick, punchy reading"
    else:
        readability = "Ultra-short visual snack"
        
    return {
        "score": score,
        "readability": readability,
        "feedback": feedback
    }

def calculate_efficiency_score(model_id, latency, quality_score):
    """
    Computes an efficiency score out of 100 based on:
    - Content Quality Score (60% weight)
    - Latency (30% weight)
    - Resource Cost Factor (10% weight)
    """
    cost_mapping = {
        "llama-3.1-8b-instant": 1.0,     # Extremely cheap / lightweight
        "gemma2-9b-it": 1.2,             # Cheap
        "mixtral-8x7b-32768": 2.5,       # Medium
        "llama-3.3-70b-versatile": 4.0   # Expensive / heavy
    }
    cost_factor = cost_mapping.get(model_id, 1.5)
    
    # 1. Quality Component (60%)
    quality_comp = quality_score * 0.60
    
    # 2. Speed Component (30%)
    if latency <= 0.5:
        speed_score = 100
    elif latency >= 5.0:
        speed_score = 10
    else:
        speed_score = 100 - ((latency - 0.5) / 4.5) * 90
        
    speed_comp = speed_score * 0.30
    
    # 3. Cost/Resource Component (10%)
    resource_score = max(10, min(100, 100 / cost_factor))
    resource_comp = resource_score * 0.10
    
    overall_efficiency = quality_comp + speed_comp + resource_comp
    return round(overall_efficiency)

