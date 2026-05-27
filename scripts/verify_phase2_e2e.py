"""Phase 1+2 端到端验证脚本 - 验证 Supervisor 多智能体架构全链路"""
import sys
import json
import requests

BASE = "http://localhost:8000"
HEADERS = {"X-QA-User-Id": "customer_alice", "Content-Type": "application/json"}


def create_conversation():
    r = requests.post(f"{BASE}/api/conversations", headers=HEADERS)
    assert r.status_code == 200, f"创建会话失败: {r.text}"
    return r.json()["conversation_id"]


def chat(conv_id, message):
    r = requests.post(f"{BASE}/api/chat", headers=HEADERS,
                      json={"conversation_id": conv_id, "message": message})
    assert r.status_code == 200, f"聊天失败: {r.text}"
    return r.json()


def verify(name, response, expected_type, expected_agent=None, min_citations=0):
    ok = True
    errors = []

    if response["type"] != expected_type:
        errors.append(f"类型不匹配: 期望 {expected_type}, 实际 {response['type']}")
        ok = False

    actual_agent = response.get("metadata", {}).get("sub_agent", "N/A")
    if expected_agent and actual_agent != expected_agent:
        errors.append(f"路由不匹配: 期望 {expected_agent}, 实际 {actual_agent}")
        ok = False

    if len(response.get("citations", [])) < min_citations:
        errors.append(f"引用不足: 期望 >= {min_citations}, 实际 {len(response.get('citations', []))}")
        ok = False

    status = "PASS" if ok else "FAIL"
    print(f"\n[{status}] {name}")
    print(f"  路由: {actual_agent}")
    print(f"  类型: {response['type']}")
    print(f"  引用: {len(response.get('citations', []))} 条")
    print(f"  内容: {response['content'][:80]}...")
    if errors:
        for e in errors:
            print(f"  错误: {e}")
    return ok


def main():
    print("=" * 60)
    print("Phase 1+2 端到端验证")
    print("=" * 60)

    results = []

    # 场景 1: 产品咨询
    conv = create_conversation()
    resp = chat(conv, "X2 支持 Zigbee 吗？")
    results.append(verify("产品咨询", resp, "final_answer", "ConsultationHandler", 1))

    # 场景 2: 故障排查
    conv = create_conversation()
    resp = chat(conv, "X1 连不上 WiFi")
    results.append(verify("故障排查", resp, "final_answer", "TroubleshootingAgent", 1))

    # 场景 3: 售后办理（使用 ORD-A-C1，购买于 2026-03-01，在保修期内）
    conv = create_conversation()
    resp = chat(conv, "我的订单 ORD-A-C1 要申请保修维修，产品无法开机，不是人为损坏")
    results.append(verify("售后办理", resp, "confirm_action", "AfterSalesAgent", 1))

    # 场景 4: 转人工
    conv = create_conversation()
    resp = chat(conv, "转人工")
    results.append(verify("转人工", resp, "handoff"))

    # 场景 5: 未知问题转人工（用明确超出知识库范围的问题）
    conv = create_conversation()
    resp = chat(conv, "帮我写一首诗")
    results.append(verify("未知问题", resp, "handoff"))

    # 场景 6: 管理侧接口
    r = requests.get(f"{BASE}/api/admin/conversations",
                     headers={"X-QA-User-Id": "admin_zhang", "Content-Type": "application/json"})
    admin_ok = r.status_code == 200
    print(f"\n[{'PASS' if admin_ok else 'FAIL'}] 管理侧会话列表 (status={r.status_code})")
    results.append(admin_ok)

    # 场景 7: 权限隔离
    r = requests.get(f"{BASE}/api/orders",
                     headers={"X-QA-User-Id": "customer_bob", "Content-Type": "application/json"})
    bob_orders = r.json()
    alice_order_visible = any(o.get("order_id") == "ORD-A-X1" for o in bob_orders.get("orders", []))
    perm_ok = not alice_order_visible
    print(f"\n[{'PASS' if perm_ok else 'FAIL'}] 权限隔离: Bob 看不到 Alice 订单")
    results.append(perm_ok)

    # 汇总
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    print(f"结果: {passed}/{total} 通过")
    if passed == total:
        print("全部验证通过!")
    else:
        print(f"有 {total - passed} 项未通过")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
