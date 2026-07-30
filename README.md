# Equipment Manager

Maya 2026向けの、Sword・Shield・Bow・Arrow・String操作をまとめたアニメーター用装備管理ツールです。左右の持ち替えと装備ごとの位置補正を、同じUIから安全に操作できます。

## 対象ユーザー

- キャラクターアニメーター
- Maya用リグ／パイプラインツール開発者
- PythonによるMayaツールの責務分離例を確認したい方

## 解決する課題

手作業でConstraint WeightやSpace Attributeを変更すると、設定漏れや左右の値の取り違えが起こります。本ツールは装備操作を定型化し、アニメーターが保存した左右別オフセットを持ち替え後に復元します。

## 主な機能

- Sword・Shield・Bowの左右持ち替え
- 装備ごとの左右別オフセット保存／復元
- 装備Follow ON／OFF
- Arrowの左右切り替え、Follow、オフセット保存
- Arrow Reset基準の保存／ワールド位置への1回スナップ
- String Release／String Follow
- String Follow OFF時のIK姿勢からFKコントローラーへの姿勢合わせ
- String Follow ON時のFK姿勢からIK Hand／Pole Vectorへの姿勢合わせ
- 選択中の手、Follow状態、装備タブの表示同期
- 不足ノードや不正なConstraint Aliasの警告表示
- 起動時と装備タブ切り替え時のシーン状態読み取り同期

## 動作環境

- Autodesk Maya 2026
- Maya付属Python 3
- `maya.cmds`
- 外部Pythonパッケージ不要

## インストール

`3Weapons` フォルダを任意のMayaスクリプト用フォルダへ配置し、そのフォルダを `sys.path` に追加します。リグ側には [constants.py](equipment_manager/constants.py) に記載されたノードとAttributeが必要です。

## 起動方法

通常利用時は次の2行で起動できます。

```python
from launch_equipment_manager import show
show()
```

### シェルフ登録

次のコードをPythonシェルフへ登録してください。

```python
import sys
from pathlib import Path

import maya.cmds as cmds

scripts_path = (
    Path(cmds.internalVar(userAppDir=True))
    / "scripts"
    / "3Weapons"
)
scripts_path_text = str(scripts_path)

if scripts_path_text not in sys.path:
    sys.path.insert(0, scripts_path_text)

from launch_equipment_manager import show
show()
```

この例はMayaのユーザールートを基準に相対的に解決するため、ユーザー名、ドライブ、OneDriveの有無、Mayaの表示言語に依存しません。`3Weapons` フォルダは `cmds.internalVar(userAppDir=True)` が返すフォルダ内の `scripts` 直下へ配置してください。

開発中にMayaを再起動せず変更を読み直す場合は、`3Weapons_shelf.py` の内容をシェルフコマンドとして使用できます。このスクリプトは本ツールのパッケージだけを再読み込みします。

## ファイル構成

```text
3Weapons/
├─ equipment_manager/
│  ├─ __init__.py       # 公開パッケージAPI
│  ├─ app.py            # 依存オブジェクトの生成とアプリ起動
│  ├─ controller.py     # UIイベントと状態遷移の調整
│  ├─ ui.py             # Maya UIの生成と表示更新
│  ├─ services.py       # Sword・Shield・Bow共通のシーン操作
│  ├─ bow_service.py    # Arrow・String固有のシーン操作
│  ├─ models.py         # 設定／状態の型モデル
│  ├─ constants.py      # リグ依存値とUI定数
│  ├─ exceptions.py     # ユーザー向けドメイン例外
│  └─ maya_utils.py     # Constraint／Transform共通処理
├─ launch_equipment_manager.py # 通常起動用エントリーポイント
├─ 3Weapons_shelf.py            # 開発時の再読み込み用シェルフコード
├─ tests/                        # Mayaシーン不要のロジックテスト
├─ .gitignore                    # Pythonキャッシュの除外設定
└─ README.md
```

## アーキテクチャ

```text
Shelf / launch_equipment_manager.show()
  ↓
EquipmentManagerApp
  ↓
EquipmentController ─── EquipmentState
  ├─ EquipmentService ── Maya scene
  ├─ BowService ──────── Maya scene
  └─ EquipmentManagerUI
           ↓
        Maya UI
```

### クラスごとの責務

- `EquipmentManagerApp`: `maya.cmds` を各層へ注入し、Service・Controller・UIを組み立てます。
- `EquipmentController`: ボタンイベント、状態遷移、エラー通知、表示更新の順序を管理します。
- `EquipmentService`: 3装備に共通する持ち替え、Follow、Constraint、Space、Offsetを操作します。
- `BowService`: ArrowのFollow／Pose／OffsetとString操作を担当します。
- `EquipmentManagerUI`: UIハンドルをインスタンス内で所有し、受け取った状態だけを描画します。

## 状態管理方針

`EquipmentState` を状態の唯一の正本としています。選択中装備、装備側、装備Follow、Arrow側、Arrow Follow、String Followをモジュールグローバルへ複製しません。UIは状態を保持せず、Controllerから渡された状態を表示します。

起動時は `setAttr`、Constraint変更、Offset復元を行いません。Swordの `weaponSpace`、Shieldの `shieldSpace`、Bowの `bowSpace`、Arrow/BowのConstraint Weight、String Followに使用する腕のFKIKを読み取り、状態へ同期してから描画します。装備タブ切り替え時も、切り替え先装備のSideとFollowをシーンから再取得します。

Bowでは `ALL_Bow_anim.bowSpace` の `0 = Left`、`1 = Right` を持ち手の正本とし、Constraint WeightはFollow状態だけに使用します。そのため左右Weightが両方0のFollow OFF中もBow Sideは維持されます。Follow OFF中の持ち替えは `bowSpace` とOffsetだけを更新し、Followを勝手にONへ戻しません。

ArrowのConstraint Weightが両方0の場合はFollow OFFとして扱い、Arrow Sideは不明状態としてチェックマークを表示しません。Bow／Arrowとも左右Weightが同時に有効な場合は、UIで表現できない異常状態として警告します。

## Arrow Save／Reset仕様

- Arrowのアニメーション／左右Offset操作用コントロールは `Arrow_anim` です。
- Resetで移動するArrow本体は `Arrow_LOC` です。
- Reset基準は `String_Reset_LOC` です。
- `ALLOW SAVE` は `Arrow_LOC` の現在ワールド行列を `String_Reset_LOC` へ保存します。
- `ARROW RESET` は `Arrow_LOC` を `String_Reset_LOC` のワールド行列へ1回だけスナップします。
- どちらの操作も親子付けを変更しないため、BowとArrowの別階層を維持します。

## 設計意図

- UIとシーン操作を分離し、レイアウト変更がリグ処理へ影響しにくい構造にしました。
- 状態を1か所へ集約し、ボタン表示と操作対象の不一致を防ぎます。
- リグ依存値を `constants.py` へ集約し、処理コードからノード名を排除しました。
- `maya.cmds` をコンストラクタから注入し、状態遷移や計算をMayaシーンなしでテスト可能にしました。
- 装備定義を `EquipmentConfig` としたため、同じ操作規則の装備は設定追加を中心に拡張できます。

## エラー処理方針

必要ノード、Attribute、Constraint Weight Aliasを操作前に検証します。想定可能な問題は専用例外へ変換し、ControllerがMaya Script Editorへ `cmds.warning`、Viewportへ短いメッセージを表示します。例外を無条件に握りつぶす処理は使用していません。

## 新しい装備の追加

1. `constants.py` の `EQUIPMENT_CONFIGS` へ `EquipmentConfig` を追加します。
2. 既存3装備と異なる切替規則がある場合だけ `EquipmentService.switch_side()` に小さな戦略分岐を追加します。
3. UIタブが必要なら `EquipmentManagerUI` のタブ定義を追加します。
4. 設定取得、状態遷移、Constraint Weightのテストを追加します。

## Maya内での手動確認項目

- ウィンドウが1つだけ開き、再起動でも重複しない
- Sword／Shield／Bowの左右持ち替えと黄色い状態表示
- 起動しただけではSpace、Constraint、Transformが変更されない
- タブ切り替え時に各装備固有のSide／Followが再取得される
- 各装備の左右Offset Saveと復元
- 各装備のFollow ON／OFF
- Arrow左右、Follow、Offset Save
- ALLOW SAVEで`String_Reset_LOC`へ基準保存
- ARROW RESETで`Arrow_LOC`が基準へ1回スナップする
- String Release、String Follow ON／OFF
- チェックマーク、色、Bowセクション表示と実状態の一致
- 不足ノード／Attributeで理解しやすい警告が出る

## テスト

Mayaシーン不要のテストはMaya 2026の `mayapy` で実行できます。

```powershell
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" -m unittest discover -s tests -v
```

テスト対象はSword／Shield／BowのSpace値、Bow／ArrowのConstraint Weight、Bow Follow OFFを維持した持ち替え、ゼロWeight、左右同時Weight、タブ切り替え時の再同期、String FollowのBow Side参照、読み取り専用起動、Arrow Reset対象、UIラベル、状態遷移です。実際のリグノードを変更する操作はMaya内の手動確認対象です。

## 既知の制約

- リグのノード名とAttribute名は `constants.py` の契約に依存します。
- 複数キャラクターのNamespace自動解決には未対応です。
- Maya GUIと対象リグが必要なため、シーン操作の完全自動テストは含みません。
- 実リグ上の `Arrow_LOC` と `String_Reset_LOC` の階層・ロック状態はMaya内で手動確認が必要です。
- String Follow ONでは、`Ik_{side}_hand_anim`を`{side}_wrist_skn_jnt`へ位置・回転とも`matchTransform`します。Pole Vectorは`shoulder/elbow/wrist_skn_jnt`が作る現在の腕平面上へ配置し、距離には上腕長と前腕長の合計を使用します。固定X／Yオフセットは加えないため、FK→IK切替時にElbowが腕平面からずれることを防ぎます。その後`FKIK=1`へ切り替え、IK HandとStringコントロールを選択します。
- String Follow OFFでIKからFKへ戻す際は、`IK_{side}_shoulder_jnt`、`IK_{side}_elbow_jnt`、`IK_{side}_wrist_jnt`の現在ワールド姿勢を、対応する`FK_{side}_shoulder_anim`、`FK_{side}_elbow_anim`、`FK_{side}_wrist_anim`へ適用してから`FKIK=0`へ切り替えます。
- 必要なJointまたはFKコントローラーがない場合は、FKIKを変更せずScript EditorとViewportへエラーを表示します。
