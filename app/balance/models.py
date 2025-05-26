from app.base.models import RouteBase, TimeSeries


class Balance(RouteBase):
    balances: list[TimeSeries]

