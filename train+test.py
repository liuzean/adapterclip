import subprocess
import sys

def main():
    print("="*50)
    print("🚀 开始运行: train.py")
    print("="*50)
    
    # 使用 sys.executable 确保使用当前相同的 Python 解释器环境运行
    train_process = subprocess.run([sys.executable, "train.py"])
    
    # 检查 train.py 是否运行成功
    if train_process.returncode != 0:
        print("\n❌ train.py 运行失败或被中断，退出后续测试程序。")
        sys.exit(train_process.returncode)
        
    print("\n" + "="*50)
    print("✅ train.py 运行完成！")
    print("🚀 开始运行: test.py")
    print("="*50)
    
    test_process = subprocess.run([sys.executable, "test.py"])
    
    # 检查 test.py 是否运行成功
    if test_process.returncode != 0:
        print("\n❌ test.py 运行遇到错误。")
        sys.exit(test_process.returncode)
        
    print("\n" + "="*50)
    print("🎉 训练 (train.py) 和 测试 (test.py) 均已全部运行完成！")
    print("="*50)

if __name__ == "__main__":
    main()