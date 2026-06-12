# Metals Stock Pool

The metal pool is a hand-picked A-share universe for research. It mixes precious metals, copper, aluminum, zinc/lead, molybdenum/tin, rare earth and lithium names so the strategy is not tied to one commodity only.

| Symbol | Company | Metal theme |
|---|---|---|
| `601899` | 紫金矿业 | Gold, copper |
| `603993` | 洛阳钼业 | Copper, cobalt, molybdenum |
| `600547` | 山东黄金 | Gold |
| `600489` | 中金黄金 | Gold |
| `600988` | 赤峰黄金 | Gold |
| `600362` | 江西铜业 | Copper |
| `000630` | 铜陵有色 | Copper |
| `000878` | 云南铜业 | Copper |
| `601600` | 中国铝业 | Aluminum |
| `000807` | 云铝股份 | Aluminum |
| `600219` | 南山铝业 | Aluminum |
| `000933` | 神火股份 | Aluminum, coal power cost exposure |
| `601168` | 西部矿业 | Copper, lead, zinc |
| `600497` | 驰宏锌锗 | Zinc, germanium |
| `601958` | 金钼股份 | Molybdenum |
| `000960` | 锡业股份 | Tin |
| `600111` | 北方稀土 | Rare earth |
| `000831` | 中国稀土 | Rare earth |
| `002460` | 赣锋锂业 | Lithium |
| `002466` | 天齐锂业 | Lithium |

Run a metals prediction with:

```powershell
python run_mvp.py predict --config configs\metals.json --source auto --output-dir reports\metals_predict
```

Highlight one stock:

```powershell
python run_mvp.py predict --config configs\metals.json --source auto --symbol 601899 --output-dir reports\metals_predict
```

`source=auto` tries AKShare first and falls back to deterministic sample data per symbol if a request fails. For serious research, replace this universe with an index/industry classification sourced from a point-in-time vendor.

Use `--source akshare` for a strict real-data run. In strict mode, any failed symbol fetch stops the run so you do not accidentally mix real and sample data.
