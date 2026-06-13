"""
家庭管理路由
包含家庭创建、加入、成员列表、家庭信息等接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.family import FamilyAdminTransfer, FamilyCreate, FamilyJoin, FamilyMemberRoleUpdate, FamilyUpdate
from app.services.family_service import family_service

router = APIRouter(prefix="/family", tags=["家庭管理"])


@router.post("/create", response_model=ApiResponse, summary="创建家庭")
async def create_family(
    body: FamilyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """创建一个新家庭"""
    result = await family_service.create_family(db, user_id=current_user.id, family_name=body.family_name)
    return success(data=result, message="创建成功")


@router.post("/join", response_model=ApiResponse, summary="加入家庭")
async def join_family(
    body: FamilyJoin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """通过邀请码加入家庭"""
    result = await family_service.join_family(
        db, user_id=current_user.id, family_code=body.family_code,
        member_role=body.member_role, relation=body.relation, display_name=body.display_name,
    )
    return success(data=result, message="加入成功")


@router.get("/info", response_model=ApiResponse, summary="获取家庭信息")
async def get_family_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前用户所在家庭的信息"""
    result = await family_service.get_user_family(db, user_id=current_user.id)
    return success(data=result)


@router.put("/info", response_model=ApiResponse, summary="更新家庭信息")
async def update_family_info(
    body: FamilyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新家庭信息"""
    result = await family_service.update_family_info(db, user_id=current_user.id, family_name=body.family_name)
    return success(data=result, message="更新成功")


@router.get("/members", response_model=ApiResponse, summary="获取成员列表")
async def get_family_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭的所有成员列表"""
    result = await family_service.get_family_members(db, user_id=current_user.id)
    return success(data=result)


@router.get("/invite-code", response_model=ApiResponse, summary="获取邀请码")
async def get_invite_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭的邀请码"""
    result = await family_service.get_invite_code(db, user_id=current_user.id)
    return success(data=result)


@router.post("/leave", response_model=ApiResponse, summary="退出家庭")
async def leave_family(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """退出当前家庭"""
    await family_service.leave_family(db, user_id=current_user.id)
    return success(message="退出成功")


@router.post("/invite-code/regenerate", response_model=ApiResponse, summary="重新生成邀请码")
async def regenerate_invite_code(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return success(data=await family_service.regenerate_invite_code(db, current_user.id), message="邀请码已更新")


@router.post("/admin/transfer", response_model=ApiResponse, summary="转让管理员")
async def transfer_admin(body: FamilyAdminTransfer, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await family_service.transfer_admin(db, current_user.id, body.member_id)
    return success(message="管理员已转让")


@router.post("/dissolve", response_model=ApiResponse, summary="解散家庭")
async def dissolve_family(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await family_service.dissolve_family(db, current_user.id)
    return success(message="家庭已解散")


@router.put("/members/{member_id}/role", response_model=ApiResponse, summary="修改成员角色")
async def update_member_role(member_id: int, body: FamilyMemberRoleUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await family_service.update_member_role(db, current_user.id, member_id, body.member_role)
    return success(message="成员角色已更新")


@router.delete("/members/{member_id}", response_model=ApiResponse, summary="移除成员")
async def remove_member(member_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await family_service.remove_member(db, current_user.id, member_id)
    return success(message="成员已移除")
