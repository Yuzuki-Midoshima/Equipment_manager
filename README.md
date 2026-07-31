# Equipment Manager

Autodesk Maya 2026向けの装備リグ管理ツールです。武器や小道具の追従先切り替え、弓の弦・矢の状態管理を、アニメーター向けUIから操作できます。

## Features

- 装備のWorld／Body／Hand追従切り替え
- 左右の装備状態を独立して管理
- Constraint Weightと表示状態の一括更新
- 弓の弦を引く／戻す操作
- 矢の保存状態と発射状態の切り替え
- Scene状態からUIを復元
- 不足Node・Attributeを明示するエラー処理

## Requirements

- Autodesk Maya 2026
- Python 3.11

## Installation

`Equipment_manager`フォルダをMayaのユーザースクリプトフォルダへ配置します。

```text
<Maya userAppDir>/scripts/Equipment_manager/
```

## Launch

Maya Script EditorのPythonタブ、またはPythonシェルフから実行します。

```python
from launch_equipment_manager import show
show()
```

## Project Structure

```text
Equipment_manager/
├── equipment_manager/
│   ├── app.py          # Composition root
│   ├── controller.py   # UI EventとServiceの調整
│   ├── services.py     # Equipment操作
│   ├── bow_service.py  # Bow／Arrow操作
│   ├── models.py       # 状態と設定データ
│   ├── constants.py    # Rig設定
│   ├── maya_utils.py   # Maya API境界
│   ├── ui.py           # Maya UI
│   └── exceptions.py   # Domain固有例外
├── tests/
└── launch_equipment_manager.py
```

## Architecture

UI、操作制御、Maya処理、設定データを分離しています。装備追加時はUIロジックを書き換えず、`constants.py`の設定と必要なService処理を拡張する構成です。

```text
UI → Controller → Equipment/Bow Services → Maya API
                       ↓
                  Models / Config
```

Sceneの存在確認やAttribute操作は`maya_utils.py`へ集約し、Service層では「装備をどの状態へ遷移させるか」に集中しています。

## Testing

Maya 2026の`mayapy`から実行します。

```powershell
mayapy -m unittest discover -s tests -p "test_*.py" -v
```

テストではMayaコマンドをFakeへ置き換え、状態遷移、Constraint Weight、弓・矢の操作、エラー条件を検証します。

## Known Constraints

- 対象リグのNode名とAttribute名は`constants.py`の設定に従います。
- リグ命名が異なる場合は、Sceneに合わせて設定を変更してください。
