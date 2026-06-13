"""
LLM服务 - 调用大模型API生成成长报告
"""
import json
import httpx
from typing import Literal

from config import settings


class LLMService:
    """大模型服务"""

    def __init__(self):
        self.api_url = settings.LLM_API_URL or "http://223.247.96.246:30025/v1/chat/completions"
        self.api_key = settings.LLM_API_KEY if hasattr(settings, 'LLM_API_KEY') and settings.LLM_API_KEY else ""

    async def generate_growth_report(
        self,
        report_type: Literal["daily", "weekly", "monthly"],
        period_start: str,
        period_end: str,
        event_stats: dict,
    ) -> dict:
        """
        调用大模型生成成长报告

        Args:
            report_type: 报告类型 (daily/weekly/monthly)
            period_start: 周期开始日期
            period_end: 周期结束日期
            event_stats: 五大事件统计数据
                {
                    "sleep": {"duration_hours": float, "count": int, "avg_quality": float},
                    "cry": {"count": int, "total_duration_min": int, "avg_level": float},
                    "danger": {"count": int, "types": dict},
                    "playing": {"count": int, "duration_hours": float},
                    "milestone": {"count": int, "items": list},
                }

        Returns:
            {
                "title": str,
                "summary": str,
                "highlights": list[str],
                "recommendations": list[str],
                "sleep_analysis": str,
                "health_notes": str,
            }
        """
        prompt = self._build_prompt(report_type, period_start, period_end, event_stats)

        payload = {
            "model": "qwen2.5-instruct",
            "messages": [
                {"role": "system", "content": "你是一个专业的婴儿成长分析师，擅长分析婴儿的行为数据并给出科学的育儿建议。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Content-Type": "application/json"}
            if self.api_key and self.api_key != "empty":
                headers["Authorization"] = f"Bearer {self.api_key}"
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return self._parse_response(content)

    def _build_prompt(
        self,
        report_type: str,
        period_start: str,
        period_end: str,
        event_stats: dict,
    ) -> str:
        period_label = {"daily": "日报", "weekly": "周报", "monthly": "月报"}.get(report_type, "报告")
        type_label = {"daily": "今天", "weekly": "本周", "monthly": "本月"}.get(report_type, "本期")

        sleep = event_stats.get("sleep", {})
        cry = event_stats.get("cry", {})
        danger = event_stats.get("danger", {})
        playing = event_stats.get("playing", {})
        milestone = event_stats.get("milestone", {})

        prompt = f"""请为宝宝生成一份{period_label}，时间范围：{period_start} 至 {period_end}。

## 数据统计

### 睡眠情况
- 总睡眠时长：{sleep.get('duration_hours', 0):.1f} 小时
- 睡眠次数：{sleep.get('count', 0)} 次
- 平均睡眠质量评分：{sleep.get('avg_quality', 0):.1f}/10

### 哭闹情况
- 哭闹次数：{cry.get('count', 0)} 次
- 总哭闹时长：{cry.get('total_duration_min', 0)} 分钟
- 平均哭闹等级：{cry.get('avg_level', 0):.1f}/5

### 危险事件
- 危险事件次数：{danger.get('count', 0)} 次
- 危险类型分布：{json.dumps(danger.get('types', {}), ensure_ascii=False)}

### 玩耍情况
- 玩耍次数：{playing.get('count', 0)} 次
- 总玩耍时长：{playing.get('duration_hours', 0):.1f} 小时

### 里程碑事件
- 里程碑数量：{milestone.get('count', 0)} 个
- 里程碑详情：{json.dumps(milestone.get('items', [])[:5], ensure_ascii=False)}

## 输出要求

请以JSON格式输出成长报告，包含以下字段：
{{
    "title": "{period_label}标题，例如：{type_label}成长报告 - 睡眠质量良好",
    "summary": "总体总结，2-3句话概括{type_label}整体情况",
    "highlights": ["亮点1", "亮点2", "亮点3"],
    "recommendations": ["建议1", "建议2", "建议3"],
    "sleep_analysis": "睡眠分析，1-2句话",
    "health_notes": "健康提示，1-2句话"
}}

请直接输出JSON，不要添加其他说明。"""

        return prompt

    def _parse_response(self, content: str) -> dict:
        """解析LLM响应，提取JSON"""
        try:
            # 尝试提取JSON块
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
                if line.startswith('```json'):
                    continue
                if line.startswith('```'):
                    continue

            # 尝试从整个内容中提取JSON
            content = content.strip()
            if content.startswith('{'):
                end_idx = content.index('}') + 1
                return json.loads(content[:end_idx])

            # 如果解析失败，返回默认结构
            return {
                "title": "成长报告",
                "summary": content[:200] if content else "数据汇总中",
                "highlights": ["数据收集中"],
                "recommendations": ["请耐心等待下一期报告"],
                "sleep_analysis": "暂无",
                "health_notes": "暂无",
            }
        except json.JSONDecodeError:
            return {
                "title": "成长报告",
                "summary": content[:200] if content else "数据汇总中",
                "highlights": ["数据收集中"],
                "recommendations": ["请耐心等待下一期报告"],
                "sleep_analysis": "暂无",
                "health_notes": "暂无",
            }


llm_service = LLMService()