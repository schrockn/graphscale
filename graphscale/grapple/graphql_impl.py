from uuid import UUID

from graphscale import check
from graphscale.pent import create_pent, delete_pent, update_pent, PentContext, PentMutationData, PentMutationPayload


async def gen_pent_dynamic(context: PentContext, out_cls_name: str, obj_id: UUID):
    out_cls = context.cls_from_name(out_cls_name)
    return await out_cls.gen(context, obj_id)


async def gen_delete_pent_dynamic(
    context: PentContext, pent_cls_name: str, payload_cls_name: str, obj_id: UUID
) -> PentMutationPayload:
    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)
    deleted_id = await delete_pent(context, pent_cls, obj_id)
    return payload_cls(deleted_id)


async def gen_create_pent_dynamic(
    context: PentContext,
    pent_cls_name: str,
    data_cls_name: str,
    payload_cls_name: str,
    data: PentMutationData
) -> PentMutationPayload:

    # data_cls = context.cls_from_name(data_cls_name)
    # check.invariant(data, data_cls, 'data')

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    out_pent = await create_pent(context, pent_cls, data)
    return payload_cls(out_pent)


async def gen_update_pent_dynamic(
    context: PentContext,
    obj_id: UUID,
    pent_cls_name: str,
    data_cls_name: str,
    payload_cls_name: str,
    data: PentMutationData
) -> PentMutationPayload:

    # data_cls = context.cls_from_name(data_cls_name)
    # check.invariant(data, data_cls, 'data')

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    pent = await update_pent(context, pent_cls, obj_id, data)
    return payload_cls(pent)


async def gen_browse_pents_dynamic(
    context: PentContext, after: UUID, first: int, out_cls_name: str
):
    # check.param(context, PentContext, 'context')
    # check.int_param(first, 'first')
    # check.opt_uuid_param(after, 'after')
    # check.str_param(out_cls_name, 'out_cls_name')

    out_cls = context.cls_from_name(out_cls_name)

    return await out_cls.gen_all(context, after, first)
