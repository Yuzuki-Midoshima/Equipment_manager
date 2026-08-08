# Equipment Manager for Maya

Autodesk Maya 2026でSword、Shield、Bow、Arrow、Stringの持ち替えや追従状態を管理する、キャラクターアニメーター向けツールです。リガーやTechnical Artistがリグ操作を安全に定型化するための、責務分離されたPython実装例でもあります。

## Overview

Constraint WeightやSpace Attributeを手作業で切り替える際の設定漏れを防ぎ、装備ごとの左右持ち替え、Follow、保存済みオフセットの復元を1つのMaya UIへまとめます。起動時と装備タブ切り替え時にはシーンを読み取り、UI表示を実際のリグ状態へ同期します。

## Demo

デモ画像・動画は[`docs/media/`](docs/media/)へ追加できます。ポートフォリオ素材をMayaパッケージから分離し、コードを変更せず更新できる構成です。

## Features

- Sword、Shield、Bowの左右持ち替えとFollow ON/OFF
- 装備ごとの左右別Transform Offset保存・復元
- Arrowの左右切り替え、Follow、Offset保存
- Arrow姿勢の保存と`String_Reset_LOC`への1回スナップ
- String ReleaseとString Follow ON/OFF
- String Follow切り替え時のFK/IKコントローラー姿勢合わせ
- 選択装備、持ち手、Follow状態を反映するUI
- 必要ノード、Attribute、Constraint Alias、不正な同時Weightの検証
- 起動時にリグを変更しない読み取り専用の状態同期

## Installation

1. リポジトリをMayaユーザーディレクトリの`scripts/Equipment_manager`へ配置します。
2. MayaのPython Script Editorから次を実行します。

```python
from launch_equipment_manager import show

show()
```

リポジトリを別の場所へ配置する場合は、そのルートをMayaの`PYTHONPATH`または`sys.path`へ追加してください。

### Maya Shelf

開発中にMayaを再起動せず本ツールだけを再読み込みする場合は、[`equipment_manager_shelf.py`](equipment_manager_shelf.py)の内容をPython Shelfへ登録します。このスクリプトは`cmds.internalVar(userAppDir=True)`を基準に`scripts/Equipment_manager`を解決するため、ユーザー名やドライブ文字へ依存しません。

## Usage

1. Mayaで対象リグを開き、ツールを起動します。
2. Sword、Shield、Bowのタブを選択します。
3. 左右のHandボタンで持ち手を切り替えます。
4. 必要に応じてOffsetを保存し、Followを切り替えます。
5. BowタブではArrow、String Follow、Arrow Save/Reset、String Releaseを操作します。

リグ側には[`equipment_manager/constants.py`](equipment_manager/constants.py)で定義されたノード名、Attribute、Constraint Weight Aliasが必要です。

## Technical Highlights

- `EquipmentManagerApp`が注入された`maya.cmds`をService、Controller、UIへ渡すcomposition root
- シーン操作を`EquipmentService`と`BowService`、状態遷移を`EquipmentController`、描画を`EquipmentManagerUI`へ分離
- `EquipmentState`へ選択装備と各Follow状態を集約し、UIと操作対象の不一致を防止
- 不変のリグ設定をfrozen dataclass、左右を`Side` Enumとして表現
- 動的なparentConstraint aliasを解決し、左右同時Weightをドメインエラーとして検出
- FK/IK切り替え前に現在姿勢を合わせ、Pole Vectorをshoulder/elbow/wristの腕平面から計算
- `maya.cmds`境界をFakeへ置換し、Mayaなしでサービスと状態遷移を検証可能

## Project Structure

```text
equipment_manager/             アプリケーションパッケージ
  app.py                       依存オブジェクトの組み立て
  controller.py                UIイベントと状態遷移
  services.py                  装備共通のMayaシーン操作
  bow_service.py               Bow、Arrow、String固有処理
  ui.py                        maya.cmds UI
  models.py                    設定・状態モデル
  constants.py                 リグ契約とUI定数
  maya_utils.py                Constraint・Transform共通処理
  exceptions.py                ユーザー向けドメイン例外
tests/                         Maya非依存unit tests
docs/media/                    Demo素材
launch_equipment_manager.py    通常起動エントリーポイント
equipment_manager_shelf.py     開発用Shelf・reloadスクリプト
```

Mayaからのimportと既存起動方法を維持するため、無理な`src/` layoutへの変更は行っていません。

## Requirements

- Autodesk Maya 2026
- Python 3.11（Maya 2026同梱）
- `maya.cmds`
- 外部Pythonパッケージ不要

本ツールは[`constants.py`](equipment_manager/constants.py)の命名契約に合う単一リグを対象とし、複数Character Namespaceの自動解決には対応していません。

## Testing

### Automated Tests

Maya非依存の22件のunit testは標準ライブラリだけで実行できます。

```bash
python -m unittest discover -s tests -v
```

自動テストでは、Space値とSide判定、Constraint Weight、Follow維持、Arrow Reset、FK/IK姿勢合わせ指示、Pole Vector計算、Controller状態遷移、読み取り専用起動、UIラベルをFake `maya.cmds`で検証します。GitHub Actionsではさらに全Pythonファイルのcompile checkとMaya非依存import checkを実行します。

### Maya Manual Tests

- ウィンドウが重複せず起動・再読み込みできること
- 起動だけではSpace、Constraint、Transformが変更されないこと
- Sword、Shield、Bow、Arrowの左右持ち替えとFollow
- 保存した左右Offsetの復元
- Arrow Save/Resetと実階層・lock状態
- String ReleaseとString Follow ON/OFF
- 実リグ上のFK/IK姿勢一致とPole Vector位置
- UIのチェックマーク、色、Bowセクションとシーン状態の一致
- 不足ノードや不正Constraint状態の警告表示
- Maya Undoおよびアニメーションワークフローへの影響

## Development Workflow

変更は`feature/*`、`fix/*`、`chore/*`ブランチで行い、`main`向けPull Requestを作成します。CI成功とMaya手動確認の後にのみmergeし、`main`を公開可能な安定版として維持します。

## License

ライセンスは現在指定されていません。再配布・利用条件を公開する場合は、リポジトリ所有者が適切なライセンスを選択してください。
