from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import json
import requests
from app.models import db, Content, Activity
from app.services import groq_service, memory_service, analyzer_service
from app.dashboard.routes import log_activity

content = Blueprint('content', __name__)

@content.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    if not current_user.goal:
        return redirect(url_for('dashboard.onboarding'))
        
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        platform = request.form.get('platform')
        tone = request.form.get('tone')
        
        if not prompt or not platform or not tone:
            return jsonify({"error": "Missing required generation inputs."}), 400
            
        user_goal = current_user.goal
        
        # 1. Fetch Creator Memory (context of last 10 posts)
        memory_context = memory_service.get_memory_context(current_user.id)
        
        # 2. Call Groq AI service
        generated = groq_service.generate_post(
            goal=user_goal.goal,
            niche=user_goal.niche,
            platform=platform,
            tone=tone,
            prompt=prompt,
            memory_context=memory_context,
            creator_type=user_goal.creator_type,
            target_audience=user_goal.target_audience,
            niche_details=user_goal.niche_details
        )
        
        # Log active generation in Activity table
        log_activity(current_user.id)
        
        # 3. Perform Similarity check against last 10 posts
        # We check similarity of the generated hook
        hook_to_check = generated.get('hook', '')
        is_similar, similarity_msg = memory_service.check_similarity(current_user.id, prompt, hook_to_check)
        
        # 4. Perform Engagement & Readability analysis
        analysis = analyzer_service.analyze_post_content(platform, generated)
        
        # Return standard response
        return jsonify({
            "success": True,
            "data": generated,
            "similarity": {
                "is_similar": is_similar,
                "message": similarity_msg
            },
            "analysis": analysis
        })
        
    # GET Request: Pre-populate parameters if coming from dashboard links
    prefill_topic = request.args.get('topic', '')
    prefill_platform = request.args.get('platform', current_user.goal.platform)
    prefill_tone = request.args.get('tone', current_user.goal.tone)
    
    return render_template(
        'content/generate.html',
        prefill_topic=prefill_topic,
        prefill_platform=prefill_platform,
        prefill_tone=prefill_tone,
        goal=current_user.goal
    )

@content.route('/saved')
@login_required
def saved():
    if not current_user.goal:
        return redirect(url_for('dashboard.onboarding'))
        
    search_query = request.args.get('q', '').strip()
    
    query = Content.query.filter_by(user_id=current_user.id)
    if search_query:
        query = query.filter(
            (Content.topic.ilike(f"%{search_query}%")) | 
            (Content.content.ilike(f"%{search_query}%"))
        )
        
    drafts = query.order_by(Content.created_at.desc()).all()
    
    # Process saved drafts JSON content for template consumption
    processed_drafts = []
    for d in drafts:
        try:
            parsed_content = json.loads(d.content)
        except Exception:
            parsed_content = {
                "hook": "",
                "body": d.content,
                "cta": "",
                "hashtags": "",
                "caption": d.content,
                "thread": [d.content]
            }
        processed_drafts.append({
            "id": d.id,
            "topic": d.topic,
            "platform": d.platform,
            "created_at": d.created_at,
            "parsed_content": parsed_content
        })
        
    return render_template('content/saved.html', drafts=processed_drafts, search_query=search_query)

@content.route('/save-draft', methods=['POST'])
@login_required
def save_draft():
    topic = request.form.get('topic')
    platform = request.form.get('platform')
    content_json = request.form.get('content')
    
    if not topic or not platform or not content_json:
        return jsonify({"success": False, "error": "Invalid request fields."}), 400
        
    # Ensure content is valid JSON
    try:
        json.loads(content_json)
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Content must be valid JSON format."}), 400
        
    new_draft = Content(
        user_id=current_user.id,
        topic=topic,
        platform=platform,
        content=content_json
    )
    
    db.session.add(new_draft)
    log_activity(current_user.id)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Draft successfully saved in Creator Memory."})

@content.route('/delete-draft/<int:draft_id>', methods=['POST', 'DELETE'])
@login_required
def delete_draft(draft_id):
    draft = Content.query.filter_by(id=draft_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(draft)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'DELETE':
        return jsonify({"success": True, "message": "Draft deleted."})
        
    flash('Draft deleted successfully.', 'info')
    return redirect(url_for('content.saved'))

@content.route('/refine', methods=['POST'])
@login_required
def refine():
    current_draft_str = request.form.get('current_draft')
    refinement_prompt = request.form.get('refinement_prompt')
    platform = request.form.get('platform')
    tone = request.form.get('tone')
    topic = request.form.get('topic')
    
    if not current_draft_str or not refinement_prompt or not platform or not tone or not topic:
        return jsonify({"success": False, "error": "Missing required refinement parameters."}), 400
        
    try:
        current_draft = json.loads(current_draft_str)
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid current draft JSON format."}), 400
        
    headers = groq_service.get_groq_client_headers()
    
    system_prompt = (
        "You are an elite copywriting assistant. You are refining an existing social media draft or blog outline.\n"
        "You must apply the user's refinement instruction precisely, improving readability and impact, while retaining the exact same JSON format.\n"
        "Generate a JSON object matching this structure EXACTLY (do not wrap inside an outer object, return it directly at top level):\n"
    )
    
    if platform.lower() == 'blog':
        system_prompt += (
            "{\n"
            '  "blog_title": "SEO-optimized Title",\n'
            '  "blog_introduction": "Opening hook/intro paragraph",\n'
            '  "blog_sections": [\n'
            '    {"heading": "Heading text...", "outline": "Detailed outline points..."}\n'
            '  ],\n'
            '  "blog_conclusion": "Summary and Call-To-Action",\n'
            '  "blog_keywords": "SEO keywords"\n'
            "}\n"
        )
    else:
        system_prompt += (
            "{\n"
            '  "hook": "Punchy opening hook",\n'
            '  "body": "Value points and body story",\n'
            '  "cta": "Engagement call to action",\n'
            '  "hashtags": "3-5 hashtags",\n'
            '  "caption": "Instagram caption text",\n'
            '  "thread": ["Tweet 1", "Tweet 2", "Tweet 3"]\n'
            "}\n"
        )
    system_prompt += "Do not include any markdown code blocks (like ```json), surrounding text, or explainers. Return raw JSON."
    
    user_prompt = (
        f"Original Topic: {topic}\n"
        f"Original Platform: {platform}\n"
        f"Original Tone: {tone}\n"
        f"Current Draft JSON: {current_draft_str}\n"
        f"User Refinement Instruction: {refinement_prompt}\n"
    )
    
    refined = None
    if headers:
        try:
            payload = {
                "model": groq_service.DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            response = requests.post(groq_service.GROQ_API_URL, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                content_text = response.json()["choices"][0]["message"]["content"]
                refined = json.loads(content_text)
                refined["_source"] = "api"
        except Exception as e:
            print(f"Refinement API call failed: {e}")
            
    if not refined:
        # Fallback refinement simulation
        refined = current_draft.copy()
        refined["_source"] = "fallback"
        ref_lower = refinement_prompt.lower()
        if "short" in ref_lower or "condense" in ref_lower:
            if "body" in refined:
                lines = refined["body"].split('\n\n')
                refined["body"] = "\n\n".join(lines[:max(1, len(lines)-1)]) + "\n\n(Condensed for brevity)"
            if "thread" in refined:
                refined["thread"] = refined["thread"][:max(2, len(refined["thread"])-1)]
        elif "punchy" in ref_lower or "contrarian" in ref_lower:
            if "hook" in refined:
                refined["hook"] = f"Forget standard advice. Here is the reality: {refined['hook']}"
            elif "blog_title" in refined:
                refined["blog_title"] = f"Why Most Creators Fail at: {refined['blog_title']}"
        else:
            if "body" in refined:
                refined["body"] = refined["body"] + f"\n\n(Refined: {refinement_prompt})"
                
    analysis = analyzer_service.analyze_post_content(platform, refined)
    log_activity(current_user.id)
    
    return jsonify({
        "success": True,
        "data": refined,
        "analysis": analysis
    })
