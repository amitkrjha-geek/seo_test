from typing import AsyncIterator
from sqlmodel import Session
from ..models.content import ContentDraft, ContentStatus, ContentVersion
from ..models.content_brief import ContentBrief
from ..llm.factory import get_provider
from ..core.nlp_analyzer import analyze_text
import json
import traceback

WRITER_SYSTEM_PROMPT = """You are an expert SEO content writer. Write high-quality, SEO-optimized content based on the provided brief. Follow these rules:

1. Use the exact H2/H3 heading structure from the brief
2. Write naturally — avoid keyword stuffing
3. Include the target keyword in the first paragraph, H1, and naturally throughout
4. Use short paragraphs (2-3 sentences max)
5. Include relevant internal linking anchor text suggestions as [Link: anchor text]
6. Add E-E-A-T signals: expert quotes, data citations, personal experience hooks
7. Write in markdown format
8. Aim for the word count target specified in the brief"""

WRITER_WITH_PERSONA = """

## Brand Voice & Style
{persona_context}

Write ALL content matching this brand's voice, tone, and style guidelines exactly."""


async def write_content(
    db: Session,
    draft_id: str,
    brief_json: str,
    target_keyword: str,
    llm_provider_name: str = "anthropic",
    llm_api_key: str = "",
    llm_model: str | None = None,
    persona_context: str = "",
    on_progress: callable = None,
) -> ContentDraft:
    """Write SEO content using LLM based on a brief."""
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")

    draft.status = ContentStatus.WRITING
    draft.llm_provider = llm_provider_name
    db.add(draft)
    db.commit()

    try:
        system_prompt = WRITER_SYSTEM_PROMPT
        if persona_context:
            system_prompt += WRITER_WITH_PERSONA.format(persona_context=persona_context)

        user_prompt = f"""Write comprehensive SEO content for the keyword: "{target_keyword}"

Content Brief:
{brief_json}

Write the full article in markdown format."""

        if on_progress:
            await on_progress({"step": "writing", "message": "AI is writing content..."})

        provider = get_provider(llm_provider_name, llm_api_key, llm_model)
        content = await provider.complete(system_prompt, user_prompt, max_tokens=8192)

        # Score the content
        nlp_result = analyze_text(content)
        seo_score = _calculate_seo_score(content, target_keyword, nlp_result)

        draft.body = content
        draft.seo_score = seo_score
        draft.status = ContentStatus.DRAFT
        db.add(draft)

        # Save version
        version = ContentVersion(
            draft_id=draft.id,
            body=content,
            version_number=1,
            llm_provider=llm_provider_name,
        )
        db.add(version)

        db.commit()
        db.refresh(draft)

        if on_progress:
            await on_progress({"step": "done", "message": f"Content written! SEO Score: {seo_score}/100"})

        return draft

    except Exception as e:
        draft.status = ContentStatus.FAILED
        db.add(draft)
        db.commit()
        raise


async def stream_content(
    brief_json: str,
    target_keyword: str,
    llm_provider_name: str = "anthropic",
    llm_api_key: str = "",
    llm_model: str | None = None,
    persona_context: str = "",
) -> AsyncIterator[str]:
    """Stream content writing for real-time display."""
    system_prompt = WRITER_SYSTEM_PROMPT
    if persona_context:
        system_prompt += WRITER_WITH_PERSONA.format(persona_context=persona_context)

    user_prompt = f"""Write comprehensive SEO content for the keyword: "{target_keyword}"

Content Brief:
{brief_json}

Write the full article in markdown format."""

    provider = get_provider(llm_provider_name, llm_api_key, llm_model)
    async for chunk in provider.stream(system_prompt, user_prompt, max_tokens=8192):
        yield chunk


INLINE_PROMPTS = {
    "improve": "Improve the following text. Make it clearer, more engaging, and better written. Return ONLY the improved text, no explanations.",
    "shorten": "Make the following text shorter and more concise while keeping the key message. Return ONLY the shortened text.",
    "expand": "Expand the following text with more detail, examples, and depth. Return ONLY the expanded text.",
    "fix_grammar": "Fix all grammar, spelling, and punctuation errors in the following text. Return ONLY the corrected text.",
    "change_tone": "Rewrite the following text in a more professional and authoritative tone. Return ONLY the rewritten text.",
    "translate": "Translate the following text to English (if not already in English, keep it in English). Return ONLY the translated text.",
}


async def stream_inline_edit(
    text: str,
    action: str,
    llm_provider_name: str = "anthropic",
    llm_api_key: str = "",
    llm_model: str | None = None,
    persona_context: str = "",
) -> AsyncIterator[str]:
    """Stream inline AI text editing for bubble menu actions."""
    system_prompt = INLINE_PROMPTS.get(action, INLINE_PROMPTS["improve"])
    if persona_context:
        system_prompt += f"\n\nBrand voice context:\n{persona_context}"

    provider = get_provider(llm_provider_name, llm_api_key, llm_model)
    async for chunk in provider.stream(system_prompt, text, max_tokens=4096):
        yield chunk


def _calculate_seo_score(content: str, keyword: str, nlp_data: dict) -> int:
    """Calculate a basic SEO score for the content."""
    score = 0
    keyword_lower = keyword.lower()
    content_lower = content.lower()

    # Keyword in content (20 pts)
    if keyword_lower in content_lower:
        score += 10
        # Keyword in first 200 chars
        if keyword_lower in content_lower[:200]:
            score += 10

    # Word count (20 pts)
    word_count = nlp_data.get("word_count", 0)
    if word_count >= 1500:
        score += 20
    elif word_count >= 1000:
        score += 15
    elif word_count >= 500:
        score += 10

    # Readability (20 pts)
    readability = nlp_data.get("readability_score", 0)
    if 60 <= readability <= 80:
        score += 20
    elif 40 <= readability <= 90:
        score += 15
    elif readability > 0:
        score += 10

    # Has headings (15 pts)
    if "## " in content:
        score += 10
    if "### " in content:
        score += 5

    # Paragraph structure (10 pts)
    paragraphs = [p for p in content.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    if len(paragraphs) >= 5:
        score += 10
    elif len(paragraphs) >= 3:
        score += 5

    # Has internal link suggestions (5 pts)
    if "[Link:" in content or "[link:" in content:
        score += 5

    # Keyword density (10 pts) — not too low, not too high
    density = content_lower.count(keyword_lower) / max(word_count / 100, 1)
    if 0.5 <= density <= 3.0:
        score += 10
    elif density > 0:
        score += 5

    return min(score, 100)
