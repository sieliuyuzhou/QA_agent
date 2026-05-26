import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_llm_module():
    print("\n" + "=" * 60)
    print("[测试] LLM 模块")
    print("=" * 60)
    
    try:
        from llm import chat_service, ChatService
        print("[OK] 导入 llm 模块成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        service = ChatService()
        print(f"[OK] ChatService 实例化成功")
        print(f"     - model: {service.model_name}")
        print(f"     - base_url: {service.base_url}")
    except Exception as e:
        print(f"[FAIL] ChatService 实例化失败: {e}")
        return False
    
    try:
        from llm.exceptions import (
            ModelException,
            ModelTimeoutError,
            ModelRateLimitError,
            ModelAuthenticationError,
            ModelConnectionError,
        )
        print("[OK] 导入异常类成功")
    except ImportError as e:
        print(f"[FAIL] 导入异常类失败: {e}")
        return False
    
    return True


def test_rag_module():
    print("\n" + "=" * 60)
    print("[测试] RAG 模块 (infrastructure.rag)")
    print("=" * 60)
    
    try:
        from infrastructure.rag import get_store, VectorStore
        from infrastructure.rag import RAGException, EmbeddingError, VectorStoreError
        print("[OK] 导入 infrastructure.rag 模块成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        store = get_store()
        print(f"[OK] VectorStore 实例化成功")
        print(f"     - persist_dir: {store.persist_dir}")
        print(f"     - collection_name: {store.collection_name}")
    except Exception as e:
        print(f"[FAIL] VectorStore 实例化失败: {e}")
        return False
    
    try:
        count = store.count()
        print(f"[OK] 数据库连接成功，当前文档数: {count}")
    except Exception as e:
        print(f"[FAIL] 数据库连接失败: {e}")
        return False
    
    if count == 0:
        print("[WARN] 数据库为空，跳过检索测试")
        print("       请先运行 python scripts/import_faq.py 导入数据")
    else:
        try:
            results = store.search("测试查询", top_k=1)
            print(f"[OK] 检索功能正常，返回 {len(results)} 条结果")
        except Exception as e:
            print(f"[FAIL] 检索功能失败: {e}")
            return False
    
    return True


def test_tools_module():
    print("\n" + "=" * 60)
    print("[测试] Tools 模块")
    print("=" * 60)
    
    try:
        from tools import Tool, ToolParameter
        print("[OK] 导入 tools 模块成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        def dummy_func(query: str, count: int = 1) -> str:
            return f"结果: {query} (count={count})"
        
        tool = Tool(
            name="test_tool",
            description="测试工具",
            func=dummy_func,
            parameters=[
                ToolParameter(name="query", type="string", description="查询内容"),
                ToolParameter(name="count", type="integer", description="数量", required=False, default=1),
            ]
        )
        print("[OK] Tool 实例化成功")
        
        result = tool.run({"query": "hello"})
        print(f"[OK] Tool.run() 执行成功: {result}")
        
        result_with_optional = tool.run({"query": "world", "count": 3})
        print(f"[OK] Tool.run() 可选参数测试: {result_with_optional}")
        
        desc = tool.to_prompt_desc()
        print(f"[OK] Tool.to_prompt_desc(): {desc}")
        
        schema = tool.to_openai_schema()
        print(f"[OK] Tool.to_openai_schema() 生成成功")
    except Exception as e:
        print(f"[FAIL] Tool 功能测试失败: {e}")
        return False
    
    try:
        tool.run({})
        print(f"[FAIL] 缺少必填参数应抛出异常")
        return False
    except ValueError as e:
        print(f"[OK] 缺少必填参数正确抛出异常: {e}")
    
    return True


def test_faq_search_tool():
    print("\n" + "=" * 60)
    print("[测试] FAQ 检索工具")
    print("=" * 60)
    
    try:
        from tools import search_faq, search_faq_tool
        print("[OK] 导入 search_faq 和 search_faq_tool 成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        from infrastructure.rag import get_store
        store = get_store()
        count = store.count()
        
        if count == 0:
            print("[WARN] 数据库为空，跳过 FAQ 检索测试")
            print("       请先运行 python scripts/import_faq.py 导入数据")
            return True
    except Exception as e:
        print(f"[FAIL] 获取数据库状态失败: {e}")
        return False
    
    try:
        print("[INFO] 测试 search_faq() 函数...")
        result = search_faq("WiFi", top_k=2)
        print(f"[OK] search_faq() 返回成功")
        print(f"     结果预览: {result[:100]}...")
    except Exception as e:
        print(f"[FAIL] search_faq() 执行失败: {e}")
        return False
    
    try:
        print("[INFO] 测试 search_faq_tool.run()...")
        result = search_faq_tool.run({"query": "电池"})
        print(f"[OK] search_faq_tool.run() 返回成功")
        print(f"     结果预览: {result[:100]}...")
    except Exception as e:
        print(f"[FAIL] search_faq_tool.run() 执行失败: {e}")
        return False
    
    try:
        desc = search_faq_tool.to_prompt_desc()
        print(f"[OK] search_faq_tool.to_prompt_desc(): {desc}")
    except Exception as e:
        print(f"[FAIL] to_prompt_desc() 失败: {e}")
        return False
    
    return True


def test_utils_module():
    print("\n" + "=" * 60)
    print("[测试] Utils 模块")
    print("=" * 60)
    
    try:
        from utils import ConversationManager
        print("[OK] 导入 utils 模块成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        manager = ConversationManager()
        print("[OK] ConversationManager 实例化成功（占位实现）")
    except Exception as e:
        print(f"[FAIL] ConversationManager 实例化失败: {e}")
        return False
    
    return True


def test_domain_module():
    print("\n" + "=" * 60)
    print("[测试] Domain 模块")
    print("=" * 60)
    
    try:
        from domain import CustomerServiceAgent, AgentResponse
        print("[OK] 导入 domain 模块成功")
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        response = AgentResponse(
            type="final_answer",
            content="测试内容",
            conversation_id="test-id"
        )
        print(f"[OK] AgentResponse 实例化成功")
        print(f"     - type: {response.type}")
        print(f"     - content: {response.content}")
    except Exception as e:
        print(f"[FAIL] AgentResponse 实例化失败: {e}")
        return False
    
    try:
        from llm import chat_service
        from utils import ConversationManager
        from tools import Tool, ToolParameter
        
        def dummy_func(query: str) -> str:
            return query
        
        dummy_tool = Tool(
            name="dummy",
            description="dummy",
            func=dummy_func,
            parameters=[]
        )
        
        agent = CustomerServiceAgent(
            llm=chat_service,
            conversation_manager=ConversationManager(),
            tools=[dummy_tool]
        )
        print("[OK] CustomerServiceAgent 实例化成功（占位实现）")
    except Exception as e:
        print(f"[FAIL] CustomerServiceAgent 实例化失败: {e}")
        return False
    
    return True


def test_llm_chat():
    print("\n" + "=" * 60)
    print("[测试] LLM 聊天功能（需要配置 API）")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print("[SKIP] 未配置 LLM_API_KEY，跳过实际调用测试")
        return True
    
    try:
        from llm import chat_service
        
        print("[INFO] 正在调用 LLM API...")
        response = chat_service.chat("你好，你是谁？")
        print(f"[OK] LLM 响应: {response[:]}...")
        return True
    except Exception as e:
        print(f"[FAIL] LLM 调用失败: {e}")
        return False


def main():
    print("\n" + "#" * 60)
    print("# 功能冒烟测试脚本")
    print("#" * 60)
    
    results = []
    
    results.append(("LLM 模块", test_llm_module()))
    results.append(("RAG 模块", test_rag_module()))
    results.append(("Tools 模块", test_tools_module()))
    results.append(("FAQ 检索工具", test_faq_search_tool()))
    results.append(("Utils 模块", test_utils_module()))
    results.append(("Domain 模块", test_domain_module()))
    results.append(("LLM 聊天功能", test_llm_chat()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有冒烟测试通过！")
        print("=" * 60)
        return 0
    else:
        print("[FAILED] 存在测试失败项！")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
