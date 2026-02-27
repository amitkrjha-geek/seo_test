from sqlmodel import Session
from ..models.optimization import ContentOptimization
from ..core.nlp_analyzer import analyze_text
from ..integrations.textrazor_client import extract_entities
from ..llm.factory import get_provider
import json


async def analyze_content(
    db: Session,
    optimization_id: str,
    content: str,
    target_keyword: str,
    textrazor_api_key: str | None = None,
    llm_provider_name: str | None = None,
    llm_api_key: str | None = None,
    persona_context: str = "",
    on_progress: callable = None,
) -> ContentOptimization:
    """Run content optimization analysis."""
    optimization = db.get(ContentOptimization, optimization_id)
    if not optimization:
        raise ValueError(f"Optimization {optimization_id} not found")

    try:
        # Step 1: NLP Analysis
        if on_progress:
            await on_progress({"step": "nlp", "message": "Running NLP analysis..."})
        nlp_data = analyze_text(content)

        optimization.readability_score = nlp_data.get("readability_score", 0)
        optimization.grade_level = nlp_data.get("grade_level", 0)
        optimization.keyword_density = json.dumps(nlp_data.get("keyword_density", {}))

        # Step 2: Entity extraction
        entities = []
        if textrazor_api_key:
            if on_progress:
                await on_progress({"step": "entities", "message": "Extracting entities..."})
            try:
                entities = await extract_entities(textrazor_api_key, content)
            except Exception:
                pass
        optimization.entities = json.dumps(entities, default=str)

        # Step 3: Generate optimization suggestions
        if on_progress:
            await on_progress({"step": "suggestions", "message": "Generating optimization suggestions..."})

        suggestions = _generate_suggestions(content, target_keyword, nlp_data, entities)

        # Optional: Use LLM for more detailed suggestions
        if llm_provider_name and llm_api_key:
            try:
                provider = get_provider(llm_provider_name, llm_api_key)
                system = "You are an SEO content optimization expert. Analyze the content and provide specific, actionable improvement suggestions."
                if persona_context:
                    system += f"\n\nBrand context: {persona_context}"

                user_msg = f"""Analyze this content for SEO optimization (keyword: "{target_keyword}"):

Content (first 2000 chars):
{content[:2000]}

NLP Data:
- Readability: {nlp_data.get('readability_score')}
- Word count: {nlp_data.get('word_count')}
- Grade level: {nlp_data.get('grade_level')}

Provide 5-7 specific, actionable suggestions to improve SEO performance. Return as JSON array of objects with "title", "description", "priority" (high/medium/low) fields."""

                llm_suggestions = await provider.complete(system, user_msg)
                try:
                    parsed = json.loads(llm_suggestions)
                    if isinstance(parsed, list):
                        suggestions.extend(parsed)
                except json.JSONDecodeError:
                    suggestions.append({"title": "AI Analysis", "description": llm_suggestions, "priority": "medium"})
            except Exception:
                pass

        optimization.suggestions = json.dumps(suggestions, default=str)

        # Step 4: E-E-A-T Score
        eeat = _calculate_eeat_score(content, entities)
        optimization.eeat_score = json.dumps(eeat)

        db.add(optimization)
        db.commit()
        db.refresh(optimization)

        if on_progress:
            await on_progress({"step": "done", "message": "Optimization analysis complete!"})

        return optimization

    except Exception:
        db.add(optimization)
        db.commit()
        raise


def _generate_suggestions(content: str, keyword: str, nlp_data: dict, entities: list) -> list[dict]:
    """Generate rule-based optimization suggestions."""
    suggestions = []
    keyword_lower = keyword.lower()
    content_lower = content.lower()
    word_count = nlp_data.get("word_count", 0)

    # Word count check
    if word_count < 300:
        suggestions.append({
            "title": "Content too short",
            "description": f"Content is only {word_count} words. Aim for at least 1,500 words for competitive ranking.",
            "priority": "high",
        })
    elif word_count < 1000:
        suggestions.append({
            "title": "Consider longer content",
            "description": f"Content is {word_count} words. Most top-ranking pages have 1,500+ words.",
            "priority": "medium",
        })

    # Readability
    readability = nlp_data.get("readability_score", 0)
    if readability < 40:
        suggestions.append({
            "title": "Improve readability",
            "description": f"Readability score is {readability:.0f}. Use shorter sentences and simpler words. Aim for 60-70.",
            "priority": "high",
        })
    elif readability > 85:
        suggestions.append({
            "title": "Content may be too simple",
            "description": f"Readability score is {readability:.0f}. Consider adding more depth and technical detail.",
            "priority": "low",
        })

    # Keyword usage
    keyword_count = content_lower.count(keyword_lower)
    if keyword_count == 0:
        suggestions.append({
            "title": "Target keyword missing",
            "description": f'The keyword "{keyword}" does not appear in the content.',
            "priority": "high",
        })
    elif keyword_count < 3:
        suggestions.append({
            "title": "Increase keyword usage",
            "description": f'"{keyword}" appears only {keyword_count} time(s). Include it naturally 3-5 times.',
            "priority": "medium",
        })

    # First paragraph check
    first_para = content_lower[:300]
    if keyword_lower not in first_para:
        suggestions.append({
            "title": "Add keyword to introduction",
            "description": "Include your target keyword in the first paragraph for better relevance signals.",
            "priority": "medium",
        })

    # Heading check
    if "## " not in content:
        suggestions.append({
            "title": "Add subheadings",
            "description": "Use H2 and H3 headings to structure content. Improves readability and SEO.",
            "priority": "high",
        })

    return suggestions


def _calculate_eeat_score(content: str, entities: list) -> dict:
    """Simple E-E-A-T score estimation."""
    score = {
        "experience": 0,
        "expertise": 0,
        "authority": 0,
        "trust": 0,
        "total": 0,
    }

    content_lower = content.lower()

    # Experience signals
    experience_words = ["i've", "we've", "our experience", "in my experience", "we found", "we tested", "first-hand"]
    for word in experience_words:
        if word in content_lower:
            score["experience"] += 5
    score["experience"] = min(score["experience"], 25)

    # Expertise signals
    if entities and len(entities) >= 5:
        score["expertise"] += 10
    if len(content.split()) > 1500:
        score["expertise"] += 10
    if "## " in content:
        score["expertise"] += 5
    score["expertise"] = min(score["expertise"], 25)

    # Authority signals
    authority_words = ["according to", "research shows", "study", "data", "statistics", "expert"]
    for word in authority_words:
        if word in content_lower:
            score["authority"] += 5
    score["authority"] = min(score["authority"], 25)

    # Trust signals
    trust_words = ["source", "reference", "citation", "peer-reviewed", "verified", "updated"]
    for word in trust_words:
        if word in content_lower:
            score["trust"] += 5
    score["trust"] = min(score["trust"], 25)

    score["total"] = score["experience"] + score["expertise"] + score["authority"] + score["trust"]
    return score
