from graphscale import check
from graphscale.pent import create_pent, delete_pent, update_pent, PentContext, PentMutationData


async def gen_pent_dynamic(context, out_cls_name, obj_id):
    check.param(context, PentContext, 'context')
    check.str_param(out_cls_name, 'out_cls_name')
    check.uuid_param(obj_id, 'obj_id')

    out_cls = context.cls_from_name(out_cls_name)
    return await out_cls.gen(context, obj_id)


async def gen_delete_pent_dynamic(context, pent_cls_name, payload_cls_name, obj_id):
    check.param(context, PentContext, 'context')
    check.str_param(pent_cls_name, 'pent_cls_name')
    check.str_param(payload_cls_name, 'payload_cls_name')
    check.uuid_param(obj_id, 'obj_id')

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)
    deleted_id = await delete_pent(context, pent_cls, obj_id)
    return payload_cls(deleted_id)


async def gen_create_pent_dynamic(context, pent_cls_name, data_cls_name, payload_cls_name, data):
    check.param(context, PentContext, 'context')
    check.str_param(pent_cls_name, 'pent_cls_name')
    check.str_param(data_cls_name, 'data_cls_name')
    check.str_param(payload_cls_name, 'payload_cls_name')
    data_cls = context.cls_from_name(data_cls_name)
    check.param(data, data_cls, 'data')

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    out_pent = await create_pent(context, pent_cls, data)
    return payload_cls(out_pent)


async def gen_update_pent_dynamic(
    context, obj_id, pent_cls_name, data_cls_name, payload_cls_name, data
):
    check.param(context, PentContext, 'context')
    check.str_param(pent_cls_name, 'pent_cls_name')
    check.str_param(data_cls_name, 'data_cls_name')
    check.str_param(payload_cls_name, 'payload_cls_name')
    data_cls = context.cls_from_name(data_cls_name)
    check.param(data, data_cls, 'data')

    pent_cls = context.cls_from_name(pent_cls_name)
    payload_cls = context.cls_from_name(payload_cls_name)

    pent = await update_pent(context, pent_cls, obj_id, data)
    return payload_cls(pent)


async def gen_browse_pents_dynamic(context, after, first, out_cls_name):
    check.param(context, PentContext, 'context')
    check.int_param(first, 'first')
    check.opt_uuid_param(after, 'after')
    check.str_param(out_cls_name, 'out_cls_name')

    out_cls = context.cls_from_name(out_cls_name)

    return await out_cls.gen_all(context, after, first)
