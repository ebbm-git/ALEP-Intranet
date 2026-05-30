"""Seed the navigation tree and a placeholder block per leaf page.

Run from the backend folder with the venv active:
    python scripts/seed_navigation.py

Re-runs are idempotent: existing pages (matched by parent_id + slug) are kept
and only filled with a starter block if they have none.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `app.*` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import ContentBlock, Page, RolePagePermission, UserRole  # noqa: E402


NAVIGATION = [
    {
        "slug": "conhecimento-alep",
        "title": "Conhecimento ALEP",
        "children": [
            ("historia-e-percurso", "História e Percurso"),
            ("missao-visao-valores", "Missão, Visão e Valores"),
            ("estrutura-organizacional", "Estrutura Organizacional"),
            ("servicos-aos-associados", "Serviços Prestados aos Associados"),
            ("conquistas-e-atividades", "Conquistas e Atividades Desenvolvidas"),
            ("entidades-publicas-e-privadas", "Relação com Entidades Públicas e Privadas"),
            ("canais-de-comunicacao", "Canais de Comunicação com Associados"),
        ],
    },
    {
        "slug": "plano-de-atividades-2026",
        "title": "Plano de Atividades 2026",
        "children": [
            ("pontos-estrategicos-2025-2027", "Pontos Estratégicos 2025–2027"),
            ("iniciativas-e-eventos-2026", "Iniciativas e Eventos 2026"),
            ("kpis-2026", "Indicadores de Desempenho (KPIs) 2026"),
        ],
    },
    {
        "slug": "operacao-interna",
        "title": "Operação Interna",
        "children": [
            ("gestao-de-quotas", "Gestão de Quotas"),
            ("renovacao-de-quotas", "Renovação de Quotas"),
            ("seguros", "Seguros"),
            ("admissao-de-novos-associados", "Admissão de Novos Associados"),
            ("helpdesk-freshdesk", "Helpdesk – Freshdesk"),
            ("atendimento-telefonico", "Atendimento Telefónico"),
        ],
    },
]


def placeholder_body(title: str) -> str:
    return (
        f"# {title}\n\n"
        "_Conteúdo inicial — edite ou substitua usando o botão **Editar**._\n\n"
        "Conteúdo extraído do **Manual de Onboarding ALEP 2026 (v1.0)**.\n"
        "Para inserir secções acima ou abaixo, use os botões `+ Inserir secção`.\n"
    )


def upsert_page(session, *, parent_id, slug: str, title: str, position: int) -> Page:
    existing = session.scalar(
        select(Page).where(Page.parent_id.is_(parent_id), Page.slug == slug)
        if parent_id is None
        else select(Page).where(Page.parent_id == parent_id, Page.slug == slug)
    )
    if existing:
        existing.title = title
        existing.position = position
        return existing
    page = Page(parent_id=parent_id, slug=slug, title=title, position=position)
    session.add(page)
    session.flush()
    return page


def ensure_starter_block(session, page: Page) -> None:
    has_block = session.scalar(
        select(ContentBlock.id).where(ContentBlock.page_id == page.id).limit(1)
    )
    if has_block:
        return
    session.add(
        ContentBlock(
            page_id=page.id,
            position=0,
            block_type="markdown",
            body=placeholder_body(page.title),
        )
    )


def ensure_default_permissions(session) -> int:
    """Grant every non-admin role access to every page, if not already set.
    Admins are NOT stored here (they have implicit access)."""
    n_added = 0
    non_admin_roles = [r for r in UserRole if r is not UserRole.admin]
    all_page_ids = list(session.scalars(select(Page.id)))
    existing = {
        (perm.role, perm.page_id)
        for perm in session.scalars(select(RolePagePermission))
    }
    for role in non_admin_roles:
        for pid in all_page_ids:
            if (role, pid) not in existing:
                session.add(RolePagePermission(role=role, page_id=pid))
                n_added += 1
    return n_added


def main() -> None:
    with SessionLocal() as session:
        for top_pos, top in enumerate(NAVIGATION):
            top_page = upsert_page(
                session,
                parent_id=None,
                slug=top["slug"],
                title=top["title"],
                position=top_pos,
            )
            for child_pos, (slug, title) in enumerate(top["children"]):
                child = upsert_page(
                    session,
                    parent_id=top_page.id,
                    slug=slug,
                    title=title,
                    position=child_pos,
                )
                ensure_starter_block(session, child)
        n_perms = ensure_default_permissions(session)
        session.commit()
        if n_perms:
            print(f"  Granted {n_perms} default role-page permissions.")

    print("Seed complete.")
    with SessionLocal() as session:
        total_pages = session.scalar(select(Page.id).limit(1))  # noqa: F841
        from sqlalchemy import func

        n_pages = session.scalar(select(func.count(Page.id)))
        n_blocks = session.scalar(select(func.count(ContentBlock.id)))
        print(f"  pages: {n_pages}  content_blocks: {n_blocks}")


if __name__ == "__main__":
    main()
