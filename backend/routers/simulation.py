from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from core.game_engine import GameState, GameMode

router = APIRouter()

def get_game_engine():
    import main
    return main.game_engine

@router.get("/status")
async def get_simulation_status():
    """获取模拟系统状态"""
    engine = get_game_engine()
    
    return {
        "status": engine.state.value,
        "mode": engine.mode.value,
        "current_round": engine.current_round,
        "current_phase": engine.current_phase.value,
        "last_round_time": engine.last_round_time.isoformat(),
        "companies_count": len(engine.companies),
        "employees_count": len(engine.employees),
        "decisions_count": len(engine.decisions),
        "events_count": len(engine.events),
        "ai_stats": engine.ai_client.call_stats,
        "config": engine.config
    }

@router.post("/start")
async def start_simulation():
    """启动模拟"""
    engine = get_game_engine()
    
    if engine.state == GameState.RUNNING:
        return {"message": "Simulation is already running"}
    
    engine.state = GameState.RUNNING
    if engine.mode == GameMode.AUTO:
        import asyncio
        asyncio.create_task(engine.start_auto_rounds())
    
    return {
        "message": "Simulation started successfully",
        "status": engine.state.value,
        "companies": len(engine.companies),
        "current_round": engine.current_round
    }

@router.post("/pause")
async def pause_simulation():
    """暂停模拟"""
    engine = get_game_engine()
    
    if engine.state != GameState.RUNNING:
        raise HTTPException(status_code=400, detail="Simulation is not running")
    
    engine.pause()
    
    return {
        "message": "Simulation paused",
        "status": engine.state.value
    }

@router.post("/resume")
async def resume_simulation():
    """恢复模拟"""
    engine = get_game_engine()
    
    if engine.state != GameState.PAUSED:
        raise HTTPException(status_code=400, detail="Simulation is not paused")
    
    engine.resume()
    
    return {
        "message": "Simulation resumed",
        "status": engine.state.value
    }

@router.post("/stop")
async def stop_simulation():
    """停止模拟"""
    engine = get_game_engine()
    
    engine.stop()
    
    return {
        "message": "Simulation stopped",
        "status": engine.state.value
    }

@router.post("/round")
async def manual_round():
    """手动执行一轮模拟"""
    engine = get_game_engine()
    
    if engine.state != GameState.RUNNING and engine.state != GameState.PAUSED:
        raise HTTPException(status_code=400, detail="Simulation is not running")
    
    events = await engine.execute_round()
    
    return {
        "message": "Round executed successfully",
        "events_count": len(events),
        "current_round": engine.current_round
    }

@router.post("/reset")
async def reset_simulation():
    """重置模拟"""
    engine = get_game_engine()
    
    await engine.reset_game()
    
    return {
        "message": "Simulation reset successfully",
        "status": engine.state.value
    }

@router.get("/events")
async def get_simulation_events(limit: int = 50):
    """获取模拟事件"""
    engine = get_game_engine()
    
    events = engine.get_recent_events(limit)
    return {
        "events": [event.to_dict() for event in events]
    }

@router.get("/decisions")
async def get_recent_decisions(
    company_id: str = None,
    limit: int = 50
):
    """获取最近的决策"""
    engine = get_game_engine()
    
    decisions = engine.get_recent_decisions(limit)
    
    # 过滤公司ID
    if company_id:
        decisions = [d for d in decisions if d.company_id == company_id]
    
    # 获取公司和员工信息用于丰富决策数据
    companies = {c.id: c for c in engine.get_companies()}
    employees = {e.id: e for e in engine.get_employees()}
    
    return {
        "decisions": [
            {
                "id": d.id,
                "company_id": d.company_id,
                "company_name": companies.get(d.company_id, {}).name if companies.get(d.company_id) and companies.get(d.company_id).name else "Unknown Company",
                "employee_id": d.employee_id,
                "employee_name": employees.get(d.employee_id, {}).name if employees.get(d.employee_id) else "Unknown Employee",
                "employee_role": employees.get(d.employee_id, {}).role.value if employees.get(d.employee_id) else "Unknown Role",
                "employee_level": employees.get(d.employee_id, {}).level if employees.get(d.employee_id) else None,
                "employee_experience": employees.get(d.employee_id, {}).experience if employees.get(d.employee_id) else None,
                "employee_ai_personality": employees.get(d.employee_id, {}).ai_personality if employees.get(d.employee_id) else None,
                "employee_decision_style": employees.get(d.employee_id, {}).decision_style if employees.get(d.employee_id) else None,
                "decision_type": d.decision_type.value,
                "content": d.content,
                "created_at": d.created_at.isoformat(),
                "ai_provider": d.ai_provider,
                "ai_model": d.ai_model,
                "cost": d.cost,
                # 添加缺失的关键字段
                "status": d.status.value,
                "importance": d.importance,
                "urgency": d.urgency,
                "impact_score": d.impact_score,
                # 投票相关字段
                "votes_for": d.votes_for,
                "votes_against": d.votes_against,
                "abstentions": d.abstentions,
                "vote_result": d.get_vote_result(),
                "approval_rate": d.get_approval_rate(),
                "voters": d.voters if d.voters else [],
                "vote_details": d.vote_details if hasattr(d, 'vote_details') and d.vote_details else {},
                # 时间相关字段
                "started_at": d.started_at.isoformat() if d.started_at else None,
                "completed_at": d.completed_at.isoformat() if d.completed_at else None,
                "outcome": d.outcome
            }
            for d in decisions
        ],
        "total_decisions": len(decisions)
    }

@router.post("/mode")
async def set_simulation_mode(mode: str):
    """设置模拟模式"""
    engine = get_game_engine()
    
    if mode not in ["auto", "manual"]:
        raise HTTPException(status_code=400, detail="Mode must be 'auto' or 'manual'")
    
    await engine.set_mode(GameMode(mode))
    
    return {
        "message": f"Simulation mode set to {mode}",
        "mode": engine.mode.value
    }

@router.get("/stats")
async def get_simulation_stats():
    """获取模拟统计信息"""
    engine = get_game_engine()
    return engine.get_game_stats()

@router.get("/companies")
async def get_simulation_companies():
    """获取所有公司信息"""
    engine = get_game_engine()
    companies = engine.get_companies()
    
    return {
        "companies": [{
            "id": c.id,
            "name": c.name,
            "company_type": c.company_type.value,
            "funds": c.funds,
            "size": c.size,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in companies]
    }

@router.get("/employees")
async def get_simulation_employees(company_id: str = None):
    """获取员工信息"""
    engine = get_game_engine()
    employees = engine.get_employees(company_id)
    
    return {
        "employees": [{
            "id": e.id,
            "company_id": e.company_id,
            "name": e.name,
            "role": e.role.value,
            "level": e.level,
            "experience": e.experience,
            "ai_personality": getattr(e, 'ai_personality', None),
            "decision_style": getattr(e, 'decision_style', None)
        } for e in employees]
    }

@router.put("/config")
async def update_simulation_config(
    step_interval: int = None,
    base_funding_rate: int = None,
    max_companies: int = None,
    decision_timeout: int = None
):
    """更新模拟配置"""
    engine = get_game_engine()
    
    config_updated = {}
    
    if step_interval is not None:
        if step_interval < 10 or step_interval > 300:
            raise HTTPException(
                status_code=400, 
                detail="Step interval must be between 10 and 300 seconds"
            )
        engine.config["round_interval"] = step_interval
        config_updated["round_interval"] = step_interval
    
    if base_funding_rate is not None:
        if base_funding_rate < 100 or base_funding_rate > 10000:
            raise HTTPException(
                status_code=400,
                detail="Base funding rate must be between 100 and 10000"
            )
        engine.config["base_funding_rate"] = base_funding_rate
        config_updated["base_funding_rate"] = base_funding_rate
    
    if max_companies is not None:
        if max_companies < 2 or max_companies > 20:
            raise HTTPException(
                status_code=400,
                detail="Max companies must be between 2 and 20"
            )
        engine.config["max_companies"] = max_companies
        config_updated["max_companies"] = max_companies
    
    if decision_timeout is not None:
        if decision_timeout < 30 or decision_timeout > 300:
            raise HTTPException(
                status_code=400,
                detail="Decision timeout must be between 30 and 300 seconds"
            )
        engine.config["decision_timeout"] = decision_timeout
        config_updated["decision_timeout"] = decision_timeout
    
    return {
        "message": "Configuration updated successfully",
        "updated_config": config_updated,
        "current_config": engine.config
    }

@router.get("/leaderboard")
async def get_company_leaderboard():
    """获取公司排行榜"""
    engine = get_game_engine()
    
    companies = engine.get_companies()
    
    leaderboard = []
    for company in companies:
        employees = [e for e in engine.get_employees() if e.company_id == company.id]
        decisions = [d for d in engine.get_recent_decisions(10) if d.company_id == company.id]
        
        # 计算综合评分
        funds_score = company.funds / 10000  # 资金评分
        size_score = len(employees) * 10  # 规模评分
        activity_score = len(decisions) * 5  # 活跃度评分
        
        # 员工质量评分
        if employees:
            # Use experience as performance metric
            avg_performance = sum(e.experience for e in employees) / len(employees)
            avg_level = sum(e.level for e in employees) / len(employees)
            quality_score = (avg_performance * avg_level) * 20
        else:
            quality_score = 0
        
        total_score = funds_score + size_score + activity_score + quality_score
        
        leaderboard.append({
            "company_id": company.id,
            "company_name": company.name,
            "company_type": company.company_type.value,
            "total_score": round(total_score, 2),
            "breakdown": {
                "funds_score": round(funds_score, 2),
                "size_score": round(size_score, 2),
                "activity_score": round(activity_score, 2),
                "quality_score": round(quality_score, 2)
            },
            "stats": {
                "funds": company.funds,
                "employees": len(employees),
                "decisions": len(decisions),
                "avg_performance": round(sum(e.experience for e in employees) / len(employees), 2) if employees else 0
            }
        })
    
    # 按总分排序
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    
    # 添加排名
    for i, company in enumerate(leaderboard):
        company["rank"] = i + 1
    
    return {
        "leaderboard": leaderboard,
        "total_companies": len(leaderboard),
        "updated_at": datetime.now().isoformat()
    }

@router.post("/trigger-event")
async def trigger_custom_event(
    event_type: str,
    description: str,
    company_id: str = None,
    data: Dict[str, Any] = None
):
    """触发自定义事件（用于测试）"""
    engine = get_game_engine()
    
    if company_id and company_id not in engine.companies:
        raise HTTPException(status_code=404, detail="Company not found")
    
    from core.game_engine import GameEvent
    
    event = GameEvent(
        id=f"custom_{datetime.now().timestamp()}",
        type=event_type,
        timestamp=datetime.now(),
        company_id=company_id,
        description=description,
        data=data or {}
    )
    
    engine.events.append(event)
    
    return {
        "message": "Custom event triggered successfully",
        "event": {
            "id": event.id,
            "type": event.type,
            "timestamp": event.timestamp.isoformat(),
            "company_id": event.company_id,
            "description": event.description,
            "data": event.data
        }
    }

@router.post("/end")
async def end_simulation():
    """结束模拟并生成统计数据"""
    engine = get_game_engine()
    
    # 停止模拟
    engine.stop()
    
    # 获取统计数据
    stats = engine.get_game_stats()
    
    # 添加更详细的统计信息
    companies = engine.get_companies()
    company_stats = {}
    
    for company in companies:
        employees = [e for e in engine.get_employees() if e.company_id == company.id]
        decisions = [d for d in engine.get_recent_decisions(1000) if d.company_id == company.id]
        events = [e for e in engine.get_recent_events(1000) if e.company_id == company.id]
        
        company_stats[company.id] = {
            "name": company.name,
            "type": company.company_type.value,
            "funds": company.funds,
            "employees_count": len(employees),
            "decisions_count": len(decisions),
            "events_count": len(events),
            "avg_employee_level": sum(e.level for e in employees) / len(employees) if employees else 0,
            "total_experience": sum(e.experience for e in employees),
            "is_active": company.is_active
        }
    
    stats["companies"] = company_stats
    
    # 返回游戏总结数据
    return {
        "total_rounds": stats["current_round"],
        "total_companies": stats["companies_count"],
        "total_employees": stats["employees_count"],
        "total_decisions": stats["decisions_count"],
        "total_events": stats["events_count"],
        "ai_cost": stats["ai_stats"]["total_cost"] if stats["ai_stats"] else 0,
        "ai_calls": stats["ai_stats"]["total_calls"] if stats["ai_stats"] else 0,
        "companies": company_stats
    }