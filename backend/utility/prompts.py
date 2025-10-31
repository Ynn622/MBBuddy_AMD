"""
AI Prompt 構建模組
負責構建各種 AI 任務的 prompt，包括主題生成、總結等
"""

import json
import re
from typing import List, Dict, Any, Optional
from api.data_store import ROOMS, topics, votes

class PromptBuilder:
    """AI Prompt 構建器"""
    
    @staticmethod
    def build_summary_prompt(room: str, topic: str) -> str:
        """
        構建討論總結的 prompt
        
        Args:
            room: 討論室代碼
            topic: 要總結的主題名稱
        
        Returns:
            構建好的 prompt 字串
        """
        # 檢查討論室是否存在
        if room not in ROOMS:
            return "錯誤：找不到指定的討論室。"

        # 組合主題 ID 並檢查主題是否存在
        topic_id = f"{room}_{topic}"
        if topic_id not in topics:
            return "錯誤：在該討論室中找不到指定的主題。"

        room_data = ROOMS[room]
        topic_data = topics[topic_id]
        
        # 開始建立 Prompt
        prompt = f"主題: {topic}\n"

        # 取得參與者列表
        participants = [p.get("nickname", "匿名") for p in room_data.get("participants_list", [])]
        if participants:
            prompt += f"參與者: {', '.join(participants)}\n"

        prompt += "\n留言與票數:\n"

        # 取得該主題的所有留言與其對應的票數
        comments_for_prompt = []
        if "comments" in topic_data:
            for c in topic_data["comments"]:
                comment_id = c.get("id")
                nickname = c.get("nickname", "匿名")
                content = c.get("content", "")
                
                # 從 votes 字典中取得票數
                good_votes = len(votes.get(comment_id, {}).get("good", []))
                bad_votes = len(votes.get(comment_id, {}).get("bad", []))

                comments_for_prompt.append(
                    f"- {nickname}：{content}（👍{good_votes}、👎{bad_votes}）"
                )

        if not comments_for_prompt:
            prompt += "目前這個主題還沒有任何留言。\n"
        else:
            prompt += "\n".join(comments_for_prompt)

        # 加上固定的指令模板
        prompt += """

                    你的任務是擔任一個專業的討論記錄員。
                    你必須嚴格根據上方提供的「留言與票數」資訊，進行條列式彙整。
                    禁止臆測或生成任何未在資料中出現的數字、名稱或觀點。
                    你的回答內容，只能包含彙整後的結果，禁止加入任何開場白、問候語或結尾的免責聲明。

                    請直接以以下格式輸出，並將真實的內容填入：
                    ---
                    1. [第一個重點主題]
                    - 主流意見：
                    - 分歧點：（若無則寫"無"）
                    - 可能決議：
                    ---
                    2. [第二個重點主題]
                    - 主流意見：
                    - 分歧點：（若無則寫"無"）
                    - 可能決議：
                    ---
                    總結：
                    [此處條列討論的最重要共識或後續追蹤事項]
                """

        return prompt
    
    @staticmethod
    def build_topics_generation_prompt(meeting_title: str, topic_count: int) -> str:
        """
        構建主題生成的 prompt
        
        Args:
            meeting_title: 討論標題
            topic_count: 要生成的主題數量
        
        Returns:
            構建好的 prompt 字串
        """
        topic_count = max(1, min(10, topic_count))
        meeting_title = meeting_title.strip()

        if not meeting_title:
            return "錯誤：討論名稱不可為空。"

        prompt = f"""請為「{meeting_title}」討論設計 {topic_count} 個討論主題。

要求：
- 主題與「{meeting_title}」直接相關  
- 用繁體中文
- 具體可執行
- 直接以JSON陣列格式回答

回答格式：["主題一", "主題二", "主題三"]

請立即生成 {topic_count} 個主題："""

        return prompt
    
    @staticmethod
    def build_single_topic_generation_prompt(room: str, custom_prompt: str) -> str:
        """
        構建單個主題生成的 prompt
        
        Args:
            room: 討論室代碼
            custom_prompt: 自訂提示語句
        
        Returns:
            構建好的 prompt 字串
        """
        # 檢查討論室是否存在
        if room not in ROOMS:
            return "錯誤：找不到指定的討論室。"

        room_data = ROOMS[room]

        # 開始建立 Prompt
        prompt = f"討論名稱: {room_data.get('title', '未命名討論')}\n"
        prompt += f"討論代碼: {room}\n"
        
        # 添加討論描述/摘要（如果有）
        if room_data.get('topic_summary'):
            prompt += f"討論摘要: {room_data['topic_summary']}\n"
        if room_data.get('desired_outcome'):
            prompt += f"預期成果: {room_data['desired_outcome']}\n"
        
        # 取得參與者列表
        participants = [p.get("nickname", "匿名") for p in room_data.get("participants_list", [])]
        if participants:
            prompt += f"參與者: {', '.join(participants)}\n"
        
        # 找出該討論室的所有已有主題
        existing_topics = [
            t["topic_name"] for t_id, t in topics.items() 
            if t["room_id"] == room and "topic_name" in t
        ]
        
        if existing_topics:
            prompt += "\n已有的主題:\n"
            for i, topic_name in enumerate(existing_topics, 1):
                prompt += f"{i}. {topic_name}\n"
            
            prompt += "\n請生成一個與已有主題互補但不重複的新議程主題。主題應該既要與討論整體目標相關，又能夠覆蓋尚未討論的重要方面。"
        else:
            prompt += "\n目前討論尚未有任何主題。請生成一個適合作為第一個討論主題的議程。"

        # 加上使用者自訂的提示
        if custom_prompt:
            prompt += f"\n\n自訂提示: {custom_prompt}"
        
        prompt += "\n\n請直接返回一個簡潔、具體且不超過10個字的主題，不需要任何前綴或解釋。"

        return prompt

class TopicParser:
    """主題解析器，處理AI回覆的解析"""
    
    @staticmethod
    def flatten_and_clean_topics(items):
        """遞迴函式，用於攤平所有可能的巢狀結構"""
        if not isinstance(items, list):
            return []
        
        flat_list = []
        for item in items:
            # 如果項目是列表，遞迴攤平
            if isinstance(item, list):
                flat_list.extend(TopicParser.flatten_and_clean_topics(item))
            # 如果項目是字串
            elif isinstance(item, str):
                # 去除頭尾空白
                item = item.strip()
                # 嘗試將其視為 JSON 進行解析
                if item.startswith('[') and item.endswith(']'):
                    try:
                        nested_list = json.loads(item)
                        flat_list.extend(TopicParser.flatten_and_clean_topics(nested_list))
                    except json.JSONDecodeError:
                        # 解析失敗，當作普通字串，但過濾空值
                        if item:
                            flat_list.append(item)
                # 如果是普通字串，過濾空值
                elif item:
                    flat_list.append(item)
        return flat_list
    
    @staticmethod
    def parse_topics_from_response(raw_text: str, topic_count: int) -> List[str]:
        """
        從AI回覆中解析主題列表，增強過濾邏輯
        
        Args:
            raw_text: AI的原始回覆
            topic_count: 期望的主題數量
        
        Returns:
            解析出的主題列表
        """
        import re
        import json
        
        # 預先清理：移除常見的無效內容
        cleaned_text = raw_text
        
        # 移除聊天模板標記
        cleaned_text = re.sub(r'<\|[^|]*\|>', '', cleaned_text)
        
        # 移除 Markdown 代碼塊
        cleaned_text = re.sub(r'```(json)?\s*', '', cleaned_text)
        cleaned_text = cleaned_text.strip('`').strip()
        
        # 收集所有找到的主題（用於去重）
        all_topics = []
        
        try:
            # 策略 1: 找出所有 JSON 陣列
            # 使用正則表達式找到所有完整的 JSON 陣列
            json_pattern = r'\[(?:[^\[\]]*(?:"[^"]*"[^\[\]]*)*)*\]'
            json_matches = re.findall(json_pattern, cleaned_text)
            
            for json_str in json_matches:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list):
                        # 遞迴攤平
                        flat_topics = TopicParser.flatten_and_clean_topics(parsed)
                        all_topics.extend(flat_topics)
                except json.JSONDecodeError:
                    continue
            
        except Exception as e:
            pass
        
        # 策略 2: 如果 JSON 解析失敗或結果不足，使用行解析
        if len(all_topics) < topic_count:
            lines = cleaned_text.split('\n')
            for line in lines:
                # 清理行內容
                line = line.strip()
                # 移除列表標記
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+[\.)]\s*', '', line)
                # 移除引號
                line = line.strip(' "\'"')
                
                # 過濾有效主題
                if (line and 
                    len(line) >= 4 and
                    not line.startswith('[') and 
                    not line.endswith(']') and
                    not line.startswith('{') and
                    '以下是' not in line and
                    '符合條件' not in line):
                    all_topics.append(line)
        
        # 最終清理和去重
        seen = set()
        final_topics = []
        
        # 定義無效關鍵詞
        invalid_keywords = [
            'json', '範例', '例如', '格式', 'example',
            '請回答', '以下是', '符合條件', '主題：',
            '主題一', '主題二', '主題三', 
            '主題1', '主題2', '主題3',
            '主題 1', '主題 2', '主題 3',
            '討論主題', '議程主題'
        ]
        
        for topic in all_topics:
            if not isinstance(topic, str):
                continue
                
            # 深度清理
            topic = topic.strip(' "\'"[]{}、，。')
            
            # 移除冒號後的內容（如 "主題："）
            if '：' in topic or ':' in topic:
                parts = re.split('[：:]', topic)
                if len(parts) > 1:
                    topic = parts[-1].strip()
            
            # 檢查主題質量
            if len(topic) < 4 or len(topic) > 50:
                continue
            
            # 檢查是否包含無效關鍵詞
            topic_lower = topic.lower()
            if any(keyword.lower() in topic_lower for keyword in invalid_keywords):
                continue
            
            # 檢查是否純數字或特殊字符
            if topic.isdigit() or not any(c.isalnum() for c in topic):
                continue
            
            # 去重（使用標準化後的主題進行比較）
            normalized = topic.strip().replace(' ', '').replace('　', '')
            if normalized not in seen and len(normalized) >= 4:
                seen.add(normalized)
                final_topics.append(topic)
                
                # 達到所需數量就停止
                if len(final_topics) >= topic_count:
                    break
        
        # 如果還是不夠，返回錯誤提示
        if len(final_topics) == 0:
            return [f"無法從 AI 回應中解析出有效主題，原始回應：{raw_text[:100]}..."]
        
        return final_topics[:topic_count]

# 全局實例
prompt_builder = PromptBuilder()
topic_parser = TopicParser()
