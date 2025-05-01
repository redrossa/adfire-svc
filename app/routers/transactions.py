from fastapi import APIRouter

routers = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)


@routers.get('/')
async def get_transactions():
    """Returns all transactions belonging to user"""
    return [
        {
            'id': 'cma5t859d00000cjod6i2abqi',
            'name': 'Kroger Groceries',
            'date': '2024-04-28',
            'amount': -100,
            'symbol': 'USD',
        },
        {
            'id': 'cma5t9rnq00000cl599qh8tot',
            'name': "Wendy's Wages",
            'date': '2024-04-15',
            'amount': 2200,
            'symbol': 'USD',
        },
    ]


@routers.get('/{id}')
async def get_transaction(id: str):
    """Returns a transaction by id belonging to user"""
    return {
        'id': 'cma5t859d00000cjod6i2abqi',
        'name': 'Kroger Groceries',
        'date': '2024-04-28',
        'amount': -100,
        'symbol': 'USD',
        'from': [
            {
                'id': 'cma5t9zmu00010cl5hjpfh8up',
                'account': 'Amex Gold',
                'mask': '0001',
                'amount': 100,
                'symbol': 'USD',
                'date': '2024-04-28',
            },
        ],
        'to': [
            {
                'id': 'cma5tab5a00030cl51hophzf3',
                'account': 'Kroger',
                'amount': 100,
                'symbol': 'USD',
                'date': '2024-04-30',
            },
        ],
    }
