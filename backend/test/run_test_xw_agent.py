#!/usr/bin/env python
"""
运行 WorkerNode 集成测试的脚本，自动加载测试环境变量
仿照 run_game_test.py 的实现，支持多环境变量文件加载
"""
import os
import sys
from pathlib import Path

# 确定 backend 目录的绝对路径
backend_dir = Path(__file__).resolve().parent

# 加载 .env 文件（多个候选位置，按优先级排列）
env_files_to_try = [
    backend_dir / '.env.test',
    backend_dir / '.env',
]

env_loaded = False
loaded_file = None

for env_file in env_files_to_try:
    if env_file.exists():
        print(f"✓ Loading environment variables from {env_file}")
        try:
            with open(env_file, encoding='utf-8') as f:
                loaded_count = 0
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key:
                                os.environ[key] = value
                                loaded_count += 1
                
                if loaded_count > 0:
                    print(f"  → Successfully loaded {loaded_count} environment variables")
                    env_loaded = True
                    loaded_file = env_file
                    break
        except Exception as e:
            print(f"  ⚠ Error reading {env_file}: {e}")
            continue

if not env_loaded:
    print(f"⚠ Warning: No .env file found, using system environment")
    print(f"  Tried: {[str(f) for f in env_files_to_try]}")
    print(f"  To use .env file, create one in {backend_dir}")

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, str(backend_dir))

# 现在导入并运行 WorkerNode 测试
print("\n" + "="*60)
print("Running WorkerNode Integration Tests")
if loaded_file:
    print(f"Configuration: {loaded_file.name}")
print("="*60 + "\n")

# 使用 exec 来运行测试文件，这样可以访问其全局作用域
test_file = backend_dir / 'integration' / 'test_agent_node.py'
if test_file.exists():
    try:
        with open(test_file, encoding='utf-8') as f:
            code = f.read()
        # 执行测试代码
        exec(code, {'__name__': '__main__', '__file__': str(test_file)})
    except Exception as e:
        print(f"✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print(f"✗ Error: {test_file} not found")
    sys.exit(1)
