import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    base = os.path.dirname(os.path.abspath(__file__))
    print('  === 软件造价自动生成器 ===')
    print(f'  启动服务: http://localhost:{port}')
    print(f'  数据目录: {os.path.join(base, "instance")}')
    print(f'  导出目录: {os.path.join(base, "exports")}')
    print()
    app.run(host='0.0.0.0', port=port, debug=True)
