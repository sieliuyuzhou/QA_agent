import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_directory_structure():
    print("=" * 60)
    print("目录结构验证")
    print("=" * 60)
    
    required_dirs = [
        "llm",
        "tools",
        "utils",
        "domain",
        "domain/customer_service",
        "apps",
        "apps/customer_service",
        "infrastructure",
        "infrastructure/rag",
    ]
    
    removed_dirs = [
        "model",
        "rag",
        "retriever",
        "api",
    ]
    
    all_passed = True
    
    print("\n[检查] 新目录是否存在...")
    for dir_name in required_dirs:
        dir_path = Path(__file__).parent.parent / dir_name
        if dir_path.exists():
            print(f"  [OK] {dir_name}/")
        else:
            print(f"  [FAIL] {dir_name}/ 不存在")
            all_passed = False
    
    print("\n[检查] 旧目录是否已删除...")
    for dir_name in removed_dirs:
        dir_path = Path(__file__).parent.parent / dir_name
        if not dir_path.exists():
            print(f"  [OK] {dir_name}/ 已删除")
        else:
            print(f"  [FAIL] {dir_name}/ 仍然存在")
            all_passed = False
    
    return all_passed


def check_imports():
    print("\n" + "=" * 60)
    print("Import 路径验证")
    print("=" * 60)
    
    all_passed = True
    
    print("\n[检查] llm 模块...")
    try:
        from llm import chat_service, ChatService
        print("  [OK] from llm import chat_service, ChatService")
    except ImportError as e:
        print(f"  [FAIL] {e}")
        all_passed = False
    
    print("\n[检查] infrastructure.rag 模块...")
    try:
        from infrastructure.rag import get_store, VectorStore
        print("  [OK] from infrastructure.rag import get_store, VectorStore")
    except ImportError as e:
        print(f"  [FAIL] {e}")
        all_passed = False
    
    print("\n[检查] tools 模块...")
    try:
        from tools import Tool, ToolParameter
        print("  [OK] from tools import Tool, ToolParameter")
    except ImportError as e:
        print(f"  [FAIL] {e}")
        all_passed = False
    
    print("\n[检查] utils 模块...")
    try:
        from utils import ConversationManager
        print("  [OK] from utils import ConversationManager")
    except ImportError as e:
        print(f"  [FAIL] {e}")
        all_passed = False
    
    print("\n[检查] domain 模块...")
    try:
        from domain import CustomerServiceAgent, AgentResponse
        print("  [OK] from domain import CustomerServiceAgent, AgentResponse")
    except ImportError as e:
        print(f"  [FAIL] {e}")
        all_passed = False
    
    return all_passed


def check_env_file():
    print("\n" + "=" * 60)
    print("环境变量文件验证")
    print("=" * 60)
    
    env_path = Path(__file__).parent.parent / ".env"
    env_example_path = Path(__file__).parent.parent / ".env.example"
    
    all_passed = True
    
    if env_path.exists():
        print(f"  [OK] .env 文件存在")
    else:
        print(f"  [FAIL] .env 文件不存在")
        all_passed = False
    
    if env_example_path.exists():
        print(f"  [OK] .env.example 文件存在")
    else:
        print(f"  [FAIL] .env.example 文件不存在")
        all_passed = False
    
    return all_passed


def check_file_existence():
    print("\n" + "=" * 60)
    print("关键文件验证")
    print("=" * 60)
    
    required_files = [
        "llm/__init__.py",
        "llm/client.py",
        "llm/exceptions.py",
        "infrastructure/__init__.py",
        "infrastructure/rag/__init__.py",
        "infrastructure/rag/store.py",
        "infrastructure/rag/embedding.py",
        "infrastructure/rag/exceptions.py",
        "tools/__init__.py",
        "tools/base.py",
        "utils/__init__.py",
        "domain/__init__.py",
        "domain/customer_service/__init__.py",
    ]
    
    all_passed = True
    
    for file_name in required_files:
        file_path = Path(__file__).parent.parent / file_name
        if file_path.exists():
            print(f"  [OK] {file_name}")
        else:
            print(f"  [FAIL] {file_name} 不存在")
            all_passed = False
    
    return all_passed


def main():
    print("\n" + "#" * 60)
    print("# 项目迁移验证脚本")
    print("#" * 60)
    
    results = []
    
    results.append(("目录结构", check_directory_structure()))
    results.append(("Import路径", check_imports()))
    results.append(("环境变量文件", check_env_file()))
    results.append(("关键文件", check_file_existence()))
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有验证通过，迁移成功！")
        print("=" * 60)
        return 0
    else:
        print("[FAILED] 存在验证失败项，请检查！")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
