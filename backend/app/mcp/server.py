"""MCP Server for SEO Agency - exposes all 7 pipeline steps as tools."""
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
from mcp.server.lowlevel.helper_types import ReadResourceContents

from ..database import get_session
from ..models.audit import SiteAudit, AuditIssue
from ..models.keyword import KeywordResearch, Keyword
from ..models.competitor import CompetitorAnalysis
from ..models.content_brief import ContentBrief
from ..models.content import ContentDraft
from ..models.optimization import ContentOptimization
from ..models.brand_persona import BrandPersona
from ..models.project_api_key import ProjectApiKey
from ..models.project import Project
from ..models.rank_tracking import RankTracker
from ..services.audit_service import run_audit
from ..services.keyword_service import run_keyword_research
from ..services.competitor_service import run_competitor_analysis
from ..services.brief_service import generate_brief
from ..services.content_service import write_content
from ..services.optimization_service import analyze_content
from ..services.tracking_service import check_rankings, check_core_web_vitals
from ..services.crypto_service import decrypt_api_key
from sqlmodel import select, func

app = Server("seo-agency")


def _get_project_key(db, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None


def _get_persona_context(db, project_id: str) -> str:
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()
    return persona.to_prompt_context() if persona else ""


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="seo_audit",
            description="Run a full SEO site audit on a URL. Returns health score (0-100) and list of issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to audit"},
                    "project_id": {"type": "string", "description": "Project ID (optional, for API keys)"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="seo_keywords",
            description="Research keywords from multiple sources (Google Autocomplete, Serper, Trends). Returns clustered keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "seed_keyword": {"type": "string", "description": "Seed keyword to research"},
                    "project_id": {"type": "string", "description": "Project ID (optional, for API keys)"},
                },
                "required": ["seed_keyword"],
            },
        ),
        Tool(
            name="seo_competitors",
            description="Analyze SERP competitors for a keyword. Returns gap analysis and competitor details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Target keyword"},
                    "url": {"type": "string", "description": "Your URL (optional, for gap comparison)"},
                    "project_id": {"type": "string", "description": "Project ID (required for Serper key)"},
                },
                "required": ["keyword", "project_id"],
            },
        ),
        Tool(
            name="seo_brief",
            description="Generate an SEO content brief from SERP analysis. Uses brand persona if project_id provided.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Target keyword for the brief"},
                    "project_id": {"type": "string", "description": "Project ID (required for API keys and persona)"},
                    "provider": {"type": "string", "description": "LLM provider (anthropic/openai/google_ai)", "default": "anthropic"},
                },
                "required": ["keyword", "project_id"],
            },
        ),
        Tool(
            name="seo_write",
            description="Write SEO-optimized content using AI. Applies brand persona from the project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Target keyword"},
                    "brief": {"type": "string", "description": "Content brief (JSON or text)"},
                    "project_id": {"type": "string", "description": "Project ID (required for API keys and persona)"},
                    "provider": {"type": "string", "description": "LLM provider", "default": "anthropic"},
                },
                "required": ["keyword", "project_id"],
            },
        ),
        Tool(
            name="seo_optimize",
            description="Analyze and optimize content for SEO. Returns readability, entities, keyword density, and suggestions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to optimize"},
                    "keyword": {"type": "string", "description": "Target keyword"},
                    "project_id": {"type": "string", "description": "Project ID (optional)"},
                },
                "required": ["content", "keyword"],
            },
        ),
        Tool(
            name="seo_track",
            description="Check rankings for keywords and Core Web Vitals for a URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to check CWV for"},
                    "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to check rankings"},
                    "project_id": {"type": "string", "description": "Project ID (required)"},
                },
                "required": ["project_id"],
            },
        ),
    ]


@app.list_resources()
async def list_resources() -> list[Resource]:
    with next(get_session()) as db:
        projects = db.exec(select(Project)).all()

    resources = [
        Resource(
            uri="seo://projects",
            name="All Projects",
            description="List all SEO projects",
            mimeType="application/json",
        ),
    ]
    for p in projects:
        resources.extend([
            Resource(
                uri=f"seo://projects/{p.id}",
                name=f"Project: {p.name}",
                description=f"Detail for {p.name} ({p.domain}) with pipeline status",
                mimeType="application/json",
            ),
            Resource(
                uri=f"seo://projects/{p.id}/keywords",
                name=f"Keywords: {p.name}",
                description=f"All keyword research for {p.name}",
                mimeType="application/json",
            ),
            Resource(
                uri=f"seo://projects/{p.id}/audits",
                name=f"Audits: {p.name}",
                description=f"Audit history for {p.name}",
                mimeType="application/json",
            ),
        ])
    return resources


@app.read_resource()
async def read_resource(uri) -> list[ReadResourceContents]:
    uri_str = str(uri)
    # Parse seo://projects/... URIs
    prefix = "seo://"
    if uri_str.startswith(prefix):
        path = uri_str[len(prefix):]
    else:
        path = uri_str
    parts = [p for p in path.split("/") if p]

    with next(get_session()) as db:
        if parts == ["projects"]:
            data = _resource_all_projects(db)
        elif len(parts) == 2 and parts[0] == "projects":
            data = _resource_project_detail(db, parts[1])
        elif len(parts) == 3 and parts[0] == "projects" and parts[2] == "keywords":
            data = _resource_project_keywords(db, parts[1])
        elif len(parts) == 3 and parts[0] == "projects" and parts[2] == "audits":
            data = _resource_project_audits(db, parts[1])
        else:
            data = json.dumps({"error": f"Unknown resource: {uri_str}"})

    return [ReadResourceContents(content=data, mime_type="application/json")]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    with next(get_session()) as db:
        try:
            if name == "seo_audit":
                return await _handle_audit(db, arguments)
            elif name == "seo_keywords":
                return await _handle_keywords(db, arguments)
            elif name == "seo_competitors":
                return await _handle_competitors(db, arguments)
            elif name == "seo_brief":
                return await _handle_brief(db, arguments)
            elif name == "seo_write":
                return await _handle_write(db, arguments)
            elif name == "seo_optimize":
                return await _handle_optimize(db, arguments)
            elif name == "seo_track":
                return await _handle_track(db, arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_audit(db, args):
    url = args["url"]
    project_id = args.get("project_id")
    ps_key = _get_project_key(db, project_id, "pagespeed") if project_id else None

    audit = SiteAudit(project_id=project_id or "mcp", url=url, initiated_by="mcp")
    db.add(audit)
    db.commit()
    db.refresh(audit)

    result = await run_audit(db, audit.id, url, pagespeed_api_key=ps_key)
    return [TextContent(type="text", text=json.dumps({
        "health_score": result.health_score,
        "status": result.status,
        "url": url,
    }, indent=2, default=str))]


async def _handle_keywords(db, args):
    seed = args["seed_keyword"]
    project_id = args.get("project_id")
    serper_key = _get_project_key(db, project_id, "serper") if project_id else None

    research = KeywordResearch(project_id=project_id or "mcp", seed_keyword=seed)
    db.add(research)
    db.commit()
    db.refresh(research)

    result = await run_keyword_research(db, research.id, seed, serper_api_key=serper_key)
    kws = db.exec(select(Keyword).where(Keyword.research_id == result.id)).all()

    return [TextContent(type="text", text=json.dumps({
        "seed_keyword": seed,
        "total_keywords": len(kws),
        "keywords": [{"keyword": k.keyword, "source": k.source, "intent": k.intent, "cluster": k.cluster} for k in kws[:50]],
    }, indent=2, default=str))]


async def _handle_competitors(db, args):
    keyword = args["keyword"]
    project_id = args["project_id"]
    serper_key = _get_project_key(db, project_id, "serper")

    analysis = CompetitorAnalysis(project_id=project_id, target_keyword=keyword)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    result = await run_competitor_analysis(db, analysis.id, keyword, own_url=args.get("url"), serper_api_key=serper_key)
    return [TextContent(type="text", text=json.dumps({
        "keyword": keyword,
        "status": result.status,
        "gap_data": json.loads(result.gap_data) if result.gap_data else None,
    }, indent=2, default=str))]


async def _handle_brief(db, args):
    keyword = args["keyword"]
    project_id = args["project_id"]
    provider = args.get("provider", "anthropic")

    brief = ContentBrief(project_id=project_id, target_keyword=keyword)
    db.add(brief)
    db.commit()
    db.refresh(brief)

    serper_key = _get_project_key(db, project_id, "serper")
    llm_key = _get_project_key(db, project_id, provider)
    persona = _get_persona_context(db, project_id)

    result = await generate_brief(db, brief.id, keyword, serper_api_key=serper_key,
                                   llm_provider_name=provider, llm_api_key=llm_key or "",
                                   persona_context=persona)
    return [TextContent(type="text", text=json.dumps({
        "keyword": keyword,
        "status": result.status,
        "outline": json.loads(result.outline) if result.outline else None,
    }, indent=2, default=str))]


async def _handle_write(db, args):
    keyword = args["keyword"]
    project_id = args["project_id"]
    provider = args.get("provider", "anthropic")
    brief_json = args.get("brief", "{}")

    draft = ContentDraft(project_id=project_id, title=keyword, llm_provider=provider, created_by="mcp")
    db.add(draft)
    db.commit()
    db.refresh(draft)

    llm_key = _get_project_key(db, project_id, provider)
    persona = _get_persona_context(db, project_id)

    result = await write_content(db, draft.id, brief_json, keyword,
                                  llm_provider_name=provider, llm_api_key=llm_key or "",
                                  persona_context=persona)
    return [TextContent(type="text", text=result.body[:5000] if result.body else "No content generated")]


async def _handle_optimize(db, args):
    content = args["content"]
    keyword = args["keyword"]
    project_id = args.get("project_id")

    opt = ContentOptimization(draft_id="mcp-inline")
    db.add(opt)
    db.commit()
    db.refresh(opt)

    tr_key = _get_project_key(db, project_id, "textrazor") if project_id else None
    persona = _get_persona_context(db, project_id) if project_id else ""

    result = await analyze_content(db, opt.id, content, keyword, textrazor_api_key=tr_key, persona_context=persona)
    return [TextContent(type="text", text=json.dumps({
        "readability_score": result.readability_score,
        "grade_level": result.grade_level,
        "suggestions": json.loads(result.suggestions) if result.suggestions else [],
        "eeat_score": json.loads(result.eeat_score) if result.eeat_score else {},
    }, indent=2, default=str))]


async def _handle_track(db, args):
    project_id = args["project_id"]
    url = args.get("url")
    keywords = args.get("keywords", [])

    results = {}
    if keywords:
        project = db.get(Project, project_id)
        domain = project.domain if project else ""
        serper_key = _get_project_key(db, project_id, "serper")
        results["rankings"] = await check_rankings(db, project_id, keywords, domain, serper_api_key=serper_key)

    if url:
        ps_key = _get_project_key(db, project_id, "pagespeed")
        results["cwv"] = await check_core_web_vitals(db, project_id, url, pagespeed_api_key=ps_key)

    return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]


def _resource_all_projects(db) -> str:
    projects = db.exec(select(Project)).all()
    return json.dumps([
        {
            "id": p.id,
            "name": p.name,
            "domain": p.domain,
            "business_type": p.business_type,
            "created_at": str(p.created_at),
        }
        for p in projects
    ], indent=2, default=str)


def _resource_project_detail(db, project_id: str) -> str:
    project = db.get(Project, project_id)
    if not project:
        return json.dumps({"error": "Project not found"})

    audit_count = db.exec(
        select(func.count()).select_from(SiteAudit).where(SiteAudit.project_id == project_id)
    ).one()
    latest_audit = db.exec(
        select(SiteAudit).where(SiteAudit.project_id == project_id).order_by(SiteAudit.created_at.desc())
    ).first()
    kw_count = db.exec(
        select(func.count()).select_from(KeywordResearch).where(KeywordResearch.project_id == project_id)
    ).one()
    comp_count = db.exec(
        select(func.count()).select_from(CompetitorAnalysis).where(CompetitorAnalysis.project_id == project_id)
    ).one()
    brief_count = db.exec(
        select(func.count()).select_from(ContentBrief).where(ContentBrief.project_id == project_id)
    ).one()
    draft_count = db.exec(
        select(func.count()).select_from(ContentDraft).where(ContentDraft.project_id == project_id)
    ).one()
    tracked_count = db.exec(
        select(func.count()).select_from(RankTracker).where(
            RankTracker.project_id == project_id, RankTracker.is_active == True
        )
    ).one()
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()

    return json.dumps({
        "id": project.id,
        "name": project.name,
        "domain": project.domain,
        "business_type": project.business_type,
        "created_at": str(project.created_at),
        "pipeline_status": {
            "audits": audit_count,
            "latest_health_score": latest_audit.health_score if latest_audit else None,
            "keyword_research_runs": kw_count,
            "competitor_analyses": comp_count,
            "content_briefs": brief_count,
            "content_drafts": draft_count,
            "tracked_keywords": tracked_count,
        },
        "has_persona": persona is not None and bool(persona.brand_name),
    }, indent=2, default=str)


def _resource_project_keywords(db, project_id: str) -> str:
    researches = db.exec(
        select(KeywordResearch).where(KeywordResearch.project_id == project_id)
        .order_by(KeywordResearch.created_at.desc())
    ).all()

    result = []
    for r in researches:
        kws = db.exec(select(Keyword).where(Keyword.research_id == r.id)).all()
        result.append({
            "research_id": r.id,
            "seed_keyword": r.seed_keyword,
            "status": r.status,
            "created_at": str(r.created_at),
            "keywords": [
                {
                    "keyword": k.keyword,
                    "source": k.source,
                    "search_volume": k.search_volume,
                    "difficulty": k.difficulty,
                    "intent": k.intent,
                    "cluster": k.cluster,
                    "is_selected": k.is_selected,
                }
                for k in kws
            ],
        })
    return json.dumps(result, indent=2, default=str)


def _resource_project_audits(db, project_id: str) -> str:
    audits = db.exec(
        select(SiteAudit).where(SiteAudit.project_id == project_id)
        .order_by(SiteAudit.created_at.desc())
    ).all()

    result = []
    for a in audits:
        issues = db.exec(select(AuditIssue).where(AuditIssue.audit_id == a.id)).all()
        result.append({
            "id": a.id,
            "url": a.url,
            "status": a.status,
            "health_score": a.health_score,
            "created_at": str(a.created_at),
            "issues": [
                {
                    "category": i.category,
                    "severity": i.severity,
                    "title": i.title,
                    "recommendation": i.recommendation,
                }
                for i in issues
            ],
        })
    return json.dumps(result, indent=2, default=str)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
