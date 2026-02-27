from sqlmodel import Session
from ..models.content_brief import ContentBrief, BriefStatus
from ..llm.factory import get_provider
from ..integrations.serper import search_serp
import json
import traceback

BRIEF_SYSTEM_PROMPT = """You are an expert SEO content strategist. Generate a comprehensive content brief based on SERP analysis data and the target keyword. The brief should include:

1. **Target Keyword & Intent**: Primary keyword, search intent classification
2. **Recommended Title**: SEO-optimized title (50-60 chars)
3. **Meta Description**: Compelling meta description (150-160 chars)
4. **Content Outline**: H2/H3 heading structure with key points under each
5. **Word Count Target**: Based on competitor analysis
6. **Key Topics to Cover**: Must-include topics from SERP analysis
7. **Internal Linking Opportunities**: Suggested link anchors
8. **Content Angle**: Unique angle to differentiate from competitors
9. **E-E-A-T Signals**: How to demonstrate expertise, experience, authority, trust

Return the brief as a structured JSON object."""

BRIEF_WITH_PERSONA = """

## Brand Voice Guidelines
{persona_context}

Ensure all recommendations align with this brand's voice, tone, and target audience."""


async def generate_brief(
    db: Session,
    brief_id: str,
    keyword: str,
    serper_api_key: str | None = None,
    llm_provider_name: str = "anthropic",
    llm_api_key: str = "",
    llm_model: str | None = None,
    persona_context: str = "",
    on_progress: callable = None,
) -> ContentBrief:
    """Generate a content brief using SERP data and LLM."""
    brief = db.get(ContentBrief, brief_id)
    if not brief:
        raise ValueError(f"Brief {brief_id} not found")

    brief.status = BriefStatus.GENERATING
    db.add(brief)
    db.commit()

    try:
        # Step 1: Gather SERP insights
        serp_insights = {}
        if serper_api_key:
            if on_progress:
                await on_progress({"step": "serp", "message": "Gathering SERP insights..."})
            try:
                serp_data = await search_serp(serper_api_key, keyword, num=10)
                serp_insights = {
                    "organic_results": [
                        {"title": r.get("title"), "snippet": r.get("snippet"), "link": r.get("link")}
                        for r in serp_data.get("organic", [])[:5]
                    ],
                    "people_also_ask": [
                        q.get("question") for q in serp_data.get("peopleAlsoAsk", [])
                    ],
                    "related_searches": [
                        r.get("query") for r in serp_data.get("relatedSearches", [])
                    ],
                }
            except Exception:
                pass

        brief.serp_insights = json.dumps(serp_insights, default=str)

        # Step 2: Generate brief with LLM
        if on_progress:
            await on_progress({"step": "generate", "message": "Generating content brief with AI..."})

        system_prompt = BRIEF_SYSTEM_PROMPT
        if persona_context:
            system_prompt += BRIEF_WITH_PERSONA.format(persona_context=persona_context)

        user_prompt = f"""Generate a content brief for the target keyword: "{keyword}"

SERP Analysis Data:
{json.dumps(serp_insights, indent=2, default=str)}

Create a comprehensive, actionable content brief."""

        provider = get_provider(llm_provider_name, llm_api_key, llm_model)
        result = await provider.complete(system_prompt, user_prompt)

        # Try to parse as JSON, fall back to raw text
        try:
            outline = json.loads(result)
        except json.JSONDecodeError:
            outline = {"raw_brief": result}

        brief.outline = json.dumps(outline, default=str)
        brief.status = BriefStatus.READY
        db.add(brief)
        db.commit()
        db.refresh(brief)

        if on_progress:
            await on_progress({"step": "done", "message": "Content brief generated!"})

        return brief

    except Exception as e:
        brief.status = BriefStatus.FAILED
        db.add(brief)
        db.commit()
        raise
