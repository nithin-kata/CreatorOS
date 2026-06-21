import json
import re
from app.models import Content

def get_memory_context(user_id):
    """
    Retrieves the last 10 saved contents for the user and forms a context block
    for the AI to avoid repetitive ideas.
    """
    recent_posts = Content.query.filter_by(user_id=user_id).order_by(Content.created_at.desc()).limit(10).all()
    if not recent_posts:
        return "No recent posts saved yet. This is a fresh slate."

    context_lines = []
    for idx, post in enumerate(recent_posts, 1):
        # Extract hook if available in stored content JSON
        hook = ""
        try:
            content_data = json.loads(post.content)
            hook = content_data.get('hook', '')
        except Exception:
            hook = post.content[:60] + "..."
            
        context_lines.append(f"{idx}. Topic: {post.topic} (Platform: {post.platform}) | Hook: '{hook}'")
        
    return "\n".join(context_lines)

def check_similarity(user_id, new_topic, new_hook):
    """
    Determines if the generated topic/hook is too similar to the last 10 saved posts.
    Returns: (is_similar, message)
    """
    recent_posts = Content.query.filter_by(user_id=user_id).order_by(Content.created_at.desc()).limit(10).all()
    if not recent_posts:
        return False, "Not similar to your last 10 posts."

    # Helper function to tokenize and clean text into a set of unique words
    def get_words(text):
        if not text:
            return set()
        text = text.lower()
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return set(w for w in text.split() if len(w) > 3) # Ignore short filler words

    new_words = get_words(new_topic).union(get_words(new_hook))
    if not new_words:
        return False, "Not similar to your last 10 posts."

    for post in recent_posts:
        saved_hook = ""
        try:
            content_data = json.loads(post.content)
            saved_hook = content_data.get('hook', '')
        except Exception:
            saved_hook = post.content
            
        saved_words = get_words(post.topic).union(get_words(saved_hook))
        if not saved_words:
            continue
            
        # Jaccard similarity index
        intersection = new_words.intersection(saved_words)
        union = new_words.union(saved_words)
        similarity = len(intersection) / len(union) if union else 0
        
        # If the similarity is above 40%, we mark it as similar
        if similarity > 0.4:
            return True, f"Similar to your past post on '{post.topic}' ({int(similarity*100)}% overlap)."
            
    return False, "Not similar to your last 10 posts."
