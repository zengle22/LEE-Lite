window.__LEE_PROTO_DATA__ = {
  "feat_ref": "PROTO-RUNNER-OPERATOR-MAIN",
  "feat_title": "Runner Operator Main",
  "related_feat_refs": [
    "FEAT-SRC-003-002",
    "FEAT-SRC-003-003",
    "FEAT-SRC-003-007"
  ],
  "source_refs": [
    "FEAT-SRC-003-002",
    "EPIC-SRC-003-001",
    "SRC-003",
    "product.raw-to-src::adr018-raw2src-restart-20260326-r1",
    "ADR-018",
    "ADR-001",
    "ADR-003",
    "ADR-005",
    "ADR-006",
    "ADR-009",
    "FEAT-SRC-003-003",
    "FEAT-SRC-003-007"
  ],
  "surface_map_refs": [
    "SURFACE-MAP-FEAT-SRC-003-002",
    "SURFACE-MAP-FEAT-SRC-003-003",
    "SURFACE-MAP-FEAT-SRC-003-007"
  ],
  "prototype_owner_ref": "PROTO-RUNNER-OPERATOR-MAIN",
  "prototype_action": "update",
  "ui_owner_ref": "UI-RUNNER-OPERATOR-SHELL",
  "ui_action": "update",
  "journey_structural_spec_ref": "journey-ux-ascii.md",
  "ui_shell_snapshot_ref": "ui-shell-spec.md",
  "pages": [
    {
      "page_id": "runner-用户入口流",
      "title": "Runner 用户入口流",
      "page_goal": "冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。",
      "page_type": "single-page feature flow",
      "page_type_family": "generic",
      "platform": "web",
      "completion_definition": "用户完成主路径并满足 FEAT 成功标准。",
      "entry_condition": "用户进入 Runner 用户入口流 页面。",
      "exit_condition": "用户完成主路径后离开当前页面或进入下一步。",
      "main_path": [
        "进入 Runner 用户入口流",
        "查看首屏说明",
        "执行核心输入或选择",
        "点击主按钮",
        "接收校验与提交反馈",
        "进入下一步或完成本页"
      ],
      "branch_paths": [
        {
          "title": "Branch A",
          "steps": [
            "点击主按钮",
            "校验失败",
            "修正信息",
            "重新提交"
          ]
        },
        {
          "title": "Branch B",
          "steps": [
            "提交请求",
            "服务端失败",
            "展示错误",
            "允许重试"
          ]
        }
      ],
      "states": [
        {
          "name": "initial",
          "trigger": "页面首次进入",
          "ui_behavior": "展示默认结构与说明",
          "user_options": "开始主路径操作"
        },
        {
          "name": "ready",
          "trigger": "首屏可交互",
          "ui_behavior": "页面主要结构和主操作已就绪",
          "user_options": "执行主路径操作"
        },
        {
          "name": "partial",
          "trigger": "内容加载不完整",
          "ui_behavior": "展示局部状态和骨架",
          "user_options": "等待或刷新"
        },
        {
          "name": "retryable_error",
          "trigger": "页面内容获取失败",
          "ui_behavior": "展示错误并保留上下文",
          "user_options": "重试或退出"
        },
        {
          "name": "settled",
          "trigger": "内容稳定",
          "ui_behavior": "展示最终结构",
          "user_options": "继续操作"
        }
      ],
      "page_sections": [
        "Header",
        "Intro / Context",
        "Main Content",
        "Help / Error / Recovery Slot",
        "Footer"
      ],
      "information_priority": [
        "Goal and context first",
        "Primary interaction next",
        "Help and recovery last"
      ],
      "action_priority": [
        "Fill or edit content",
        "Click primary action",
        "Go back"
      ],
      "input_fields": [],
      "display_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-002",
          "label": "Frozen Feat Product Slice For Feat-Src-003-002",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "editable_ui_fields": [],
      "ui_visible_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-002",
          "label": "Frozen Feat Product Slice For Feat-Src-003-002",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "technical_payload_fields": [],
      "required_fields": [],
      "required_ui_fields": [],
      "user_actions": [
        "填写或编辑内容",
        "点击主按钮",
        "返回上一层"
      ],
      "system_actions": [
        "初始化页面",
        "前端校验",
        "提交请求",
        "更新页面状态"
      ],
      "frontend_validation_rules": [],
      "data_dependencies": [],
      "api_touchpoints": [],
      "loading_feedback": "关键区域局部 loading。",
      "validation_feedback": "字段或区域级错误反馈优先。",
      "success_feedback": "成功后进入下一步或刷新结果。",
      "error_feedback": "失败时展示明确错误并保留上下文。",
      "retry_behavior": "修正后允许再次提交。",
      "ascii_wireframe": "+--------------------------------------------------+\n| Header: Runner 用户入口流                           |\n| Intro / Context                                  |\n+--------------------------------------------------+\n| Main Content                                     |\n| Core Form / Core Decision / Core Result          |\n+--------------------------------------------------+\n| Help / Error / Recovery Slot                     |\n+--------------------------------------------------+\n| Footer: [返回]                          [下一步] |\n+--------------------------------------------------+",
      "buttons": [
        {
          "label": "继续",
          "action": "primary",
          "tone": "primary"
        },
        {
          "label": "重置场景",
          "action": "reset",
          "tone": "ghost"
        }
      ],
      "open_questions": [
        "ui_units 未显式提供，当前页面拆分由 feat-to-ui skill 基于 FEAT 内容推断。"
      ],
      "ui_spec_id": "",
      "fidelity_class": "feat_derived",
      "source_feat_ref": "FEAT-SRC-003-002"
    },
    {
      "page_id": "runner-控制面流",
      "title": "Runner 控制面流",
      "page_goal": "冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。",
      "page_type": "single-page feature flow",
      "page_type_family": "generic",
      "platform": "web",
      "completion_definition": "用户完成主路径并满足 FEAT 成功标准。",
      "entry_condition": "用户进入 Runner 控制面流 页面。",
      "exit_condition": "用户完成主路径后离开当前页面或进入下一步。",
      "main_path": [
        "进入 Runner 控制面流",
        "查看首屏说明",
        "执行核心输入或选择",
        "点击主按钮",
        "接收校验与提交反馈",
        "进入下一步或完成本页"
      ],
      "branch_paths": [
        {
          "title": "Branch A",
          "steps": [
            "点击主按钮",
            "校验失败",
            "修正信息",
            "重新提交"
          ]
        },
        {
          "title": "Branch B",
          "steps": [
            "提交请求",
            "服务端失败",
            "展示错误",
            "允许重试"
          ]
        }
      ],
      "states": [
        {
          "name": "initial",
          "trigger": "页面首次进入",
          "ui_behavior": "展示默认结构与说明",
          "user_options": "开始主路径操作"
        },
        {
          "name": "ready",
          "trigger": "首屏可交互",
          "ui_behavior": "页面主要结构和主操作已就绪",
          "user_options": "执行主路径操作"
        },
        {
          "name": "partial",
          "trigger": "内容加载不完整",
          "ui_behavior": "展示局部状态和骨架",
          "user_options": "等待或刷新"
        },
        {
          "name": "retryable_error",
          "trigger": "页面内容获取失败",
          "ui_behavior": "展示错误并保留上下文",
          "user_options": "重试或退出"
        },
        {
          "name": "settled",
          "trigger": "内容稳定",
          "ui_behavior": "展示最终结构",
          "user_options": "继续操作"
        }
      ],
      "page_sections": [
        "Header",
        "Intro / Context",
        "Main Content",
        "Help / Error / Recovery Slot",
        "Footer"
      ],
      "information_priority": [
        "Goal and context first",
        "Primary interaction next",
        "Help and recovery last"
      ],
      "action_priority": [
        "Fill or edit content",
        "Click primary action",
        "Go back"
      ],
      "input_fields": [],
      "display_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-003",
          "label": "Frozen Feat Product Slice For Feat-Src-003-003",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "editable_ui_fields": [],
      "ui_visible_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-003",
          "label": "Frozen Feat Product Slice For Feat-Src-003-003",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "technical_payload_fields": [],
      "required_fields": [],
      "required_ui_fields": [],
      "user_actions": [
        "填写或编辑内容",
        "点击主按钮",
        "返回上一层"
      ],
      "system_actions": [
        "初始化页面",
        "前端校验",
        "提交请求",
        "更新页面状态"
      ],
      "frontend_validation_rules": [],
      "data_dependencies": [],
      "api_touchpoints": [],
      "loading_feedback": "关键区域局部 loading。",
      "validation_feedback": "字段或区域级错误反馈优先。",
      "success_feedback": "成功后进入下一步或刷新结果。",
      "error_feedback": "失败时展示明确错误并保留上下文。",
      "retry_behavior": "修正后允许再次提交。",
      "ascii_wireframe": "+--------------------------------------------------+\n| Header: Runner 控制面流                            |\n| Intro / Context                                  |\n+--------------------------------------------------+\n| Main Content                                     |\n| Core Form / Core Decision / Core Result          |\n+--------------------------------------------------+\n| Help / Error / Recovery Slot                     |\n+--------------------------------------------------+\n| Footer: [返回]                          [下一步] |\n+--------------------------------------------------+",
      "buttons": [
        {
          "label": "继续",
          "action": "primary",
          "tone": "primary"
        },
        {
          "label": "重置场景",
          "action": "reset",
          "tone": "ghost"
        }
      ],
      "open_questions": [
        "ui_units 未显式提供，当前页面拆分由 feat-to-ui skill 基于 FEAT 内容推断。"
      ],
      "ui_spec_id": "",
      "fidelity_class": "feat_derived",
      "source_feat_ref": "FEAT-SRC-003-003"
    },
    {
      "page_id": "runner-运行监控流",
      "title": "Runner 运行监控流",
      "page_goal": "冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。",
      "page_type": "single-page feature flow",
      "page_type_family": "generic",
      "platform": "web",
      "completion_definition": "用户完成主路径并满足 FEAT 成功标准。",
      "entry_condition": "用户进入 Runner 运行监控流 页面。",
      "exit_condition": "用户完成主路径后离开当前页面或进入下一步。",
      "main_path": [
        "进入 Runner 运行监控流",
        "查看首屏说明",
        "执行核心输入或选择",
        "点击主按钮",
        "接收校验与提交反馈",
        "进入下一步或完成本页"
      ],
      "branch_paths": [
        {
          "title": "Branch A",
          "steps": [
            "点击主按钮",
            "校验失败",
            "修正信息",
            "重新提交"
          ]
        },
        {
          "title": "Branch B",
          "steps": [
            "提交请求",
            "服务端失败",
            "展示错误",
            "允许重试"
          ]
        }
      ],
      "states": [
        {
          "name": "initial",
          "trigger": "页面首次进入",
          "ui_behavior": "展示默认结构与说明",
          "user_options": "开始主路径操作"
        },
        {
          "name": "ready",
          "trigger": "首屏可交互",
          "ui_behavior": "页面主要结构和主操作已就绪",
          "user_options": "执行主路径操作"
        },
        {
          "name": "partial",
          "trigger": "内容加载不完整",
          "ui_behavior": "展示局部状态和骨架",
          "user_options": "等待或刷新"
        },
        {
          "name": "retryable_error",
          "trigger": "页面内容获取失败",
          "ui_behavior": "展示错误并保留上下文",
          "user_options": "重试或退出"
        },
        {
          "name": "settled",
          "trigger": "内容稳定",
          "ui_behavior": "展示最终结构",
          "user_options": "继续操作"
        }
      ],
      "page_sections": [
        "Header",
        "Intro / Context",
        "Main Content",
        "Help / Error / Recovery Slot",
        "Footer"
      ],
      "information_priority": [
        "Goal and context first",
        "Primary interaction next",
        "Help and recovery last"
      ],
      "action_priority": [
        "Fill or edit content",
        "Click primary action",
        "Go back"
      ],
      "input_fields": [],
      "display_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-007",
          "label": "Frozen Feat Product Slice For Feat-Src-003-007",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "editable_ui_fields": [],
      "ui_visible_fields": [
        {
          "field": "Frozen FEAT product slice for FEAT-SRC-003-007",
          "label": "Frozen Feat Product Slice For Feat-Src-003-007",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
          "label": "Feat-Specific Acceptance Checks For Downstream Tech And Testset Derivation",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        },
        {
          "field": "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
          "label": "Traceable Handoff Metadata For Downstream Governed Tech And Testset Workflows",
          "type": "string",
          "required": false,
          "source": "feat_input",
          "note": "无",
          "options": []
        }
      ],
      "technical_payload_fields": [],
      "required_fields": [],
      "required_ui_fields": [],
      "user_actions": [
        "填写或编辑内容",
        "点击主按钮",
        "返回上一层"
      ],
      "system_actions": [
        "初始化页面",
        "前端校验",
        "提交请求",
        "更新页面状态"
      ],
      "frontend_validation_rules": [],
      "data_dependencies": [],
      "api_touchpoints": [],
      "loading_feedback": "关键区域局部 loading。",
      "validation_feedback": "字段或区域级错误反馈优先。",
      "success_feedback": "成功后进入下一步或刷新结果。",
      "error_feedback": "失败时展示明确错误并保留上下文。",
      "retry_behavior": "修正后允许再次提交。",
      "ascii_wireframe": "+--------------------------------------------------+\n| Header: Runner 运行监控流                           |\n| Intro / Context                                  |\n+--------------------------------------------------+\n| Main Content                                     |\n| Core Form / Core Decision / Core Result          |\n+--------------------------------------------------+\n| Help / Error / Recovery Slot                     |\n+--------------------------------------------------+\n| Footer: [返回]                          [下一步] |\n+--------------------------------------------------+",
      "buttons": [
        {
          "label": "继续",
          "action": "primary",
          "tone": "primary"
        },
        {
          "label": "重置场景",
          "action": "reset",
          "tone": "ghost"
        }
      ],
      "open_questions": [
        "ui_units 未显式提供，当前页面拆分由 feat-to-ui skill 基于 FEAT 内容推断。"
      ],
      "ui_spec_id": "",
      "fidelity_class": "feat_derived",
      "source_feat_ref": "FEAT-SRC-003-007"
    }
  ]
};
