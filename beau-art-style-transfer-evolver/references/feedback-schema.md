# 反馈与规则提案最小格式

反馈先写事实，再写解释。事实来自用户原话、实际看到的图片或工具返回；推测必须标记低置信度。

## 反馈字段

- `source`: conversation / visual-review / tool-result / user-confirmed
- `area`: subject / composition / style / color / text-watermark / retry / tooling
- `observation`: 发生了什么
- `user_intent`: 用户要什么
- `evidence`: 原话、图像路径或工具字段
- `confidence`: high / medium / low
- `status`: new / clustered / proposed / accepted / rejected

## 提案原则

提案必须能回答：为什么当前规则不够、加入哪条最小规则、会影响什么、哪些内容保持不变。艺术质量提案必须保留人工复核，不得只用“生成成功”作为质量证明。
