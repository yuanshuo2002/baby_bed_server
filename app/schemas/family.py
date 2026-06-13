"""
家庭相关Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class FamilyCreate(BaseModel):
    """创建家庭请求"""
    family_name: str = Field(..., min_length=1, max_length=100, description="家庭名称")


class FamilyJoin(BaseModel):
    """加入家庭请求"""
    family_code: str = Field(..., min_length=1, max_length=20, description="家庭邀请码")
    member_role: str = Field(default="parent", description="家庭角色：parent/grandparent/nanny/other")
    relation: str | None = Field(None, max_length=20, description="与宝宝关系：mom/dad/grandma/grandpa/nanny")
    display_name: str | None = Field(None, max_length=50, description="显示名称")


class FamilyUpdate(BaseModel):
    """更新家庭信息请求"""
    family_name: str | None = Field(None, min_length=1, max_length=100, description="家庭名称")


class FamilyAdminTransfer(BaseModel):
    member_id: int


class FamilyMemberRoleUpdate(BaseModel):
    member_role: str = Field(..., pattern=r"^(parent|grandparent|nanny|other)$")


class FamilyInfo(BaseModel):
    """家庭信息响应"""
    id: int
    family_name: str | None = None
    family_code: str | None = None
    plan_type: str | None = None
    plan_expire_at: datetime | None = None
    device_quota: int | None = None
    baby_quota: int | None = None
    status: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FamilyMemberInfo(BaseModel):
    """家庭成员信息"""
    id: int
    family_id: int
    user_id: int
    member_role: str | None = None
    relation: str | None = None
    display_name: str | None = None
    phone: str | None = None
    can_view: int | None = None
    can_control: int | None = None
    can_receive_push: int | None = None
    push_priority: int | None = None
    is_emergency_contact: int | None = None
    is_active: int | None = None
    joined_at: datetime | None = None
    # 关联的用户信息
    nickname: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
