from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import json
import requests
import io
import time
import random
from app.models import db, Content, Activity, Document
from app.services import groq_service, memory_service, analyzer_service
from app.dashboard.routes import log_activity
from app.utils.document_parser import extract_text_from_file
import logging

logger = logging.getLogger(__name__)

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
        model = request.form.get('model')
        doc_ids = request.form.getlist('document_ids')
        
        if not prompt or not platform or not tone:
            return jsonify({"error": "Missing required generation inputs."}), 400
            
        user_goal = current_user.goal
        
        # 1. Fetch Creator Memory (context of last 10 posts)
        memory_context = memory_service.get_memory_context(current_user.id)
        
        # 2. Fetch Selected reference context documents
        document_context = ""
        if doc_ids:
            docs = Document.query.filter(Document.id.in_(doc_ids), Document.user_id == current_user.id).all()
            for d in docs:
                document_context += f"\n--- Reference Context from Document '{d.filename}' ---\n{d.content_text}\n"
        
        # 3. Call Groq AI service with latency tracking
        start_time = time.time()
        
        selected_model = model if model in groq_service.SUPPORTED_MODELS else groq_service.DEFAULT_MODEL
        
        try:
            generated = groq_service.generate_post(
                goal=user_goal.goal,
                niche=user_goal.niche,
                platform=platform,
                tone=tone,
                prompt=prompt,
                memory_context=memory_context,
                creator_type=user_goal.creator_type,
                target_audience=user_goal.target_audience,
                niche_details=user_goal.niche_details,
                document_context=document_context,
                model=selected_model
            )
        except Exception as e:
            # Fallback
            generated = groq_service.get_fallback_generation(
                goal=user_goal.goal,
                niche=user_goal.niche,
                platform=platform,
                tone=tone,
                prompt=prompt,
                creator_type=user_goal.creator_type,
                target_audience=user_goal.target_audience,
                document_context=document_context,
                model=selected_model
            )
            generated["_source"] = "fallback"

        latency = round(time.time() - start_time, 2)
        
        # Add artificial delays in fallback mode to highlight model performance differences
        if generated.get("_source") == "fallback":
            mock_delays = {
                "llama-3.1-8b-instant": 0.4,
                "gemma2-9b-it": 0.7,
                "mixtral-8x7b-32768": 1.4,
                "llama-3.3-70b-versatile": 2.2
            }
            delay = mock_delays.get(selected_model, 0.5)
            time.sleep(delay)
            latency = round(delay + random.uniform(-0.05, 0.1), 2)
        
        # Log active generation in Activity table
        log_activity(current_user.id)
        
        # 4. Perform Similarity check against last 10 posts
        # We check similarity of the generated hook
        hook_to_check = generated.get('hook', '')
        is_similar, similarity_msg = memory_service.check_similarity(current_user.id, prompt, hook_to_check)
        
        # 5. Perform Engagement & Readability analysis
        analysis = analyzer_service.analyze_post_content(platform, generated)
        
        # 6. Calculate model efficiency score
        efficiency_score = analyzer_service.calculate_efficiency_score(selected_model, latency, analysis["score"])
        
        cost_levels = {
            "llama-3.1-8b-instant": "Ultra-Low",
            "gemma2-9b-it": "Low",
            "mixtral-8x7b-32768": "Medium",
            "llama-3.3-70b-versatile": "High"
        }
        cost_level = cost_levels.get(selected_model, "Low")
        
        # Return standard response
        return jsonify({
            "success": True,
            "data": generated,
            "similarity": {
                "is_similar": is_similar,
                "message": similarity_msg
            },
            "analysis": analysis,
            "efficiency": {
                "score": efficiency_score,
                "latency": latency,
                "cost_level": cost_level,
                "model_id": selected_model,
                "model_name": groq_service.SUPPORTED_MODELS[selected_model]
            }
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

@content.route('/compare', methods=['POST'])
@login_required
def compare():
    if not current_user.goal:
        return jsonify({"error": "Please complete onboarding first."}), 400
        
    prompt = request.form.get('prompt')
    platform = request.form.get('platform')
    tone = request.form.get('tone')
    doc_ids = request.form.getlist('document_ids')
    
    if not prompt or not platform or not tone:
        return jsonify({"error": "Missing required generation inputs."}), 400
        
    user_goal = current_user.goal
    memory_context = memory_service.get_memory_context(current_user.id)
    
    document_context = ""
    if doc_ids:
        docs = Document.query.filter(Document.id.in_(doc_ids), Document.user_id == current_user.id).all()
        for d in docs:
            document_context += f"\n--- Reference Context from Document '{d.filename}' ---\n{d.content_text}\n"
            
    models = ["llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
    results = {}
    
    log_activity(current_user.id)
    
    cost_levels = {
        "llama-3.1-8b-instant": "Ultra-Low",
        "gemma2-9b-it": "Low",
        "mixtral-8x7b-32768": "Medium",
        "llama-3.3-70b-versatile": "High"
    }
    
    for m in models:
        start_time = time.time()
        try:
            generated = groq_service.generate_post(
                goal=user_goal.goal,
                niche=user_goal.niche,
                platform=platform,
                tone=tone,
                prompt=prompt,
                memory_context=memory_context,
                creator_type=user_goal.creator_type,
                target_audience=user_goal.target_audience,
                niche_details=user_goal.niche_details,
                document_context=document_context,
                model=m
            )
        except Exception as e:
            generated = groq_service.get_fallback_generation(
                goal=user_goal.goal,
                niche=user_goal.niche,
                platform=platform,
                tone=tone,
                prompt=prompt,
                creator_type=user_goal.creator_type,
                target_audience=user_goal.target_audience,
                document_context=document_context,
                model=m
            )
            generated["_source"] = "fallback"
            
        latency = round(time.time() - start_time, 2)
        
        if generated.get("_source") == "fallback":
            mock_delays = {
                "llama-3.1-8b-instant": 0.4,
                "gemma2-9b-it": 0.7,
                "mixtral-8x7b-32768": 1.4,
                "llama-3.3-70b-versatile": 2.2
            }
            delay = mock_delays.get(m, 0.5)
            time.sleep(delay)
            latency = round(delay + random.uniform(-0.05, 0.1), 2)
            
        analysis = analyzer_service.analyze_post_content(platform, generated)
        eff_score = analyzer_service.calculate_efficiency_score(m, latency, analysis["score"])
        
        hook_to_check = generated.get('hook', '')
        is_similar, similarity_msg = memory_service.check_similarity(current_user.id, prompt, hook_to_check)
        
        results[m] = {
            "data": generated,
            "analysis": analysis,
            "similarity": {
                "is_similar": is_similar,
                "message": similarity_msg
            },
            "efficiency": {
                "score": eff_score,
                "latency": latency,
                "cost_level": cost_levels[m],
                "model_id": m,
                "model_name": groq_service.SUPPORTED_MODELS[m]
            }
        }
        
    db.session.commit()
    
    return jsonify({
        "success": True,
        "results": results
    })

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
    model = request.form.get('model')
    doc_ids = request.form.getlist('document_ids')
    
    if not current_draft_str or not refinement_prompt or not platform or not tone or not topic:
        return jsonify({"success": False, "error": "Missing required refinement parameters."}), 400
        
    try:
        current_draft = json.loads(current_draft_str)
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid current draft JSON format."}), 400
        
    # Resolve document context
    document_context = ""
    if doc_ids:
        docs = Document.query.filter(Document.id.in_(doc_ids), Document.user_id == current_user.id).all()
        for d in docs:
            document_context += f"\n--- Reference Context from Document '{d.filename}' ---\n{d.content_text}\n"

    selected_model = model if model in groq_service.SUPPORTED_MODELS else groq_service.DEFAULT_MODEL
    headers = groq_service.get_groq_client_headers()
    
    system_prompt = (
        "You are an elite copywriting assistant. You are refining an existing social media draft or blog outline.\n"
        "You must apply the user's refinement instruction precisely, improving readability and impact, while retaining the exact same JSON format.\n"
        "Strictly avoid using any emojis or symbols in the content.\n"
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
    if document_context:
        user_prompt += f"\nReference Context / Source Material (Analyse this document data for refinement):\n{document_context}\n"
    
    refined = None
    start_time = time.time()
    
    if headers:
        try:
            payload = {
                "model": selected_model,
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
            logger.error(f"Refinement API call failed: {e}")
            
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
                
    latency = round(time.time() - start_time, 2)
    
    if refined.get("_source") == "fallback":
        # Simulate delay
        mock_delays = {
            "llama-3.1-8b-instant": 0.3,
            "gemma2-9b-it": 0.5,
            "mixtral-8x7b-32768": 0.9,
            "llama-3.3-70b-versatile": 1.5
        }
        delay = mock_delays.get(selected_model, 0.4)
        time.sleep(delay)
        latency = round(delay + random.uniform(-0.02, 0.05), 2)
                
    analysis = analyzer_service.analyze_post_content(platform, refined)
    
    efficiency_score = analyzer_service.calculate_efficiency_score(selected_model, latency, analysis["score"])
    cost_levels = {
        "llama-3.1-8b-instant": "Ultra-Low",
        "gemma2-9b-it": "Low",
        "mixtral-8x7b-32768": "Medium",
        "llama-3.3-70b-versatile": "High"
    }
    cost_level = cost_levels.get(selected_model, "Low")
    
    log_activity(current_user.id)
    
    return jsonify({
        "success": True,
        "data": refined,
        "analysis": analysis,
        "efficiency": {
            "score": efficiency_score,
            "latency": latency,
            "cost_level": cost_level,
            "model_id": selected_model,
            "model_name": groq_service.SUPPORTED_MODELS[selected_model]
        }
    })

@content.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected."}), 400
        
    try:
        content_text = extract_text_from_file(file, file.filename)
        if not content_text.strip():
            return jsonify({"success": False, "error": "Document appears to be empty or unparseable."}), 400
            
        new_doc = Document(
            user_id=current_user.id,
            filename=file.filename,
            content_text=content_text
        )
        db.session.add(new_doc)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "document": {
                "id": new_doc.id,
                "filename": new_doc.filename,
                "created_at": new_doc.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to upload document: {e}"}), 500

@content.route('/delete-document/<int:doc_id>', methods=['POST', 'DELETE'])
@login_required
def delete_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"success": True, "message": "Document deleted."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@content.route('/list-documents', methods=['GET'])
@login_required
def list_documents():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.created_at.desc()).all()
    return jsonify({
        "success": True,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "created_at": d.created_at.strftime('%Y-%m-%d %H:%M')
            } for d in docs
        ]
    })
