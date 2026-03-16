# bi 目录文档结构速查

本 skill 适用于 **bi** 目录下所有子项目；以下以 `bi/tkDashboard` 为参考实现。

## 目录树（bi/tkDashboard，可类推到 bi 下其他子项目）

```
bi/tkDashboard/
├── index.html                    # 入口：侧栏导航 + iframe 内容区
├── 销售数据映射/
│   ├── 需求文档.html             # 需求一、需求二 等
│   └── htmls/
│       ├── 店铺统计.html
│       ├── 商品统计.html
│       └── 需求二-销量趋势数据表.html
├── PID/
│   ├── 需求文档.html
│   └── htmls/
│       ├── 需求一-GMV计算表.html
│       └── 需求二-数据看板.html
├── 接口设计文档/
│   └── 接口文档.html            # 通用约定 + 各模块接口 + 积加对接 + 接口总览
└── 技术方案/
    ├── 技术方案.html
    └── 表结构设计-Doris.html
```

## 接口文档章节顺序（接口文档.html）

1. 标题 + 对应页面说明  
2. 通用约定（表格 + 统一响应结构）  
3. 零、下拉选项（0.1 站点 0.2 店铺 0.3 货币）  
4. 一、需求一：店铺统计（主表、导出、链比等）  
5. 二、需求二：商品统计（主表、弹框、导出）  
6. 三、需求二：PID 数据看板（查询条件、3.2 主表、参与对比字段、响应示例、51 列表、每日明细、弹框、导出）  
7. 五、积加对接：全渠道商品（URL、请求、响应、childList 字段表、示例、导出/落库字段）  
8. 六、积加对接：全渠道订单（URL、请求、响应、rows/itemVoList 字段表、示例、落库两份数据及字段）  
9. 四、接口总览（序号 1 起连续）  
10. 文档版本说明 + 返回首页链接  

## 落库/导出备注写法

- **全渠道商品**：从 `childList` 单条取字段：groupItemId、itemId、marketId、marketName、sku、msku、skuName、spu、spuName、salePrice、adjustStandardPrice、currency、categoryTree、salesState、salesStateDesc、single、mainImageUrl。  
- **全渠道订单**：  
  - 1. 订单数据（`data.rows[]`）：orderId、platformId、platformMarketId、platformOrderStatus、marketId、marketName、orderStatusName、orderTotal、currencyCode、purchaseDate、paymentMarketTime、buyerPayAmount、refundTotalAmount、timeZone。  
  - 2. 订单商品明细（`data.rows[].itemVoList[]`）：itemId、asin、platformId、platformFid、marketId、sku、msku、productName、orderTitle、categoryName、sellingPrice、itemPrice、orderStatusName、promotionDiscount。

## 术语统一

- **接口**：接口文档中称「接口」或「接口地址」，不混用 URL/路由/路径。  
- **字段**：表头/JSON 用「字段」，不混用「列」「属性」「box」。  
- **请求体/响应 data**：POST 用「请求体」；响应根级为 code/message/data，业务内容在 `data` 下。
