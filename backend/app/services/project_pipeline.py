from app.models.project import ProjectState
from app.models.pipeline import PipelineResult, PipelineStage, QualityInfo

try:
    from app.utils.trace_log import trace_continue, clear_log
except ImportError:
    trace_continue = None
    clear_log = None

from app.engines.discovery import (
    understand_project,
    find_missing_fields,
    generate_questions,
    apply_answers,
    _extract_technologies_from_text,
    _extract_technologies_with_status,
)
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.artifact import create_artifact
from app.services.quality_gate import run_quality_gate
from app.services import project_store


async def start_project(
    idea: str,
    project_id: str | None = None,
) -> PipelineResult:

    project = await understand_project(idea)

    missing_fields = find_missing_fields(project)

    if missing_fields:

        questions = await generate_questions(
            project,
            missing_fields,
        )

        return PipelineResult(
            stage=PipelineStage.DISCOVERY,
            complete=False,
            project=project,
            missing_fields=missing_fields,
            questions=questions,
        )

    return await _complete_pipeline(project, project_id=project_id)


async def continue_project(
    project_data: dict,
    answers: dict,
    conversation_history: list[dict] | None = None,
    project_id: str | None = None,
) -> PipelineResult:

    project = ProjectState(**project_data)

    if conversation_history is None:
        conversation_history = []

    if trace_continue:
        trace_continue(
            step="incoming",
            project_data=project_data,
            answers=answers,
            conversation_history=conversation_history,
            answer_list=[],
            force_applied=[],
            project_after_force=project.model_dump(),
            missing_fields=[],
            answered_fields=[],
            remaining_missing=[],
            raw_questions=[],
            deduplicated=[],
        )

    answer_list = [
        {"field": field, "answer": str(value)}
        for field, value in answers.items()
    ]

    # Add new answers to conversation history
    for item in answer_list:
        # Avoid adding duplicates
        already_asked = any(
            h.get("field") == item["field"]
            for h in conversation_history
        )
        if not already_asked:
            conversation_history.append(item)

    updated_project = await apply_answers(
        project,
        answer_list,
    )

    # ------------------------------------------------------------------
    # SOURCE FIX: Force-apply every answered field onto ProjectState.
    # apply_answers() is an LLM call that may not reliably extract
    # the answer into the correct field.  When it fails, the field
    # stays null, find_missing_fields() lists it again, and the next
    # question generation re-asks the same question.
    #
    # By writing the answer directly onto the project, we guarantee
    # the field is never null after the user has answered it.
    # ------------------------------------------------------------------
    for item in answer_list:
        field_name = item["field"]
        answer_value = item["answer"]
        current_value = getattr(updated_project, field_name, None)

        # Only force-set if the LLM left the field empty / null
        if current_value is None or (
            isinstance(current_value, list) and len(current_value) == 0
        ):
            # For list fields, wrap the string in a list
            if field_name in (
                "target_users", "core_features", "technologies",
                "integrations", "constraints",
            ):
                setattr(updated_project, field_name, [answer_value])
            else:
                setattr(updated_project, field_name, answer_value)

    # ------------------------------------------------------------------
    # Merge user_selected_technologies from FULL conversation history.
    # Extract technology names from ALL previous answers (not just current)
    # to ensure user-selected technologies are always tracked.
    # ------------------------------------------------------------------
    all_answers = []
    for h in conversation_history:
        all_answers.append({"field": h["field"], "answer": h.get("answer", "")})
    # Also include current answers (avoid duplicates)
    current_fields = {a["field"] for a in all_answers}
    for a in answer_list:
        if a["field"] not in current_fields:
            all_answers.append(a)
    _merge_user_selected_technologies(updated_project, all_answers)

    # ------------------------------------------------------------------
    # Now check missing fields AFTER the deterministic fix.
    # ------------------------------------------------------------------
    missing_fields = find_missing_fields(updated_project)

    # Build list of already-answered fields (from full conversation)
    answered_fields = [h["field"] for h in conversation_history]

    if missing_fields:

        # Filter out fields already answered — deterministic, no LLM
        remaining_missing = [
            f for f in missing_fields if f not in answered_fields
        ]

        if not remaining_missing:
            # All remaining fields are already answered — discovery done
            return await _complete_pipeline(updated_project, project_id=project_id)

        questions = await generate_questions(
            updated_project,
            remaining_missing,
            asked_questions=conversation_history,
            answered_fields=answered_fields,
        )

        # --------------------------------------------------------------
        # POST-GENERATION DEDUP: deterministic filter.
        # Remove any question whose field:
        #  1. the user already answered (conversation history)
        #  2. is NOT in remaining_missing (field already has a value)
        #  3. is a duplicate of another question in the same batch
        #  4. has a non-null value in the project state (belt-and-suspenders)
        #
        # The LLM often generates questions about fields that already
        # have values (e.g. platform inferred by AI), even though
        # they are not in remaining_missing.  This filter catches that.
        # --------------------------------------------------------------
        remaining_missing_set = set(remaining_missing)
        deduplicated = []
        seen_fields = set(answered_fields)  # start with all answered
        for q in questions:
            field = q.get("field", "")
            if field in seen_fields or field not in remaining_missing_set:
                continue

            # Belt-and-suspenders: check the project state directly.
            # If the field already has a value, skip it regardless.
            project_value = getattr(updated_project, field, None)
            if project_value is not None and not (
                isinstance(project_value, list) and len(project_value) == 0
            ):
                continue

            deduplicated.append(q)
            seen_fields.add(field)

        if trace_continue:
            trace_continue(
                step="continue",
                project_data=project.model_dump(),
                answers=answers,
                conversation_history=conversation_history,
                answer_list=answer_list,
                force_applied=[
                    {"field": a["field"], "value": a["answer"]}
                    for a in answer_list
                ],
                project_after_force=updated_project.model_dump(),
                missing_fields=missing_fields,
                answered_fields=answered_fields,
                remaining_missing=remaining_missing,
                raw_questions=questions,
                deduplicated=deduplicated,
            )

        # CRITICAL: Ensure 'technologies' is always asked if it's still missing.
        # The user's technology choices are the most important input for
        # architecture generation. Discovery MUST NOT complete without them.
        if "technologies" in remaining_missing:
            has_tech_question = any(
                q.get("field") == "technologies" for q in deduplicated
            )
            if not has_tech_question:
                # Force-add a technologies question
                deduplicated.insert(0, {
                    "field": "technologies",
                    "question": (
                        "What programming languages, frameworks, databases, "
                        "and tools do you want to use for this project? "
                        "For example: Python, Django, PostgreSQL, React, Docker."
                    ),
                    "reason": "Technology stack selection",
                })

        return PipelineResult(
            stage=PipelineStage.DISCOVERY,
            complete=False,
            project=updated_project,
            missing_fields=remaining_missing,
            questions=deduplicated,
            conversation_history=conversation_history,
        )

    return await _complete_pipeline(updated_project, project_id=project_id)


async def _complete_pipeline(
    project: ProjectState,
    project_id: str | None = None,
) -> PipelineResult:

    requirements = await generate_requirements(project)

    architecture = await generate_architecture(
        project,
        requirements,
    )

    context = await generate_context(
        project,
        requirements,
        architecture,
    )

    # Run quality gate (validation + agent readiness)
    quality_gate = run_quality_gate(
        project, requirements, architecture, context,
    )

    quality_info = QualityInfo(
        overall_score=quality_gate.overall_score,
        validation_score=quality_gate.validation_score,
        readiness_score=quality_gate.readiness_score,
        ready_for_agent=quality_gate.ready_for_agent,
        checks=quality_gate.checks,
        warnings_count=len(quality_gate.warnings),
        assumptions_count=len(quality_gate.assumptions),
        warnings=quality_gate.warnings,
        assumptions=quality_gate.assumptions,
        errors=quality_gate.errors,
        rejection_reasons=quality_gate.rejection_reasons,
        tech_preservation=quality_gate.tech_preservation.model_dump(),
    )

    if project_id:
        from app.models.validation import ContextValidationResult
        validation = ContextValidationResult(
            valid=quality_gate.validation_score >= 80,
            score=quality_gate.validation_score,
        )
        project_store.save_context(
            project_id=project_id,
            requirements=requirements.model_dump(),
            architecture=architecture.model_dump(),
            implementation_context=context.model_dump(),
            validation_result=validation.model_dump(),
            quality_result=quality_info.model_dump(),
        )

    # If quality gate fails, do not create artifact
    if not quality_gate.passed:
        if project_id:
            project_store.update_project(
                project_id,
                name=project.name or "Untitled Project",
                project_data=project.model_dump(),
                status="improvement",
                current_stage="validation",
            )
        return PipelineResult(
            stage=PipelineStage.VALIDATION,
            complete=False,
            project=project,
            quality=quality_info,
        )

    # Quality gate passed — create artifact
    from app.models.validation import ContextValidationResult
    validation = ContextValidationResult(
        valid=True,
        score=quality_gate.validation_score,
    )

    if project_id:
        from app.engines.assembly import assemble_markdown
        markdown = assemble_markdown(context=context, validation=validation)
        stored = project_store.save_artifact(
            project_id=project_id,
            markdown=markdown,
            txt=markdown,
            quality_score=quality_gate.overall_score,
        )
        project_store.update_project(
            project_id,
            name=project.name or "Untitled Project",
            project_data=project.model_dump(),
            status="complete",
            current_stage="complete",
        )
        artifact_id = stored["id"]
    else:
        artifact = create_artifact(context=context, validation=validation)
        artifact_id = artifact.project_id

    return PipelineResult(
        stage=PipelineStage.COMPLETE,
        complete=True,
        project=project,
        project_id=artifact_id,
        download_markdown=f"/export/{artifact_id}/markdown",
        download_txt=f"/export/{artifact_id}/txt",
        quality=quality_info,
    )


# ============================================================
# User-selected technology extraction
# ============================================================

# Technology category keywords for heuristic detection.
# NOTE: Generic domain words ("ai", "sms", "payment", "backend",
# "web", "mobile", "users", "appointments", etc.) are intentionally
# EXCLUDED. They are domain concepts, not concrete technologies.
_TECH_CATEGORY_KEYWORDS = {
    "AI_PROVIDER": ["openai", "anthropic", "claude", "gpt", "tensorflow", "pytorch", "huggingface", "langchain", "llm", "machine learning", "deep learning", "nlp", "openai api"],
    "PAYMENT_PROVIDER": ["stripe", "paypal", "chapa", "telebirr", "budpay", "paystack", "razorpay"],
    "SMS_PROVIDER": ["africas talking", "africa\'s talking", "twilio", "sendgrid"],
    "MAP_PROVIDER": ["google maps", "mapbox", "here maps", "mapbox gl", "leaflet"],
    "DATABASE": ["postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "dynamodb", "supabase", "firebase", "sql server", "mssql", "mariadb", "cassandra"],
    "CLOUD_PROVIDER": ["aws", "amazon web services", "gcp", "google cloud", "azure", "vercel", "netlify", "heroku", "render"],
    "AUTH_PROVIDER": ["auth0", "clerk", "firebase auth", "supabase auth", "jwt", "oauth"],
    "FRONTEND_FRAMEWORK": ["react", "next.js", "vue", "angular", "svelte", "flutter", "react native"],
    "BACKEND_FRAMEWORK": ["node.js", "express", "fastapi", "django", "flask", "spring boot", "laravel", "rails", "asp.net core", "asp.net"],
    "HOSTING": ["docker", "containers", "kubernetes", "aws fargate", "aws ecs", "heroku", "render"],
    "CSS_UI": ["tailwind", "tailwindcss", "bootstrap", "material ui", "shadcn"],
    "ORM": ["prisma", "sequelize", "typeorm", "entity framework", "entity framework core", "sqlalchemy", "django orm"],
    "VITE": ["vite", "webpack"],
}


def _classify_tech_category(tech_name: str, purpose: str = "") -> str:
    """Classify a technology into a semantic category.

    Uses exact name matching rather than substring matching to avoid
    false positives from generic domain words.
    """
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    normalized = normalize_tech_name(tech_name)
    name_lower = tech_name.strip().lower()

    # Reject generic domain words immediately
    if not normalized or normalized in NON_TECH_WORDS or name_lower in NON_TECH_WORDS:
        return "OTHER"

    # Only match concrete technology names, not generic words
    for category, techs in _TECH_CATEGORY_KEYWORDS.items():
        # Exact match against known tech names
        if normalized in techs:
            return category
        if name_lower in techs:
            return category
    return "OTHER"


def _merge_user_selected_technologies(
    project: ProjectState,
    answer_list: list[dict],
) -> None:
    """
    Extract user-selected technologies from answers AND from all project
    text (description, problem, conversation history) and merge them
    into the project's user_selected_technologies list.

    This ensures technologies explicitly mentioned by the user are
    tracked separately from AI-inferred technologies.
    """
    from app.models.project import UserSelectedTechnology

    existing_names = {
        t.name.lower() for t in project.user_selected_technologies
    }

    # Technology-related fields that might contain user tech choices
    tech_fields = {"technologies", "database", "authentication", "integrations"}

    for item in answer_list:
        field = item.get("field", "")
        answer = item.get("answer", "")
        answer_lower = answer.lower()

        if field in tech_fields:
            for tech_name, status in _extract_technologies_with_status(answer):
                name_lower = tech_name.lower()
                if name_lower not in existing_names:
                    project.user_selected_technologies.append(
                        UserSelectedTechnology(
                            name=tech_name,
                            purpose=f"user-specified in {field}",
                            category=_classify_tech_category(tech_name, field),
                            status=status,
                        )
                    )
                    existing_names.add(name_lower)

    # ------------------------------------------------------------------
    # Helper: check if an extracted tech is a variant of an existing one.
    # E.g., "spring" is a variant of "Spring Boot", "fcm" of "Firebase Cloud Messaging".
    # ------------------------------------------------------------------
    from app.utils.tech_normalizer import normalize_tech_name

    existing_normalized = {
        normalize_tech_name(t.name): t.name
        for t in project.user_selected_technologies
    }

    def _is_variant_of_existing(tech_name: str) -> bool:
        """Check if tech_name is a prefix/substring variant of an existing technology."""
        norm = normalize_tech_name(tech_name)
        if not norm:
            return True  # empty = non-tech, skip
        for existing_norm in existing_normalized:
            if not existing_norm:
                continue
            # Exact match — skip
            if norm == existing_norm:
                return True
            # Prefix match: "spring" is prefix of "spring boot"
            if norm.startswith(existing_norm) or existing_norm.startswith(norm):
                return True
            # Substring match: "fcm" is part of "firebase cloud messaging" context
            if norm in existing_norm or existing_norm in norm:
                return True
        return False

    # ------------------------------------------------------------------
    # ALSO: Extract technologies from project text fields.
    # The user may have mentioned technologies in description, problem,
    # or other text fields without them being in the 'technologies' answer.
    # ------------------------------------------------------------------
    text_fields = [
        project.description or "",
        project.problem or "",
        " ".join(project.core_features),
        " ".join(project.constraints),
        project.deployment or "",
        project.database or "",
        project.authentication or "",
    ]

    for text in text_fields:
        if text:
            extracted = _extract_technologies_with_status(text)
            for tech_name, status in extracted:
                name_lower = tech_name.lower()
                if name_lower not in existing_names and not _is_variant_of_existing(tech_name):
                    category = _classify_tech_category(tech_name)
                    project.user_selected_technologies.append(
                        UserSelectedTechnology(
                            name=tech_name,
                            purpose="extracted from project text",
                            category=category,
                            status=status,
                        )
                    )
                    existing_names.add(name_lower)

    # Also scan all answer text for technology mentions
    for item in answer_list:
        answer = item.get("answer", "")
        if answer:
            extracted = _extract_technologies_with_status(answer)
            for tech_name, status in extracted:
                name_lower = tech_name.lower()
                if name_lower not in existing_names and not _is_variant_of_existing(tech_name):
                    category = _classify_tech_category(tech_name)
                    project.user_selected_technologies.append(
                        UserSelectedTechnology(
                            name=tech_name,
                            purpose="extracted from user answer",
                            category=category,
                            status=status,
                        )
                    )
                    existing_names.add(name_lower)


# ============================================================
# Persistent pipeline functions
# ============================================================


async def start_persistent_project(
    project_id: str,
    idea: str,
) -> PipelineResult:
    """Start discovery and persist state to database."""

    # Update project with idea
    project_store.update_project(
        project_id,
        idea=idea,
        current_stage="discovery",
    )

    # Run discovery
    result = await start_project(idea)

    # Persist the project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
        )

    return result


async def continue_persistent_project(
    project_id: str,
    project_data: dict,
    answers: dict,
    conversation_history: list[dict] | None = None,
) -> PipelineResult:
    """Continue discovery and persist state to database."""

    # Run continuation
    result = await continue_project(
        project_data, answers,
        conversation_history=conversation_history,
        project_id=project_id,
    )

    # Persist updated project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
            current_stage=result.stage.value,
        )

    return result


async def improve_persistent_project(
    project_id: str,
    project_data: dict,
    answers: dict,
    quality_checks: dict,
) -> PipelineResult:
    """Improve context and persist to database."""

    from app.services.context_improvement import improve_project_context

    result = await improve_project_context(
        project_data=project_data,
        answers=answers,
        quality_checks=quality_checks,
        project_id=project_id,
    )

    # Persist updated project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
            current_stage=result.stage.value,
        )

    # If complete after improvement, persist
    if result.complete and result.project_id:
        project_store.update_project(
            project_id,
            status="complete",
            current_stage="complete",
        )

    return result
