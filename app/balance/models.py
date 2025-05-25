from app.base.models import RouteBase, TimeSeriesPoint


class Balance(RouteBase):
    balances: list[TimeSeriesPoint]

