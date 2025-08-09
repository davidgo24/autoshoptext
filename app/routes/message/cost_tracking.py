from fastapi import APIRouter, Depends
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional
from app.models.scheduled_message import ScheduledMessage
from app.models.incoming_message import IncomingMessage
from app.core.database import get_session

router = APIRouter()

@router.get("/costs/summary")
async def get_cost_summary(
    date_filter: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Get SMS cost summary for outbound and inbound messages.
    date_filter: YYYY-MM-DD format to filter by specific date
    """
    
    # Base queries - calculate costs based on message counts (10 cents per message)
    outbound_query = select(
        func.count(ScheduledMessage.id).label("count")
    ).where(ScheduledMessage.status == "sent")
    
    inbound_query = select(
        func.count(IncomingMessage.id).label("count")
    )
    
    # Apply date filter if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            outbound_query = outbound_query.where(func.date(ScheduledMessage.sent_at) == filter_date)
            inbound_query = inbound_query.where(func.date(IncomingMessage.created_at) == filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Execute queries
    outbound_result = await session.execute(outbound_query)
    inbound_result = await session.execute(inbound_query)
    
    outbound_data = outbound_result.first()
    inbound_data = inbound_result.first()
    
    # Handle None values and calculate costs (10 cents per message)
    outbound_count = outbound_data.count or 0
    outbound_total_cents = outbound_count * 10  # 10 cents per sent message
    inbound_count = inbound_data.count or 0
    inbound_total_cents = inbound_count * 10  # 10 cents per received message
    
    total_messages = outbound_count + inbound_count
    total_cents = outbound_total_cents + inbound_total_cents
    total_dollars = total_cents / 100.0
    
    return {
        "success": True,
        "data": {
            "date_filter": date_filter,
            "outbound_messages": {
                "count": outbound_count,
                "total_cents": outbound_total_cents,
                "total_dollars": round(outbound_total_cents / 100.0, 2)
            },
            "inbound_messages": {
                "count": inbound_count,
                "total_cents": inbound_total_cents,
                "total_dollars": round(inbound_total_cents / 100.0, 2)
            },
            "totals": {
                "total_messages": total_messages,
                "total_cents": total_cents,
                "total_dollars": round(total_dollars, 2)
            }
        }
    }

@router.get("/costs/monthly")
async def get_monthly_costs(session: AsyncSession = Depends(get_session)):
    """Get cost breakdown by month for the current year"""
    
    current_year = datetime.now().year
    
    # Query for monthly outbound costs
    outbound_monthly = await session.execute(
        select(
            func.extract('month', ScheduledMessage.sent_at).label('month'),
            func.count(ScheduledMessage.id).label('count')
        ).where(
            ScheduledMessage.status == "sent",
            func.extract('year', ScheduledMessage.sent_at) == current_year
        ).group_by(func.extract('month', ScheduledMessage.sent_at))
    )
    
    # Query for monthly inbound costs
    inbound_monthly = await session.execute(
        select(
            func.extract('month', IncomingMessage.created_at).label('month'),
            func.count(IncomingMessage.id).label('count')
        ).where(
            func.extract('year', IncomingMessage.created_at) == current_year
        ).group_by(func.extract('month', IncomingMessage.created_at))
    )
    
    # Process results
    monthly_data = {}
    
    for row in outbound_monthly:
        month = int(row.month)
        monthly_data[month] = monthly_data.get(month, {
            "outbound_count": 0, "outbound_cents": 0,
            "inbound_count": 0, "inbound_cents": 0
        })
        count = row.count or 0
        monthly_data[month]["outbound_count"] = count
        monthly_data[month]["outbound_cents"] = count * 10  # 10 cents per message
    
    for row in inbound_monthly:
        month = int(row.month)
        monthly_data[month] = monthly_data.get(month, {
            "outbound_count": 0, "outbound_cents": 0,
            "inbound_count": 0, "inbound_cents": 0
        })
        count = row.count or 0
        monthly_data[month]["inbound_count"] = count
        monthly_data[month]["inbound_cents"] = count * 10  # 10 cents per message
    
    # Format for frontend
    months = []
    for month_num in range(1, 13):
        month_data = monthly_data.get(month_num, {
            "outbound_count": 0, "outbound_cents": 0,
            "inbound_count": 0, "inbound_cents": 0
        })
        
        total_cents = month_data["outbound_cents"] + month_data["inbound_cents"]
        total_count = month_data["outbound_count"] + month_data["inbound_count"]
        
        months.append({
            "month": month_num,
            "month_name": datetime(current_year, month_num, 1).strftime("%B"),
            "outbound": {
                "count": month_data["outbound_count"],
                "cents": month_data["outbound_cents"],
                "dollars": round(month_data["outbound_cents"] / 100.0, 2)
            },
            "inbound": {
                "count": month_data["inbound_count"],
                "cents": month_data["inbound_cents"],
                "dollars": round(month_data["inbound_cents"] / 100.0, 2)
            },
            "total": {
                "count": total_count,
                "cents": total_cents,
                "dollars": round(total_cents / 100.0, 2)
            }
        })
    
    return {
        "success": True,
        "data": {
            "year": current_year,
            "months": months
        }
    }
