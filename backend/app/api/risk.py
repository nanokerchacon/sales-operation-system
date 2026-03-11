from app.api.status import LEGACY_RISK_STATUS, STATUS_ES, get_operational_status, router


RISK_STATUS_ES = {
    legacy_status: STATUS_ES[current_status]
    for current_status, legacy_status in LEGACY_RISK_STATUS.items()
}


def get_risk_status(
    delivered_quantity: float,
    invoiced_quantity: float,
    ordered_quantity: float | None = None,
) -> str:
    if ordered_quantity is None:
        ordered_quantity = delivered_quantity

    operational_status = get_operational_status(
        ordered_quantity=ordered_quantity,
        delivered_quantity=delivered_quantity,
        invoiced_quantity=invoiced_quantity,
    )
    return LEGACY_RISK_STATUS[operational_status]
