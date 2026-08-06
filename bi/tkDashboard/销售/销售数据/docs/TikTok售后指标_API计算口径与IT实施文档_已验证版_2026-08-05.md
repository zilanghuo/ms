# TikTok 售后指标 API 计算口径与 IT 实施文档

**版本：** V2.0 已验证版  
**日期：** 2026-08-05  
**适用对象：** 数据开发、后端开发、BI 开发、TikTok 运营  
**接口版本：** TikTok Shop `202602`  
**接口：** `POST /return_refund/202602/returns/search`

## 1. 实施结论

售后指标应由两个数据源共同计算：

1. **订单明细 API：** 提供订单、订单行、SKU、购买数量和订单创建时间，作为指标分母。
2. **Search Returns API：** 提供售后单、售后类型、售后状态及对应商品行，作为指标分子。

不得再用普通订单状态或订单管理中的退货代理字段作为售后事实源。历史核对显示：

- 进行中的售后在订单管理中几乎不产生退货标记。
- 即使退款已经 Completed，订单 SKU 退货字段覆盖率也只有 `207 / 259 = 79.92%`。
- 因此，`Order Status`、`Cancelation/Return Type`、`Sku Quantity of return`、`Order Refund Amount` 只能用于交叉检查，不能作为售后分子的主判断依据。

## 2. 三个核心指标

三个指标必须使用同一订单组分母，只改变售后分子的状态范围。

| 指标 | 分子定义 | 订单维度公式 | SKU 维度公式 | 业务含义 |
|---|---|---|---|---|
| 售后发起率 | Search Returns 返回的全部售后记录，包括进行中、成功、拒绝和取消 | `发生过售后的去重订单数 / 非取消销售订单数` | `发生过售后的去重订单SKU数 / 非取消销售订单SKU数` | 买家产生过售后诉求的比例，反映产品、描述、物流和履约造成的全部售后压力 |
| 有效售后率 | 排除申请拒绝、买家/系统取消、退回包裹拒收；保留进行中、已通过、已完成退款和成功换补 | `有效售后的去重订单数 / 非取消销售订单数` | `有效售后的去重订单SKU数 / 非取消销售订单SKU数` | 真正进入处理流程且当前没有以拒绝/取消结束的售后比例；建议作为产品与运营绩效主指标 |
| 完成退款率 | 仅统计明确表示款项已经退款完成的终态 | `完成退款的去重订单数 / 非取消销售订单数` | `完成退款的去重订单SKU数 / 非取消销售订单SKU数` | 已经形成退款结果的订单/SKU比例，反映实际退款结果和收入损失 |

### 2.1 订单维度

```text
售后发起率_订单
= COUNT(DISTINCT is_aftersale_initiated = 1 的 order_id)
  / COUNT(DISTINCT 订单组内的 order_id)

有效售后率_订单
= COUNT(DISTINCT is_effective_aftersale = 1 的 order_id)
  / COUNT(DISTINCT 订单组内的 order_id)

完成退款率_订单
= COUNT(DISTINCT is_refund_completed = 1 的 order_id)
  / COUNT(DISTINCT 订单组内的 order_id)
```

### 2.2 SKU 维度

```text
售后发起率_SKU
= COUNT(DISTINCT is_aftersale_initiated = 1 的 order_id + sku_id)
  / COUNT(DISTINCT 订单组内的 order_id + sku_id)

有效售后率_SKU
= COUNT(DISTINCT is_effective_aftersale = 1 的 order_id + sku_id)
  / COUNT(DISTINCT 订单组内的 order_id + sku_id)

完成退款率_SKU
= COUNT(DISTINCT is_refund_completed = 1 的 order_id + sku_id)
  / COUNT(DISTINCT 订单组内的 order_id + sku_id)
```

同一订单或订单 SKU 发生多次售后时，上述“占比”指标只计一次。若以后需要衡量重复售后，应另建“售后申请次数”指标，不能混用。

## 3. 分母定义

### 3.1 订单归属期

订单按原订单创建时间归属统计周期：

```text
统计开始时间 <= order_created_at < 统计结束时间（次日零点）
```

例如历史验收周期：

```text
2026-07-01 00:00:00 <= order_created_at < 2026-07-29 00:00:00
```

售后申请可以发生在订单周期之后。7 月订单在 8 月产生售后，仍应计入这批 7 月订单的售后结果。

### 3.2 分母排除规则

分母至少排除：

- 已取消订单。
- 未支付订单（如果订单接口会返回）。
- 换货/补发生成的新履约订单，避免再次进入销售分母。

如果以后将订单归属口径从“创建时间”改成“支付时间”，所有历史和当期看板必须同时切换，不能混用。

## 4. v202602 官方状态映射

### 4.1 指标标记表

| `return_status` | 官方含义摘要 | 售后发起 | 有效售后 | 完成退款 |
|---|---|---:|---:|---:|
| `RETURN_OR_REFUND_REQUEST_PENDING` | 买家发起申请，等待商家或平台审核 | 1 | 1 | 0 |
| `AWAITING_BUYER_SHIP` | 退货已批准，等待买家寄回 | 1 | 1 | 0 |
| `BUYER_SHIPPED_ITEM` | 买家已经寄回商品 | 1 | 1 | 0 |
| `RETURN_OR_REFUND_REQUEST_SUCCESS` | 申请成功，买家将收到退款 | 1 | 1 | 0 |
| `RETURN_OR_REFUND_REQUEST_COMPLETE` | 处理完成，买家已经收到退款 | 1 | 1 | 1 |
| `REFUND_OR_RETURN_REQUEST_REJECT` | 退货/退款申请被拒绝 | 1 | 0 | 0 |
| `RETURN_OR_REFUND_REQUEST_CANCEL` | 买家或系统取消申请 | 1 | 0 | 0 |
| `REJECT_RECEIVE_PACKAGE` | 商家验货后拒绝退回包裹 | 1 | 0 | 0 |
| `AWAITING_BUYER_RESPONSE` | 商家提供其他处理方案，等待买家答复 | 1 | 1 | 0 |
| `REPLACEMENT_REQUEST_PENDING` | 换新申请等待审核 | 1 | 1 | 0 |
| `REPLACEMENT_REQUEST_REJECT` | 换新申请被拒绝 | 1 | 0 | 0 |
| `REPLACEMENT_REQUEST_CANCEL` | 买家取消换新申请 | 1 | 0 | 0 |
| `REPLACEMENT_REQUEST_COMPLETE` | 换新申请获批，平台生成新履约订单 | 1 | 1 | 0 |
| `REPLACEMENT_REQUEST_REFUND_SUCCESS` | 换新因缺货等原因最终通过退款解决 | 1 | 1 | 1 |

### 4.2 重要边界

- `RETURN_OR_REFUND_REQUEST_SUCCESS` 只表示退款已经获批、买家将收到退款，**不能计入完成退款率**。
- 只有 `RETURN_OR_REFUND_REQUEST_COMPLETE` 表示普通退货/退款已经实际完成。
- `REPLACEMENT_REQUEST_COMPLETE` 是成功换新，不是退款。
- `REPLACEMENT_REQUEST_REFUND_SUCCESS` 的最终结果是退款，应计入完成退款率。
- `REJECT_RECEIVE_PACKAGE` 会产生售后处理工作量，但最后是拒收/拒绝退款，因此不进入有效售后率；可另建“退回包裹拒收率”。

### 4.3 未知状态处理

```text
is_aftersale_initiated = 1
is_effective_aftersale = NULL
is_refund_completed = NULL
status_mapping_result = 'UNKNOWN'
```

未知状态必须报警并进入待配置表。在业务确认前，不允许自动猜测其有效/完成属性。

## 5. 售后类型映射

v202602 官方当前明确列出的类型：

| `return_type` | 含义 | 是否进入三个广义指标 |
|---|---|---:|
| `REFUND` | 仅退款，无需买家寄回 | 是 |
| `RETURN_AND_REFUND` | 退货退款 | 是 |
| `REPLACEMENT` | 换新/补发 | 是；但只有 `REPLACEMENT_REQUEST_REFUND_SUCCESS` 进入完成退款率 |

### EXCHANGE 处理要求

用户提供的截图包含 `EXCHANGE`，但 v202602 官方 Search Returns 文档当前没有把它列为可用 `return_type`，因此本版本**不得硬编码**以下状态：

```text
EXCHANGE_REQUEST_PENDING
EXCHANGE_REQUEST_REFUND_SUCCESS
EXCHANGE_REQUEST_CANCEL
EXCHANGE_REQUEST_COMPLETE
```

如果真实 API 响应出现 `EXCHANGE`：

1. 保存原始响应。
2. 进入 `UNKNOWN` 报警。
3. 业务确认后再补充映射。
4. 若 `EXCHANGE_REQUEST_REFUND_SUCCESS` 的官方含义确认是完成退款，届时再计入完成退款率。

## 6. API 取数方式

### 6.1 请求基础信息

```text
POST /return_refund/202602/returns/search
Required scope: seller.return_refund.basic
```

关键请求参数：

- Header：`x-tts-access-token`、`content-type: application/json`
- Query：`app_key`、`sign`、`timestamp`、`shop_cipher`
- 排序：`sort_field=create_time|update_time`
- 排序方向：`sort_order=ASC|DESC`
- 分页：`page_size` 范围 10～50
- 分页令牌：`page_token`
- 时间过滤：`create_time_ge/create_time_lt`、`update_time_ge/update_time_lt`

分页规则：收到 `next_page_token` 后，把它作为下一页的 `page_token`，其他筛选条件和排序条件保持不变，直到 `next_page_token` 为空。

### 6.2 首次回溯

1. 从订单 API 拉取目标订单周期的订单及订单行。
2. 从最早订单日期开始至当前时间，按售后 `create_time` 回溯 Search Returns。
3. 保存售后主表和售后商品行。
4. 通过 `order_id` 连接订单维度，通过 `order_line_item_id` 或 `order_id + sku_id` 连接 SKU 维度。

### 6.3 日常增量

必须按 `update_time` 拉取，因为同一售后单会从申请中推进到批准、寄回、成功、完成、拒绝或取消。

推荐：

```text
sort_field = update_time
sort_order = ASC
page_size = 50
update_time_ge = 上次成功水位 - 7天
update_time_lt = 本次任务启动时间
```

“减 7 天”是项目容错窗口，不是 TikTok 强制参数。重复数据通过主键更新，不会重复计入指标。

只有在本轮所有分页成功落库后才能推进水位；任何一页失败，都不能推进水位。

## 7. 数据模型与去重

### 7.1 订单行表

```text
fact_order_line
- shop_id
- order_id
- order_line_item_id
- sku_id
- seller_sku
- order_created_at
- paid_at
- order_status
- purchased_quantity
- is_cancelled
- is_replacement_child
```

### 7.2 售后主表

```text
fact_return
- shop_id
- return_id
- order_id
- return_type
- return_status
- arbitration_status
- create_time
- update_time
- pre_return_id
- next_return_id
- refund_total
- currency
- raw_json
```

主键：

```text
shop_id + return_id
```

同一 `return_id` 再次拉取时更新当前状态，不新增一笔事实。

### 7.3 售后商品行表

```text
fact_return_line
- shop_id
- return_id
- return_line_item_id
- order_id
- order_line_item_id
- sku_id
- seller_sku
- line_refund_total
```

优先连接键：

```text
shop_id + order_id + order_line_item_id
```

备用连接键：

```text
shop_id + order_id + sku_id
```

不能只用 `sku_id` 连接，因为同一 SKU 会出现在多张订单中。

### 7.4 售后链路

如果响应包含 `pre_return_id` / `next_return_id`，必须保留。它们表示售后申请被修改后的前后链路。

三个“占比”指标最终按订单或订单 SKU 去重，因此一条链路不会重复抬高占比；如果以后统计售后申请次数，再单独处理链路合并规则。

## 8. 指标生成逻辑

```sql
CASE
  WHEN return_id IS NOT NULL THEN 1
  ELSE 0
END AS is_aftersale_initiated,

CASE
  WHEN return_status IN (
    'RETURN_OR_REFUND_REQUEST_PENDING',
    'AWAITING_BUYER_SHIP',
    'BUYER_SHIPPED_ITEM',
    'RETURN_OR_REFUND_REQUEST_SUCCESS',
    'RETURN_OR_REFUND_REQUEST_COMPLETE',
    'AWAITING_BUYER_RESPONSE',
    'REPLACEMENT_REQUEST_PENDING',
    'REPLACEMENT_REQUEST_COMPLETE',
    'REPLACEMENT_REQUEST_REFUND_SUCCESS'
  ) THEN 1
  WHEN return_status IN (
    'REFUND_OR_RETURN_REQUEST_REJECT',
    'RETURN_OR_REFUND_REQUEST_CANCEL',
    'REJECT_RECEIVE_PACKAGE',
    'REPLACEMENT_REQUEST_REJECT',
    'REPLACEMENT_REQUEST_CANCEL'
  ) THEN 0
  ELSE NULL
END AS is_effective_aftersale,

CASE
  WHEN return_status IN (
    'RETURN_OR_REFUND_REQUEST_COMPLETE',
    'REPLACEMENT_REQUEST_REFUND_SUCCESS'
  ) THEN 1
  WHEN return_status IN (已配置的其他状态) THEN 0
  ELSE NULL
END AS is_refund_completed
```

## 9. 历史独立重算基准

### 9.1 数据范围

- 订单创建时间：2026-07-01 至 2026-07-28。
- 售后导出时间：2026-08-05。
- 原订单：10,535 个订单 SKU 行、9,901 个订单。
- 排除取消订单后：9,595 个订单、10,209 个订单 SKU。
- 与订单周期匹配的售后：714 行、619 个订单、672 个订单 SKU。

### 9.2 验算结果

| 指标 | 订单维度 | SKU 维度 |
|---|---:|---:|
| 售后发起率 | `619 / 9,595 = 6.45%` | `672 / 10,209 = 6.58%` |
| 有效售后率（旧导出严格排除全部拒绝/取消） | `575 / 9,595 = 5.99%` | `624 / 10,209 = 6.11%` |
| 完成退款率（旧导出 Completed） | `264 / 9,595 = 2.75%` | `289 / 10,209 = 2.83%` |

### 9.3 历史状态验证

匹配订单周期的 714 行售后中：

| 旧导出状态组 | 行数 |
|---|---:|
| Completed | 289 |
| 进行中 | 335 |
| 拒绝但无法区分申请拒绝或包裹拒收 | 39 |
| 取消 | 51 |

验证发现：

- 289 条 Completed 全部有退款时间，支持把旧导出 Completed 作为完成退款结果。
- 160 条非 Completed 记录也存在退款时间，因此不能用“退款时间非空”代替完成状态。
- 714 行售后去重后只有 672 个订单 SKU，说明不能直接用售后导出行数作为 SKU 分子。

历史有效售后率 `5.99% / 6.11%` 是旧导出严格排除所有拒绝和取消后的基准。旧导出无法区分 API 的 `REFUND_OR_RETURN_REQUEST_REJECT` 与 `REJECT_RECEIVE_PACKAGE`，因此 IT 接入 API 后应按新状态重新计算，并输出差异明细，而不是强制要求数值完全相等。

## 10. API 接入验收标准

### 10.1 基础完整性

- API `code=0`。
- 所有分页拉取完成。
- `return_id` 不为空且在店铺内唯一。
- `order_id` 能连接订单表；不能连接的进入异常明细。
- 未识别状态数量必须为 0；如不为 0，必须报警并暂停发布有效/完成指标。

### 10.2 SKU 能力确认

IT 必须提供至少一份真实 v202602 API 响应，确认是否返回：

```text
return_line_items[].return_line_item_id
return_line_items[].order_line_item_id
return_line_items[].sku_id
```

在这些字段确认之前：

- 订单维度可以上线验证。
- SKU 维度只能算“待验证”，不能声明正式可用。

如果 v202602 实际响应无法提供行项目，应评估 `POST /return_refund/202603/aftersales/search`，新版接口明确提供 `LINE_ITEMS` 和 `SKU_RETURN_REQUESTS` 白名单字段。

### 10.3 历史回放

以 2026-08-05 为观察截点回放 7 月 1 日至 7 月 28 日订单组：

- 订单分母应为 9,595。
- SKU 分母应为 10,209。
- 售后发起结果应接近订单 619、SKU 672。
- 完成退款结果应接近订单 264、SKU 289。
- 有效售后必须按 API 新状态重新计算，不要求机械等于旧导出的 575/624。

所有差异输出以下字段：

```text
shop_id
order_id
order_line_item_id
sku_id
return_id
return_type
API return_status
旧导出 Return Status
旧导出 Return Sub Status
create_time
update_time
差异分类
```

### 10.4 增量稳定性

- 同一 `return_id` 重拉不会增加售后数量。
- 状态从 Pending 更新到 Complete 后，售后发起率不变，有效售后率不变，完成退款率增加。
- 状态从 Pending 更新到 Reject/Cancel 后，售后发起率不变，有效售后率下降，完成退款率不变。
- 水位任务失败后重跑不会漏数或重复计数。

## 11. 看板展示要求

每个指标必须同时显示：

- 指标维度：订单 / SKU。
- 订单归属期。
- 售后观察截止时间。
- 成熟天数，例如 `D+8`。
- 指标口径说明。

跨周期比较时应使用相同成熟度，例如统一比较 D+7、D+14、D+30。否则最近周期的售后尚未发生或尚未完成，会天然偏低。

## 12. 待 IT 返回的验证材料

为了完成最后上线确认，请 IT 提供：

1. 一份真实 v202602 Search Returns 成功响应，敏感 token、签名可打码。
2. 响应中至少包含：仅退款、退货退款、进行中、Completed、Replacement 各一条；没有某类样本可注明。
3. 一次包含多个 SKU 的售后响应。
4. 一次分页响应及对应下一页响应。
5. 是否实际出现 `EXCHANGE` 类型或状态。
6. 接口时区与数据库落库时区。

## 13. 官方资料

- Search Returns v202602：<https://partner.tiktokshop.com/docv2/page/search-returns-202602>
- Return, refund, and cancel API overview：<https://partner.tiktokshop.com/docv2/page/return-refund-and-cancel-api-overview>
- Return status change webhook：<https://partner.tiktokshop.com/docv2/page/12-return-status-change>
- Search Aftersales Request v202603：<https://partner.tiktokshop.com/docv2/page/search-aftersales-request-202603>

