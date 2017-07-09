from typing import cast, List, TypeVar, Any, Type, Optional
from uuid import UUID

from graphscale import check

from graphscale.pent import (
    create_pent,
    delete_pent,
    update_pent,
    Pent,
    PentContext,
    PentMutationData,
    PentMutationPayload,
)

T = TypeVar('T')


def typed_or_none(obj: Any, cls: Type[T]) -> Optional[T]:
    return obj if isinstance(obj, cls) else None


async def gen_pent_dynamic(context: PentContext, out_cls_name: str, obj_id: UUID) -> Pent:
    out_cls = context.cls_from_name(out_cls_name)
    pent = await out_cls.gen(context, obj_id)
    return cast(Pent, pent)


async def gen_delete_pent_dynamic(
    context: PentContext, pent_cls_name: str, payload_cls_name: str, obj_id: UUID
) -> PentMutationPayload:
    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)
    deleted_id = await delete_pent(context, pent_cls, obj_id)
    return cast(PentMutationPayload, payload_cls(deleted_id))


async def gen_create_pent_dynamic(
    context: PentContext,
    pent_cls_name: str,
    data_cls_name: str,
    payload_cls_name: str,
    data: PentMutationData
) -> PentMutationPayload:

    data_cls = context.cls_from_name(data_cls_name)
    check.isinst(data, data_cls)

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    out_pent = await create_pent(context, pent_cls, data)
    return cast(PentMutationPayload, payload_cls(out_pent))


async def gen_update_pent_dynamic(
    context: PentContext,
    obj_id: UUID,
    pent_cls_name: str,
    data_cls_name: str,
    payload_cls_name: str,
    data: PentMutationData
) -> PentMutationPayload:

    data_cls = context.cls_from_name(data_cls_name)
    check.isinst(data, data_cls)

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    pent = await update_pent(context, pent_cls, obj_id, data)
    return cast(PentMutationPayload, payload_cls(pent))


async def gen_browse_pents_dynamic(
    context: PentContext, after: UUID, first: int, out_cls_name: str
) -> List[Pent]:
    out_cls = context.cls_from_name(out_cls_name)
    pents = await out_cls.gen_browse(context, after, first)
    return cast(List[Pent], pents)
