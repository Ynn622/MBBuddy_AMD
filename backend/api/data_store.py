"""
共享資料儲存模組
存放跨模組共享的資料結構，避免循環引用
"""

# AMD 版本的資料結構 (使用 Lemonade Server 進行 AI 推理)
ROOMS = {}
"""
{
    room_id: {
        "code": str,
        "title": str,
        "created_at": float,  # timestamp
        "settings": {"allowQuestions": bool, "allowVoting": bool},
        "status": str,  # NotFound, Stop, Discussion, End
        "participants": [{"device_id": str, "nickname": str, "last_seen": float}],  # timestamp
        "current_topic": str,
        "countdown": int,
        "time_start": float,  # timestamp
        "topic_summary": str,  # 題目摘要
        "desired_outcome": str,  # 預期成果
        "topic_count": int,  # 主題數量
        "room_context": str  # 房間上下文,用於 AMD Lemonade Server 的 AI 推理
    }
}
"""

topics = {}
"""
{
    topic_id: {
        "room_id": str,
        "topic_name": str,
        "comments": [{"id": str, "nickname": str, "content": str, "ts": float}]
    }
}
"""

votes = {}
"""
{
    comment_id: {
        "good": [device_id1, device_id2, ...],
        "bad": [device_id1, device_id2, ...]
    }
}
"""
