# 🀄 日麻 AI 模拟对战沙盒 (Riichi Mahjong AI Sandbox)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)
![TailwindCSS](https://img.shields.io/badge/Frontend-TailwindCSS-06B6D4.svg)
![Deployment](https://img.shields.io/badge/Deployment-Render-46E3B7.svg)

这是一个基于 Python (Flask) 和纯原生前端技术构建的**日本麻将 (Riichi Mahjong) 模拟对战与牌理分析沙盒**。本项目不仅提供了一个高度仿真的沉浸式绿呢绒牌桌 UI，更核心的是在后端实现了一套基于**启发式搜索 (Heuristic Search)** 和 **打点期望 (EV) 评估** 的麻将 AI 决策引擎。

本项目最初为个人技术实践与算法验证而开发，目前可直接部署于云端，作为动态应用嵌入到个人博客中展示。

## ✨ 核心特性 (Features)

### 🧠 AI 决策与牌理引擎
* **多目标权重评估**：在纯牌效（进张数最大化）的基础上，引入了针对“宝牌 (Dora)”和“中张灵活性”的二阶评分函数，打破等效进张时的决策平局。
* **打点期望估算 (EV)**：基于向听数 (Shanten) 深度搜索，结合副露状态与役种潜力，实时计算出牌的 Expected Value。
* **实时战术面甲 (Tactical Visor)**：在人类玩家回合，侧边栏会实时输出多维度的出牌建议（包含进张数、危险预警、退向听警告及 EV 评分）。

### ⚔️ 高度仿真的对战沙盒
* **完整的回合状态机**：实现了标准的摸打循环，以及复杂的**异步中断/拦截逻辑**（如 AI/人类的碰、杠、荣和触发）。
* **自动 AI 对手**：内置 3 个根据当前牌面局势动态思考的 AI 对手，支持概率性自动鸣牌。
* **沉浸式桌面 UI**：使用 TailwindCSS 重构。支持真实物理间距映射、副露牌组的视觉解耦，以及纵向玩家手牌的 90° 旋转无缝堆叠。

## 🛠️ 技术栈 (Tech Stack)

* **后端 (Backend)**: Python, Flask, Gunicorn
* **前端 (Frontend)**: HTML5, JavaScript (ES6+), TailwindCSS
* **核心依赖**: `mahjong` (用于底层牌理计算与向听分析)

## 📐 算法原理亮点 (Algorithm Highlight)

本项目将麻将对战抽象为一个**带有中断优先级的多智能体状态机**。
在 AI 的出牌决策阶段，针对处于一向听及以内的手牌，系统会进行深度为 1-2 层的状态空间搜索，通过以下简化的价值模型进行多维排序：

$$Score = w_1 \cdot EV_{base} + w_2 \cdot Ukeire + w_3 \cdot Utility_{dora}$$

其中 $Utility_{dora}$ 确保了 AI 在面对平级决策时，具备保留高打点潜力的攻击性。

## 🚀 本地运行 (Local Setup)

1. **克隆仓库**:
   ```bash
   git clone [https://github.com/Allen-cubber/mahjong.git](https://github.com/Allen-cubber/mahjong.git)
   cd mahjong

   ```

2. **创建并激活虚拟环境**:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

```


3. **安装依赖**:
```bash
pip install -r requirements.txt

```


4. **启动服务**:
```bash
python app.py

```


随后在浏览器访问 `http://127.0.0.1:5000` 即可开始对战。

## ☁️ 云端部署 (Cloud Deployment via Render)

本项目已针对 PaaS 平台（如 Render）的自动化 CI/CD 进行了优化配置：

1. 在 Render 创建新的 Web Service，关联本 GitHub 仓库。
2. 配置项设置：
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`


3. （可选）在博客中通过 iframe 嵌入沙盒 URL 即可实现在线演示。

---

*Developed by z2x.*
