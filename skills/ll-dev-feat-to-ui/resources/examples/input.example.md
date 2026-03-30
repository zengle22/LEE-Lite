```json
{
  "artifact_type": "feat_freeze_package",
  "workflow_key": "product.epic-to-feat",
  "status": "accepted",
  "feat_refs": ["FEAT-023"],
  "features": [
    {
      "feat_ref": "FEAT-023",
      "title": "新用户建档",
      "goal": "让新用户完成基础建档并进入后续个性化配置流程。",
      "scope": ["基本信息录入", "目标设置", "完成确认"],
      "constraints": ["必须保留草稿恢复", "必须支持提交失败重试"],
      "acceptance_checks": [{"scenario": "用户完成基本资料录入", "then": "用户可进入下一步"}],
      "source_refs": ["FEAT-023", "EPIC-010", "SRC-002"],
      "ui_units": [
        {
          "slug": "profile-entry",
          "page_name": "基本信息录入",
          "page_type": "multi-step form",
          "input_fields": [
            {"field": "name", "type": "string", "required": true},
            {"field": "age", "type": "integer", "required": true}
          ],
          "api_touchpoints": ["GET /profile/draft", "POST /profile/basic-info"]
        }
      ]
    }
  ]
}
```
