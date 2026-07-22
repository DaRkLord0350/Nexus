from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, require_permission
from app.schemas.seo import SlugRedirectEntityType, SlugRedirectListResponse, SlugRedirectResolveResponse
from app.services.slug_redirect_service import SlugRedirectService

router = APIRouter(prefix="/seo", tags=["catalog-seo"])


def _seo_service(db: AsyncSession, current_user) -> SlugRedirectService:
    return SlugRedirectService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/redirects", response_model=SlugRedirectListResponse)
async def list_redirects(
    entity_type: SlugRedirectEntityType = Query(...),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _seo_service(db, current_user)
    items = await service.list_for_entity_type(entity_type.value, limit, offset)
    return {"items": items}


@router.get("/resolve", response_model=SlugRedirectResolveResponse)
async def resolve_redirect(
    entity_type: SlugRedirectEntityType = Query(...),
    slug: str = Query(...),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _seo_service(db, current_user)
    resolved = await service.resolve(entity_type.value, slug)
    return {"slug": resolved}
